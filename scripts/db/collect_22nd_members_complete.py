#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
22대 모든 국회의원 정보 완전 수집
페이지네이션으로 모든 22대 의원 수집
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

ASSEMBLY_KEY = os.environ.get(
    "ASSEMBLY_SERVICE_KEY",
    "5e85053066dd409b81ed7de0f47bbcab"
)

MEMBER_INFO_API = "https://open.assembly.go.kr/portal/openapi/ALLNAMEMBER"

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

def collect_22nd_members_complete():
    """22대 모든 국회의원 정보 완전 수집"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    total_inserted = 0
    total_updated = 0
    
    print("=" * 80)
    print("22대 모든 국회의원 정보 완전 수집 시작")
    print("=" * 80)
    
    # 페이지네이션으로 모든 의원 수집
    page = 1
    page_size = 300
    max_pages = 10  # 22대는 약 300명이므로 충분
    
    while page <= max_pages:
        print(f"\n페이지 {page} 처리 중...")
        params = {
            "KEY": ASSEMBLY_KEY,
            "Type": "xml",
            "pIndex": page,
            "pSize": page_size,
            "AGE": "22"
        }
        
        try:
            response = requests.get(MEMBER_INFO_API, params=params, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            items = root.findall(".//row")
            
            if not items:
                print(f"  페이지 {page}: 데이터 없음, 수집 종료")
                break
            
            print(f"  페이지 {page}: {len(items)}건 조회")
            
            page_inserted = 0
            page_updated = 0
            
            for item in items:
                member_id = item.findtext("NAAS_CD", "").strip()
                if not member_id:
                    continue
                
                name = item.findtext("NAAS_NM", "").strip()
                party = item.findtext("PLPT_NM", "").strip()
                district = item.findtext("ELECD_NM", "").strip()
                committee = item.findtext("BLNG_CMIT_NM", "").strip()
                era = item.findtext("GTELT_ERACO", "").strip()
                gender = item.findtext("NTR_DIV", "").strip()
                birth_date = parse_date(item.findtext("BTH_DT", ""))
                photo_url = item.findtext("PHOTO_URL", "").strip()
                phone = item.findtext("TEL_NO", "").strip()
                email = item.findtext("E_MAIL", "").strip()
                homepage_url = item.findtext("HOMEPAGE_URL", "").strip()
                aide_name = item.findtext("AIDE_NM", "").strip()
                secretary_name = item.findtext("SECRETARY_NM", "").strip()
                
                # 22대가 아닌 경우 건너뛰기
                if era and '22대' not in era:
                    continue
                
                try:
                    cur.execute("""
                        INSERT INTO assembly_members (
                            member_id, name, party, district, committee, era, gender,
                            birth_date, photo_url, phone, email, homepage_url,
                            aide_name, secretary_name, created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                        ON CONFLICT (member_id) 
                        DO UPDATE SET
                            name = EXCLUDED.name,
                            party = EXCLUDED.party,
                            district = EXCLUDED.district,
                            committee = EXCLUDED.committee,
                            era = EXCLUDED.era,
                            gender = EXCLUDED.gender,
                            birth_date = EXCLUDED.birth_date,
                            photo_url = EXCLUDED.photo_url,
                            phone = EXCLUDED.phone,
                            email = EXCLUDED.email,
                            homepage_url = EXCLUDED.homepage_url,
                            aide_name = EXCLUDED.aide_name,
                            secretary_name = EXCLUDED.secretary_name,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        member_id, name, party, district, committee, era, gender,
                        birth_date, photo_url, phone, email, homepage_url,
                        aide_name, secretary_name
                    ))
                    
                    if cur.rowcount > 0:
                        if "INSERT" in str(cur.statusmessage):
                            page_inserted += 1
                            total_inserted += 1
                        else:
                            page_updated += 1
                            total_updated += 1
                
                except Exception as e:
                    print(f"  ⚠️ 오류 (MEMBER_ID: {member_id}): {e}")
                    conn.rollback()
                    continue
            
            conn.commit()
            print(f"  ✅ 페이지 {page} 완료 (신규: {page_inserted}, 업데이트: {page_updated})")
            
            # 다음 페이지가 없으면 종료
            if len(items) < page_size:
                break
            
            page += 1
            time.sleep(1)  # API 호출 제한
            
        except Exception as e:
            print(f"  ❌ 페이지 {page} 오류: {e}")
            conn.rollback()
            break
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print(f"수집 완료!")
    print(f"  - 신규 삽입: {total_inserted:,}건")
    print(f"  - 업데이트: {total_updated:,}건")
    print(f"  - 총 처리: {total_inserted + total_updated:,}건")
    print("=" * 80)

if __name__ == '__main__':
    collect_22nd_members_complete()

