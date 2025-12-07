#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
특정 날짜부터 의안 정보 수집 스크립트
2025-08-01부터 최근까지
"""

import os
import sys
import psycopg2
from urllib.parse import unquote
from xml.etree import ElementTree as ET
import requests
from datetime import datetime
import time
import re

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# .env 파일 로드
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
env_path = os.path.join(project_root, '.env')

# 수동 로드 (dotenv가 실패할 수 있으므로)
if os.path.exists(env_path):
    encodings = ['utf-8', 'utf-8-sig', 'cp949', 'latin-1']
    for encoding in encodings:
        try:
            with open(env_path, 'r', encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and value:
                            os.environ[key] = value
            break
        except Exception as e:
            continue

# dotenv도 시도 (이미 로드된 경우 override)
try:
    from dotenv import load_dotenv
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
    load_dotenv(override=True)
except ImportError:
    pass

ENCODED_SERVICE_KEY = os.environ.get("BILL_SERVICE_KEY")
if not ENCODED_SERVICE_KEY:
    print(f"❌ BILL_SERVICE_KEY를 찾을 수 없습니다.")
    print(f"   스크립트 경로: {os.path.abspath(__file__)}")
    print(f"   프로젝트 루트: {project_root if 'project_root' in locals() else 'N/A'}")
    print(f"   .env 경로: {env_path if 'env_path' in locals() else 'N/A'}")
    print(f"   .env 파일 존재: {os.path.exists(env_path) if 'env_path' in locals() else 'N/A'}")
    raise ValueError("BILL_SERVICE_KEY environment variable is required")
SERVICE_KEY = unquote(ENCODED_SERVICE_KEY)

BILL_INFO_API = "https://apis.data.go.kr/9710000/BillInfoService2/getBillInfoList"

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

def parse_date(date_str):
    if not date_str:
        return None
    try:
        if len(date_str) == 8:
            return datetime.strptime(date_str, '%Y%m%d').date()
        elif len(date_str) == 10:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        pass
    return None

def extract_proposer_name_from_title(title):
    """
    의안 제목에서 제안자 이름 추출
    형식: "의안명(제안자명의원 등 N인)" 또는 "의안명(제안자명의원)"
    예: "재난 및 안전관리 기본법 일부개정법률안(임종득의원 등 10인)"
    """
    if not title:
        return ""
    
    # 괄호 안의 내용 추출
    match = re.search(r'\(([^)]+)\)', title)
    if not match:
        return ""
    
    proposer_text = match.group(1)
    
    # "의원" 키워드가 있으면 그 앞의 이름 추출
    # 예: "임종득의원 등 10인" -> "임종득"
    # 예: "정태호의원 등 10인" -> "정태호"
    # 예: "임미애의원 등 21인" -> "임미애"
    proposer_match = re.search(r'([가-힣]+)의원', proposer_text)
    if proposer_match:
        return proposer_match.group(1)
    
    # "의원" 키워드가 없으면 전체를 반환 (예: "의장", "정부" 등)
    return proposer_text.strip()

def calculate_proc_stage_order(proc_stage_cd):
    """
    proc_stage_cd를 기반으로 proc_stage_order 계산
    1=접수, 2=심사, 3=본회의, 4=처리완료
    """
    if not proc_stage_cd:
        return None
    
    proc_stage_cd = proc_stage_cd.strip()
    
    # 접수 관련
    if '접수' in proc_stage_cd:
        return 1
    
    # 심사 관련
    if '심사' in proc_stage_cd:
        return 2
    
    # 본회의 관련
    if '본회의' in proc_stage_cd:
        return 3
    
    # 처리완료 관련 (공포, 정부이송 등)
    if any(keyword in proc_stage_cd for keyword in ['공포', '정부이송', '처리완료']):
        return 4
    
    # 기타 (철회, 폐기 등)
    if any(keyword in proc_stage_cd for keyword in ['철회', '폐기', '재의']):
        return None  # 처리되지 않은 것으로 간주
    
    # 기본값: None
    return None

def get_latest_proposal_date():
    """DB에서 가장 최근 제안일 가져오기"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT MAX(proposal_date) FROM bills WHERE proposal_date IS NOT NULL")
        result = cur.fetchone()
        return result[0] if result and result[0] else None
    finally:
        cur.close()
        conn.close()

