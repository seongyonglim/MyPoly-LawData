# -*- coding: utf-8 -*-
"""처리된 의안 범위 내에서 건너뛰어진 의안 확인"""

import sys
import os

# Windows 환경에서 한글 출력을 위한 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host='localhost',
    database='mypoly_lawdata',
    user='postgres',
    password='maza_970816',
    port=5432
)
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("처리된 의안 범위 내에서 건너뛰어진 의안 확인")
print("=" * 80)
print()

# 처리된 의안의 의안번호 범위 확인
cur.execute("""
    SELECT 
        MIN(CASE 
            WHEN bill_no ~ '^ZZ[0-9]+$' THEN CAST(SUBSTRING(bill_no FROM '([0-9]+)') AS INTEGER) - 1000000000
            WHEN bill_no ~ '^[0-9]+$' THEN CAST(bill_no AS INTEGER)
            WHEN bill_no ~ '^제[0-9]+호$' THEN CAST(SUBSTRING(bill_no FROM '([0-9]+)') AS INTEGER)
            ELSE 999999999
        END) as min_bill_no,
        MAX(CASE 
            WHEN bill_no ~ '^ZZ[0-9]+$' THEN CAST(SUBSTRING(bill_no FROM '([0-9]+)') AS INTEGER) - 1000000000
            WHEN bill_no ~ '^[0-9]+$' THEN CAST(bill_no AS INTEGER)
            WHEN bill_no ~ '^제[0-9]+호$' THEN CAST(SUBSTRING(bill_no FROM '([0-9]+)') AS INTEGER)
            ELSE 999999999
        END) as max_bill_no
    FROM bills
    WHERE proposal_date >= '2025-01-01'
      AND summary IS NOT NULL 
      AND summary != ''
      AND bill_no IS NOT NULL
""")
range_info = cur.fetchone()

print(f"처리된 의안 범위:")
print(f"  최소 의안번호: {range_info['min_bill_no']}")
print(f"  최대 의안번호: {range_info['max_bill_no']}")
print()

# 처리된 의안 범위 내에서 미처리된 의안 찾기
cur.execute("""
    WITH processed_range AS (
        SELECT 
            MIN(CASE 
                WHEN bill_no ~ '^ZZ[0-9]+$' THEN CAST(SUBSTRING(bill_no FROM '([0-9]+)') AS INTEGER) - 1000000000
                WHEN bill_no ~ '^[0-9]+$' THEN CAST(bill_no AS INTEGER)
                WHEN bill_no ~ '^제[0-9]+호$' THEN CAST(SUBSTRING(bill_no FROM '([0-9]+)') AS INTEGER)
                ELSE 999999999
            END) as min_no,
            MAX(CASE 
                WHEN bill_no ~ '^ZZ[0-9]+$' THEN CAST(SUBSTRING(bill_no FROM '([0-9]+)') AS INTEGER) - 1000000000
                WHEN bill_no ~ '^[0-9]+$' THEN CAST(bill_no AS INTEGER)
                WHEN bill_no ~ '^제[0-9]+호$' THEN CAST(SUBSTRING(bill_no FROM '([0-9]+)') AS INTEGER)
                ELSE 999999999
            END) as max_no
        FROM bills
        WHERE proposal_date >= '2025-01-01'
          AND summary IS NOT NULL 
          AND summary != ''
          AND bill_no IS NOT NULL
    )
    SELECT 
        b.bill_no,
        b.title,
        b.proposal_date,
        b.proposer_kind,
        CASE 
            WHEN b.bill_no ~ '^ZZ[0-9]+$' THEN CAST(SUBSTRING(b.bill_no FROM '([0-9]+)') AS INTEGER) - 1000000000
            WHEN b.bill_no ~ '^[0-9]+$' THEN CAST(b.bill_no AS INTEGER)
            WHEN b.bill_no ~ '^제[0-9]+호$' THEN CAST(SUBSTRING(b.bill_no FROM '([0-9]+)') AS INTEGER)
            ELSE 999999999
        END as bill_no_num
    FROM bills b, processed_range pr
    WHERE b.proposal_date >= '2025-01-01'
      AND (b.summary IS NULL OR b.summary = '')
      AND (b.summary_raw IS NOT NULL AND b.summary_raw != '')
      AND b.bill_no IS NOT NULL
      AND CASE 
            WHEN b.bill_no ~ '^ZZ[0-9]+$' THEN CAST(SUBSTRING(b.bill_no FROM '([0-9]+)') AS INTEGER) - 1000000000
            WHEN b.bill_no ~ '^[0-9]+$' THEN CAST(b.bill_no AS INTEGER)
            WHEN b.bill_no ~ '^제[0-9]+호$' THEN CAST(SUBSTRING(b.bill_no FROM '([0-9]+)') AS INTEGER)
            ELSE 999999999
          END BETWEEN pr.min_no AND pr.max_no
    ORDER BY bill_no_num
    LIMIT 30
""")
skipped = cur.fetchall()

print(f"처리된 범위 내에서 건너뛰어진 의안: {len(skipped)}개 (처음 30개)")
if len(skipped) > 0:
    print()
    for i, bill in enumerate(skipped, 1):
        title_short = (bill['title'] or '')[:50] + '...' if bill['title'] and len(bill['title']) > 50 else (bill['title'] or 'N/A')
        print(f"  {i:2d}. {bill['bill_no']:15s} | {bill['proposal_date'] or 'N/A':12s} | {title_short}")
    print()
    print("⚠️ 건너뛰어진 의안이 발견되었습니다. 이 의안들을 처리해야 합니다.")
else:
    print("✓ 처리된 범위 내에서 건너뛰어진 의안이 없습니다.")

cur.close()
conn.close()

print()
print("=" * 80)

