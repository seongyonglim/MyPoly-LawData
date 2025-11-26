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

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ENCODED_SERVICE_KEY = os.environ.get(
    "BILL_SERVICE_KEY",
    "MiXjfqnyhsYErA%2FKEzOyLNFwxzbd%2B7VE0k2%2FeVml32gs8WjdeVCOQb06tgG5UaQ7u5bb74Hibe8WkwopNsXceA%3D%3D"
)
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
    # 로컬 개발용 (기본값)
    else:
        return {
            'host': 'localhost',
            'database': 'mypoly_lawdata',
            'user': 'postgres',
            'password': 'maza_970816',
            'port': 5432
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

def collect_bills_from_date(start_date_str="20250801"):
    """특정 날짜부터 의안 정보 수집"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    total_inserted = 0
    total_updated = 0
    
    print("=" * 60)
    print(f"의안 정보 수집 시작 (제안일: {start_date_str} 이후)")
    print("=" * 60)
    
    start_date = parse_date(start_date_str)
    if not start_date:
        print(f"  ❌ 잘못된 날짜 형식: {start_date_str}")
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
            early_exit = False
            
            for item in items:
                bill_id = item.findtext("billId", "").strip()
                if not bill_id:
                    continue
                
                proposal_date = parse_date(item.findtext("proposeDt", ""))
                
                # 제안일이 시작일 이전이면 조기 종료 (날짜순 정렬 가정)
                if proposal_date and proposal_date < start_date:
                    early_exit = True
                    break
                
                # 제안일이 시작일 이후인 것만 저장
                if proposal_date and proposal_date < start_date:
                    continue
                
                bill_no = item.findtext("billNo", "").strip()
                title = item.findtext("billName", "").strip()
                proposer_kind = item.findtext("proposerKind", "").strip()
                proc_stage_cd = item.findtext("procStageCd", "").strip()
                pass_gubn = item.findtext("passGubn", "").strip()
                proc_date = parse_date(item.findtext("procDt", ""))
                general_result = item.findtext("generalResult", "").strip()
                summary_raw = item.findtext("summary", "").strip()
                link_url = item.findtext("linkUrl", "").strip()
                
                try:
                    cur.execute("""
                        INSERT INTO bills (
                            bill_id, bill_no, title, proposal_date, proposer_kind,
                            proc_stage_cd, pass_gubn, proc_date, general_result,
                            summary_raw, link_url, created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                        ON CONFLICT (bill_id) 
                        DO UPDATE SET
                            bill_no = EXCLUDED.bill_no,
                            title = EXCLUDED.title,
                            proposal_date = EXCLUDED.proposal_date,
                            proposer_kind = EXCLUDED.proposer_kind,
                            proc_stage_cd = EXCLUDED.proc_stage_cd,
                            pass_gubn = EXCLUDED.pass_gubn,
                            proc_date = EXCLUDED.proc_date,
                            general_result = EXCLUDED.general_result,
                            summary_raw = EXCLUDED.summary_raw,
                            link_url = EXCLUDED.link_url,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        bill_id, bill_no, title, proposal_date, proposer_kind,
                        proc_stage_cd, pass_gubn, proc_date, general_result,
                        summary_raw, link_url
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
            print(f"  ✅ 페이지 {page} 완료 (신규: {page_inserted}, 업데이트: {page_updated})")
            
            if early_exit:
                print(f"  조기 종료: 제안일이 {start_date_str} 이전인 의안 발견")
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
    print("=" * 60)

if __name__ == '__main__':
    import sys
    start_date = sys.argv[1] if len(sys.argv) > 1 else "20250101"
    collect_bills_from_date(start_date)