def collect_bills_from_date(start_date_str=None, end_date_str=None):
    """의안 정보 수집 (최신 데이터만 빠르게 수집)
    
    - start_date_str가 없으면: DB의 최신 제안일 이후만 수집 (추천)
    - start_date_str가 있으면: 해당 날짜 이후 수집
    - 2025년 의안만 수집합니다 (2025-01-01 이후)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    total_inserted = 0
    total_updated = 0
    total_skipped_2024 = 0
    total_skipped_old = 0
    
    # 2025-01-01 이전 데이터는 수집하지 않음 (강제 필터)
    MIN_DATE = parse_date("20250101")
    
    # 최신 제안일 확인
    latest_date = get_latest_proposal_date()
    
    # 시작일 결정: 사용자 지정 또는 DB 최신일
    if start_date_str:
        start_date = parse_date(start_date_str)
        if not start_date:
            print(f"  ❌ 잘못된 날짜 형식: {start_date_str}")
            return
        if start_date < MIN_DATE:
            print(f"  ⚠️ 시작일이 2025-01-01 이전입니다. 2025-01-01로 조정합니다.")
            start_date = MIN_DATE
    else:
        # DB의 최신 제안일 이후만 수집 (빠른 수집)
        if latest_date:
            # 최신일의 다음 날부터 수집 (중복 방지)
            from datetime import timedelta
            start_date = latest_date + timedelta(days=1)
            print(f"현재 DB의 최신 제안일: {latest_date}")
            print(f"→ {start_date} 이후의 신규 의안만 수집합니다")
        else:
            # DB에 데이터가 없으면 2025-01-01부터
            start_date = MIN_DATE
            print("DB에 데이터가 없습니다. 2025-01-01부터 수집합니다.")
    
    print("=" * 60)
    if end_date_str:
        print(f"의안 정보 수집 시작 (제안일: {start_date.strftime('%Y%m%d')} ~ {end_date_str})")
    else:
        print(f"의안 정보 수집 시작 (제안일: {start_date.strftime('%Y%m%d')} 이후)")
    print("=" * 60)
    
    end_date = None
    if end_date_str:
        end_date = parse_date(end_date_str)
        if not end_date:
            print(f"  ❌ 잘못된 종료일 형식: {end_date_str}")
            return
    
    page = 1
    page_size = 100
    max_pages = 1000  # 최대 페이지 수 제한
    
    while page <= max_pages:
        print(f"\n페이지 {page} 처리 중...")
        
        params = {
            "serviceKey": SERVICE_KEY,
            "pageNo": page,
            "numOfRows": page_size,
            "start_ord": 22,
            "end_ord": 22,
        }
        
        try:
            response = requests.get(BILL_INFO_API, params=params, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            items = root.findall(".//items/item")
            
            if not items:
                print(f"  페이지 {page}: 데이터 없음, 수집 종료")
                break
            
            print(f"  페이지 {page}: {len(items)}건 조회")
            
            page_inserted = 0
            page_updated = 0
            page_skipped_old = 0
            early_exit = False
            
            for item in items:
                bill_id = item.findtext("billId", "").strip()
                if not bill_id:
                    continue
                
                proposal_date = parse_date(item.findtext("proposeDt", ""))
                
                # proposal_date가 NULL이면 건너뛰기 (날짜 없는 의안은 수집하지 않음)
                if not proposal_date:
                    continue
                
                # 2025-01-01 이전 데이터는 무조건 건너뛰기 (2024년 데이터 방지)
                if proposal_date < MIN_DATE:
                    total_skipped_2024 += 1
                    continue
                
                # 제안일이 시작일 이전이면 건너뛰기 (이미 수집한 데이터)
                if proposal_date < start_date:
                    total_skipped_old += 1
                    page_skipped_old += 1
                    continue
                
                # 제안일이 종료일 이후인 것은 건너뛰기
                if end_date and proposal_date > end_date:
                    continue
                
                bill_no = item.findtext("billNo", "").strip()
                title = item.findtext("billName", "").strip()
                proposer_kind = item.findtext("proposerKind", "").strip()
                # 제안자 이름: API 필드 먼저 확인, 없으면 의안 제목에서 추출
                proposer_name = item.findtext("proposerNm", "") or item.findtext("proposerName", "")
                proposer_name = proposer_name.strip() if proposer_name else ""
                # API 필드에 없으면 의안 제목에서 추출
                if not proposer_name:
                    proposer_name = extract_proposer_name_from_title(title)
                proc_stage_cd = item.findtext("procStageCd", "").strip()
                pass_gubn = item.findtext("passGubn", "").strip()
                proc_date = parse_date(item.findtext("procDt", ""))
                general_result = item.findtext("generalResult", "").strip()
                summary_raw = item.findtext("summary", "").strip()
                # linkUrl 필드는 API에 없으므로 billId로 생성
                # 국회 의안 상세 페이지: https://likms.assembly.go.kr/bill/billDetail.do?billId={billId}
                link_url = f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}" if bill_id else ""
                # proc_stage_order 계산
                proc_stage_order = calculate_proc_stage_order(proc_stage_cd)
                
                try:
                    cur.execute("""
                        INSERT INTO bills (
                            bill_id, bill_no, title, proposal_date, proposer_kind, proposer_name,
                            proc_stage_cd, pass_gubn, proc_date, general_result,
                            summary_raw, link_url, proc_stage_order, created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                        ON CONFLICT (bill_id) 
                        DO UPDATE SET
                            bill_no = EXCLUDED.bill_no,
                            title = EXCLUDED.title,
                            proposal_date = EXCLUDED.proposal_date,
                            proposer_kind = EXCLUDED.proposer_kind,
                            proposer_name = EXCLUDED.proposer_name,
                            proc_stage_cd = EXCLUDED.proc_stage_cd,
                            pass_gubn = EXCLUDED.pass_gubn,
                            proc_date = EXCLUDED.proc_date,
                            general_result = EXCLUDED.general_result,
                            summary_raw = EXCLUDED.summary_raw,
                            link_url = EXCLUDED.link_url,
                            proc_stage_order = EXCLUDED.proc_stage_order,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        bill_id, bill_no, title, proposal_date, proposer_kind, proposer_name,
                        proc_stage_cd, pass_gubn, proc_date, general_result,
                        summary_raw, link_url, proc_stage_order
                    ))
                    
                    if cur.rowcount > 0:
                        if "INSERT" in str(cur.statusmessage):
                            page_inserted += 1
                            total_inserted += 1
                        else:
                            page_updated += 1
                            total_updated += 1
                
                except Exception as e:
                    print(f"  ⚠️ 오류 (BILL_ID: {bill_id[:20]}...): {e}")
                    conn.rollback()
                    continue
            
            conn.commit()
            print(f"  ✅ 페이지 {page} 완료 (신규: {page_inserted}, 업데이트: {page_updated}, 건너뜀: {page_skipped_old})")
            
            # 연속으로 오래된 데이터만 나오면 조기 종료 (빠른 수집)
            # 페이지의 90% 이상이 이미 수집한 데이터면 더 이상 신규 데이터가 없을 가능성이 높음
            if page_skipped_old > len(items) * 0.9 and page_inserted == 0 and page_updated == 0:
                print(f"  ⚠️ 페이지 {page}: 이미 수집한 데이터만 발견. 신규 데이터 수집 종료.")
                break
            
            if len(items) < page_size:
                break
            
            page += 1
            time.sleep(1)  # API 호출 제한
        
        except Exception as e:
            print(f"  ❌ 페이지 {page} 오류: {e}")
            break
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"수집 완료!")
    print(f"  - 신규 삽입: {total_inserted}건")
    print(f"  - 업데이트: {total_updated}건")
    print(f"  - 총 처리: {total_inserted + total_updated}건")
    if total_skipped_2024 > 0:
        print(f"  - 2024년 데이터 건너뜀: {total_skipped_2024}건")
    if total_skipped_old > 0:
        print(f"  - 이미 수집한 데이터 건너뜀: {total_skipped_old}건")
    print("=" * 60)

if __name__ == '__main__':
    import sys
    # 인자가 없으면 자동으로 최신 데이터만 수집 (빠름)
    # 인자가 있으면 해당 날짜부터 수집
    start_date = sys.argv[1] if len(sys.argv) > 1 else None
    end_date = sys.argv[2] if len(sys.argv) > 2 else None
    collect_bills_from_date(start_date, end_date)

