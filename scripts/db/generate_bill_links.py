#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
의안 link_url 생성
국회 홈페이지 의안 상세 페이지 URL 생성
"""

import sys
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

def generate_bill_link(bill_id, bill_no):
    """의안 링크 생성"""
    # 국회 홈페이지 의안 상세 페이지 URL 형식
    # https://likms.assembly.go.kr/bill/billDetail.do?billId=BILL_ID
    if bill_id:
        return f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
    return None

def update_bill_links():
    """의안 link_url 업데이트"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("=" * 80)
    print("의안 link_url 생성 및 업데이트")
    print("=" * 80)
    
    # link_url이 없는 의안들에 대해 링크 생성
    cur.execute("""
        SELECT bill_id, bill_no
        FROM bills
        WHERE proposal_date >= '2025-01-01'
        AND (link_url IS NULL OR link_url = '')
    """)
    
    bills = cur.fetchall()
    print(f"\n처리할 의안 수: {len(bills):,}건")
    
    updated_count = 0
    for bill_id, bill_no in bills:
        link_url = generate_bill_link(bill_id, bill_no)
        if link_url:
            try:
                cur.execute("""
                    UPDATE bills
                    SET link_url = %s
                    WHERE bill_id = %s
                """, (link_url, bill_id))
                
                if cur.rowcount > 0:
                    updated_count += 1
            except Exception as e:
                print(f"  ⚠️ 오류 (bill_id: {bill_id[:20]}...): {e}")
                conn.rollback()
                continue
    
    conn.commit()
    print(f"\n✅ {updated_count:,}건 업데이트 완료")
    
    # 최종 통계
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN link_url IS NOT NULL AND link_url != '' THEN 1 END) as with_link
        FROM bills
        WHERE proposal_date >= '2025-01-01'
    """)
    
    total, with_link = cur.fetchone()
    print(f"\n최종 통계:")
    print(f"  전체 의안: {total:,}건")
    print(f"  link_url 있는 의안: {with_link:,}건 ({with_link/total*100:.1f}%)")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("완료!")
    print("=" * 80)

if __name__ == '__main__':
    update_bill_links()

