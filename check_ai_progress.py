# -*- coding: utf-8 -*-
"""AI 요약 진행 상황 확인"""

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
print("AI 요약 진행 상황 확인")
print("=" * 80)
print()

# 전체 통계
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN summary IS NOT NULL AND summary != '' THEN 1 END) as processed,
        COUNT(CASE WHEN summary IS NULL OR summary = '' THEN 1 END) as unprocessed
    FROM bills
    WHERE proposal_date >= '2025-01-01'
""")
stats = cur.fetchone()
print(f"전체 의안: {stats['total']:,}개")
print(f"AI 요약 완료: {stats['processed']:,}개 ({stats['processed']/stats['total']*100:.1f}%)")
print(f"AI 요약 미완료: {stats['unprocessed']:,}개 ({stats['unprocessed']/stats['total']*100:.1f}%)")
print()

# 원문 있는 의안 중 미처리된 것
cur.execute("""
    SELECT 
        COUNT(*) as count
    FROM bills
    WHERE proposal_date >= '2025-01-01'
      AND (summary IS NULL OR summary = '')
      AND (summary_raw IS NOT NULL AND summary_raw != '')
      AND bill_no IS NOT NULL
""")
with_raw_unprocessed = cur.fetchone()
print(f"원문 있지만 AI 요약 미완료: {with_raw_unprocessed['count']:,}개")
print()

# 다음에 처리될 의안 (의안번호 순서)
cur.execute("""
    SELECT bill_no, title, proposal_date, proposer_kind
    FROM bills
    WHERE proposal_date >= '2025-01-01'
      AND (summary IS NULL OR summary = '')
      AND (summary_raw IS NOT NULL AND summary_raw != '')
      AND bill_no IS NOT NULL
    ORDER BY 
        CASE 
            WHEN bill_no ~ '^ZZ[0-9]+$' THEN CAST(SUBSTRING(bill_no FROM '([0-9]+)') AS INTEGER) - 1000000000
            WHEN bill_no ~ '^[0-9]+$' THEN CAST(bill_no AS INTEGER)
            WHEN bill_no ~ '^제[0-9]+호$' THEN CAST(SUBSTRING(bill_no FROM '([0-9]+)') AS INTEGER)
            ELSE 999999999
        END ASC,
        proposal_date ASC,
        bill_id ASC
    LIMIT 10
""")
next_bills = cur.fetchall()
print("다음에 처리될 의안 (의안번호 순서, 처음 10개):")
for i, bill in enumerate(next_bills, 1):
    title_short = (bill['title'] or '')[:50] + '...' if bill['title'] and len(bill['title']) > 50 else (bill['title'] or 'N/A')
    print(f"  {i:2d}. {bill['bill_no'] or 'N/A':15s} | {bill['proposal_date'] or 'N/A':12s} | {title_short}")

# 처리된 의안 중 가장 큰 의안번호
cur.execute("""
    SELECT bill_no, title, proposal_date
    FROM bills
    WHERE proposal_date >= '2025-01-01'
      AND summary IS NOT NULL 
      AND summary != ''
      AND bill_no IS NOT NULL
    ORDER BY 
        CASE 
            WHEN bill_no ~ '^ZZ[0-9]+$' THEN CAST(SUBSTRING(bill_no FROM '([0-9]+)') AS INTEGER) - 1000000000
            WHEN bill_no ~ '^[0-9]+$' THEN CAST(bill_no AS INTEGER)
            WHEN bill_no ~ '^제[0-9]+호$' THEN CAST(SUBSTRING(bill_no FROM '([0-9]+)') AS INTEGER)
            ELSE 999999999
        END DESC
    LIMIT 5
""")
last_processed = cur.fetchall()
print()
print("가장 최근에 처리된 의안 (의안번호 순서, 마지막 5개):")
for i, bill in enumerate(last_processed, 1):
    title_short = (bill['title'] or '')[:50] + '...' if bill['title'] and len(bill['title']) > 50 else (bill['title'] or 'N/A')
    print(f"  {i:2d}. {bill['bill_no'] or 'N/A':15s} | {bill['proposal_date'] or 'N/A':12s} | {title_short}")

cur.close()
conn.close()

print()
print("=" * 80)

