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
    # 로컬 개발용 (기본값)
    else:
        return {
            'host': 'localhost',
            'database': 'mypoly_lawdata',
            'user': 'postgres',
            'password': os.environ.get('DB_PASSWORD'),
            'port': 5432
        }

def get_db_connection():
    config = get_db_config()
    return psycopg2.connect(**config)

def parse_datetime(datetime_str):
    if not datetime_str:
        return None
    try:
        if len(datetime_str) == 14:
            return datetime.strptime(datetime_str, '%Y%m%d%H%M%S')
        elif len(datetime_str) == 19:
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    except:
        pass
    return None

def collect_votes_from_date(start_date_str="20251015", end_date_str=None):
    """특정 날짜부터 표결 정보 수집"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    start_date = parse_datetime(start_date_str + "000000")
    if not start_date:
        print(f"  ❌ 잘못된 날짜 형식: {start_date_str}")
        return
    
    end_date = None
    if end_date_str:
        end_date = parse_datetime(end_date_str + "235959")
    
    print("=" * 60)
    if end_date:
        print(f"표결 정보 수집 시작 (표결일: {start_date_str} ~ {end_date_str})")
    else:
        print(f"표결 정보 수집 시작 (표결일: {start_date_str} 이후)")
    print("=" * 60)
    
    # bills 테이블에서 모든 bill_id 가져오기
    cur.execute("SELECT DISTINCT bill_id FROM bills")
    bill_ids = [row[0] for row in cur.fetchall()]
    
    print(f"\n{len(bill_ids)}개의 의안에 대한 표결 정보를 수집합니다...")
    
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
                
                # 표결일이 시작일 이후인 것만 저장
                if vote_date and vote_date < start_date:
                    continue
                
                # 표결일이 종료일 이후인 것은 건너뛰기
                if end_date and vote_date and vote_date > end_date:
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
                    cur.execute("""
                        INSERT INTO votes (
                            bill_id, bill_no, bill_name, member_no, mona_cd, 
                            vote_result, vote_date, member_name, party_name, district_name, created_at
                        ) VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                        )
                        ON CONFLICT (bill_id, member_no, vote_date) 
                        DO UPDATE SET
                            vote_result = EXCLUDED.vote_result,
                            member_name = EXCLUDED.member_name,
                            party_name = EXCLUDED.party_name,
                            district_name = EXCLUDED.district_name
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
    print("=" * 60)

if __name__ == '__main__':
    import sys
    start_date = sys.argv[1] if len(sys.argv) > 1 else "20250101"
    end_date = sys.argv[2] if len(sys.argv) > 2 else None
    collect_votes_from_date(start_date, end_date)

