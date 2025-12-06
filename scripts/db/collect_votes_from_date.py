#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
특정 날짜부터 표결 정보 수집 스크립트
2025-10-15부터 현재까지
"""

import os
import sys
import psycopg2
from xml.etree import ElementTree as ET
import requests
from datetime import datetime
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# .env 파일 로드
try:
    from dotenv import load_dotenv
    # 프로젝트 루트 디렉토리로 이동
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()  # 현재 디렉토리에서 찾기
except ImportError:
    # dotenv가 없으면 수동 로드
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_file):
        encodings = ['utf-8', 'utf-8-sig', 'cp949', 'latin-1']
        for encoding in encodings:
            try:
                with open(env_file, 'r', encoding=encoding) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key and value:
                                os.environ[key] = value
                break
            except:
                continue

ASSEMBLY_KEY = os.environ.get("ASSEMBLY_SERVICE_KEY")
if not ASSEMBLY_KEY:
    raise ValueError("ASSEMBLY_SERVICE_KEY environment variable is required")

VOTE_INFO_API = "https://open.assembly.go.kr/portal/openapi/nojepdqqaweusdfbi"

def get_db_config():
    """환경 변수에서 데이터베이스 설정 가져오기"""
    # Railway는 DATABASE_URL 제공
    if 'DATABASE_URL' in os.environ:
        from urllib.parse import urlparse
        db_url = urlparse(os.environ['DATABASE_URL'])
        return {
            'host': db_url.hostname,
            'database': db_url.path[1:],  # / 제거
            'user': db_url.username,
            'password': db_url.password,
            'port': db_url.port or 5432
        }
    # Render는 개별 환경 변수 제공
    elif 'DB_HOST' in os.environ:
        return {
            'host': os.environ.get('DB_HOST'),
            'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': os.environ.get('DB_PASSWORD'),
            'port': int(os.environ.get('DB_PORT', 5432))
        }
    # 로컬 개발용 (LOCAL_DB_* 환경 변수 우선)
    else:
        return {
            'host': os.environ.get('LOCAL_DB_HOST', 'localhost'),
            'database': os.environ.get('LOCAL_DB_NAME', 'mypoly_lawdata'),
            'user': os.environ.get('LOCAL_DB_USER', 'postgres'),
            'password': os.environ.get('LOCAL_DB_PASSWORD') or os.environ.get('DB_PASSWORD'),
            'port': int(os.environ.get('LOCAL_DB_PORT', '5432'))
        }

def get_db_connection():
    config = get_db_config()
    return psycopg2.connect(**config)

def parse_datetime(datetime_str):
    """날짜 문자열을 datetime 객체로 변환 (다양한 형식 지원)"""
    if not datetime_str:
        return None
    try:
        datetime_str = datetime_str.strip()
        if len(datetime_str) == 14:
            return datetime.strptime(datetime_str, '%Y%m%d%H%M%S')
        elif len(datetime_str) == 19:
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        elif len(datetime_str) == 10:
            # YYYY-MM-DD 형식
            return datetime.strptime(datetime_str, '%Y-%m-%d')
        elif len(datetime_str) == 8:
            # YYYYMMDD 형식
            return datetime.strptime(datetime_str, '%Y%m%d')
    except Exception as e:
        # 파싱 실패 시 로그 출력 (디버깅용)
        # print(f"날짜 파싱 실패: {datetime_str}, 오류: {e}")
        pass
    return None

def collect_votes_from_date(start_date_str=None, end_date_str=None):
    """표결 정보 수집 (최신 데이터만 빠르게 수집)
    
    - start_date_str가 없으면: DB의 최신 표결일 이후만 수집 (추천)
    - start_date_str가 있으면: 해당 날짜 이후 수집
    - 2025년 의안의 표결만 수집합니다 (2025-01-01 이후)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 2025-01-01 이전 데이터는 수집하지 않음 (강제 필터)
    MIN_DATE = parse_datetime("20250101000000")
    
    # DB의 최신 표결일 확인
    cur.execute("""
        SELECT MAX(vote_date) 
        FROM votes 
        WHERE vote_date IS NOT NULL
    """)
    latest_vote_date = cur.fetchone()[0]
    
    # 시작일 결정: 사용자 지정 또는 DB 최신일
    if start_date_str:
        start_date = parse_datetime(start_date_str + "000000")
        if not start_date:
            print(f"  ❌ 잘못된 날짜 형식: {start_date_str}")
            return
        if start_date < MIN_DATE:
            print(f"  ⚠️ 시작일이 2025-01-01 이전입니다. 2025-01-01로 조정합니다.")
            start_date = MIN_DATE
    else:
        # DB의 최신 표결일 이후만 수집 (빠른 수집)
        if latest_vote_date:
            from datetime import timedelta
            start_date = latest_vote_date + timedelta(seconds=1)
            print(f"현재 DB의 최신 표결일: {latest_vote_date}")
            print(f"→ {start_date.strftime('%Y-%m-%d %H:%M:%S')} 이후의 신규 표결만 수집합니다")
        else:
            # DB에 데이터가 없으면 2025-01-01부터
            start_date = MIN_DATE
            print("DB에 표결 데이터가 없습니다. 2025-01-01부터 수집합니다.")
    
    end_date = None
    if end_date_str:
        end_date = parse_datetime(end_date_str + "235959")
    
    print("=" * 60)
    if end_date:
        print(f"표결 정보 수집 시작 (표결일: {start_date.strftime('%Y%m%d')} ~ {end_date_str})")
    else:
        print(f"표결 정보 수집 시작 (표결일: {start_date.strftime('%Y%m%d')} 이후)")
    print("=" * 60)
    
    # bills 테이블에서 2025년 의안만 가져오기 (2024년 의안 제외)
    # 최신 의안부터 확인 (최근에 추가된 의안의 표결이 있을 가능성이 높음)
    cur.execute("""
        SELECT bill_id 
        FROM bills 
        WHERE proposal_date >= '2025-01-01'
        GROUP BY bill_id
        ORDER BY MAX(proposal_date) DESC, bill_id
    """)
    bill_ids = [row[0] for row in cur.fetchall()]
    
    print(f"\n{len(bill_ids)}개의 2025년 의안에 대한 표결 정보를 확인합니다...")
    
    total_inserted = 0
    total_skipped = 0
    
    for i, bill_id in enumerate(bill_ids, 1):
        if i % 50 == 0:
            print(f"\n진행 상황: {i}/{len(bill_ids)}")
        
        params = {
            "KEY": ASSEMBLY_KEY,
            "Type": "xml",
            "pIndex": 1,
            "pSize": 300,
            "BILL_ID": bill_id,
            "AGE": "22"
        }
        
        try:
            response = requests.get(VOTE_INFO_API, params=params, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            items = root.findall(".//row")
            
            if not items:
                total_skipped += 1
                continue
            
            page_inserted = 0
            
            for item in items:
                member_no = item.findtext("MEMBER_NO", "").strip()
                if not member_no:
                    continue
                
                vote_date = parse_datetime(item.findtext("VOTE_DATE", ""))
                
                # vote_date가 NULL이면 bills 테이블의 날짜 사용
                if not vote_date:
                    cur.execute("SELECT proposal_date FROM bills WHERE bill_id = %s", (bill_id,))
                    bill_row = cur.fetchone()
                    if bill_row and bill_row[0]:
                        # proposal_date는 date 타입이므로 datetime으로 변환
                        from datetime import datetime
                        proposal_date = bill_row[0]
                        if isinstance(proposal_date, datetime):
                            vote_date = proposal_date
                        else:
                            # date 타입을 datetime으로 변환
                            vote_date = datetime.combine(proposal_date, datetime.min.time())
                
                # 2025-01-01 이전 표결일은 무조건 건너뛰기 (2024년 데이터 방지)
                if vote_date and vote_date < MIN_DATE:
                    continue
                
                # 표결일이 시작일 이후인 것만 저장
                if vote_date and vote_date < start_date:
                    continue
                
                # 표결일이 종료일 이후인 것은 건너뛰기
                if end_date and vote_date and vote_date > end_date:
                    continue
                
                # vote_date가 여전히 NULL이면 건너뛰기
                if not vote_date:
                    continue
                
                vote_result = item.findtext("RESULT_VOTE_MOD", "").strip()
                member_name = item.findtext("HG_NM", "") or item.findtext("NAAS_NM", "")
                member_name = member_name.strip() if member_name else ""
                party_name = item.findtext("POLY_NM", "").strip()
                district_name = item.findtext("ORIG_NM", "").strip()
                mona_cd = item.findtext("MONA_CD", "").strip()
                bill_no = item.findtext("BILL_NO", "").strip()
                bill_name = item.findtext("BILL_NAME", "").strip()
                
                try:
                    # 중복 체크: 현재 UNIQUE 제약조건 (bill_id, member_no, vote_date)에 맞춰서 확인
                    # 하지만 vote_result도 함께 확인하여 완전한 중복 방지
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM votes 
                        WHERE bill_id = %s 
                          AND member_no = %s 
                          AND vote_date = %s
                          AND vote_result = %s
                    """, (bill_id, member_no, vote_date, vote_result))
                    
                    if cur.fetchone()[0] > 0:
                        total_already_exists += 1
                        continue  # 이미 존재하면 건너뛰기
                    
                    # INSERT with ON CONFLICT DO NOTHING (중복 방지)
                    # 현재 UNIQUE 제약조건: (bill_id, member_no, vote_date)
                    # vote_result가 다른 경우도 있을 수 있으므로 사전 체크로 완전히 방지
                    cur.execute("""
                        INSERT INTO votes (
                            bill_id, bill_no, bill_name, member_no, mona_cd, 
                            vote_result, vote_date, member_name, party_name, district_name, created_at
                        ) VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                        )
                        ON CONFLICT (bill_id, member_no, vote_date) 
                        DO NOTHING
                    """, (
                        bill_id, bill_no, bill_name, member_no, mona_cd,
                        vote_result, vote_date, member_name, party_name, district_name
                    ))
                    
                    if cur.rowcount > 0:
                        page_inserted += 1
                        total_inserted += 1
                except Exception as e:
                    print(f"    ⚠️ 표결 저장 오류: {e}")
                    continue
            
            if page_inserted > 0:
                conn.commit()
            
            time.sleep(0.5)  # API 호출 제한
        
        except Exception as e:
            print(f"  ⚠️ 오류 (BILL_ID: {bill_id[:20]}...): {e}")
            conn.rollback()
            continue
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"수집 완료!")
    print(f"  - 신규 삽입: {total_inserted}건")
    print(f"  - 표결 데이터 없음: {total_skipped}건")
    print(f"  - 이미 존재하는 표결: {total_already_exists}건")
    print("=" * 60)

if __name__ == '__main__':
    import sys
    # 인자가 없으면 자동으로 최신 데이터만 수집 (빠름)
    # 인자가 있으면 해당 날짜부터 수집
    start_date = sys.argv[1] if len(sys.argv) > 1 else None
    end_date = sys.argv[2] if len(sys.argv) > 2 else None
    collect_votes_from_date(start_date, end_date)

