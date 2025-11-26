#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
제안자 이름 누락 보완 스크립트
"""

import sys
import re
import psycopg2

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

DB_CONFIG = {
    'host': 'localhost',
    'database': 'mypoly_lawdata',
    'user': 'postgres',
    'password': 'maza_970816',
    'port': 5432
}

def extract_proposer_from_title(title):
    """제목에서 제안자 이름 추출"""
    if not title:
        return None
    
    # 패턴 1: "법률안(홍길동의원 등 10인)"
    match = re.search(r'\(([^)]+의원)\s*등\s*\d+인\)', title)
    if match:
        name = match.group(1).replace('의원', '').strip()
        return name
    
    # 패턴 2: "법률안(홍길동의원)"
    match = re.search(r'\(([^)]+의원)\)', title)
    if match:
        name = match.group(1).replace('의원', '').strip()
        return name
    
    # 패턴 3: "법률안(홍길동 등 10인)"
    match = re.search(r'\(([^)]+)\s*등\s*\d+인\)', title)
    if match:
        name = match.group(1).strip()
        # "의원"이 포함되어 있으면 제거
        name = name.replace('의원', '').strip()
        return name
    
    return None

def improve_missing_proposer_names():
    """제안자 이름 누락 보완"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("=" * 80)
    print("제안자 이름 누락 보완 시작")
    print("=" * 80)
    
    # 1. 제안자 이름이 없는 의안 확인
    print("\n1. 제안자 이름 누락 의안 확인 중...")
    cur.execute("""
        SELECT bill_id, title, proposer_kind
        FROM bills
        WHERE proposal_date >= '2025-01-01'
        AND (proposer_name IS NULL OR proposer_name = '')
        AND proposer_kind = '의원'
    """)
    
    missing_bills = cur.fetchall()
    print(f"   제안자 이름 누락 의안: {len(missing_bills):,}건")
    
    if len(missing_bills) == 0:
        print("   ✅ 제안자 이름이 모두 채워져 있습니다!")
        cur.close()
        conn.close()
        return
    
    # 2. 제목에서 제안자 이름 추출
    print("\n2. 제목에서 제안자 이름 추출 중...")
    updated_count = 0
    
    for bill_id, title, proposer_kind in missing_bills:
        extracted_name = extract_proposer_from_title(title)
        
        if extracted_name:
            try:
                cur.execute("""
                    UPDATE bills
                    SET proposer_name = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE bill_id = %s
                """, (extracted_name, bill_id))
                updated_count += 1
            except Exception as e:
                print(f"   ⚠️ 오류 (BILL_ID: {bill_id[:20]}...): {e}")
                conn.rollback()
                continue
    
    conn.commit()
    print(f"   ✅ {updated_count:,}건의 제안자 이름 업데이트 완료")
    
    # 3. 최종 검증
    print("\n3. 최종 검증 중...")
    cur.execute("""
        SELECT COUNT(*) 
        FROM bills
        WHERE proposal_date >= '2025-01-01'
        AND (proposer_name IS NULL OR proposer_name = '')
        AND proposer_kind = '의원'
    """)
    
    remaining = cur.fetchone()[0]
    print(f"   남은 제안자 이름 누락: {remaining:,}건")
    
    if remaining > 0:
        print(f"   ⚠️ {remaining:,}건은 제목에서 추출할 수 없습니다.")
        print("   (수동 보완 또는 API 재수집 필요)")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("제안자 이름 누락 보완 완료!")
    print("=" * 80)

if __name__ == '__main__':
    improve_missing_proposer_names()

