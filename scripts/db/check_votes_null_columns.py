#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
votes 테이블의 NULL 컬럼 확인
"""

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
print("votes 테이블 NULL 컬럼 확인")
print("=" * 80)

null_columns = ['currents_code', 'dept_code', 'display_order', 'law_title', 'bill_url', 'bill_name_url']

for col in null_columns:
    cur.execute(f"SELECT COUNT(*) as total, COUNT({col}) as not_null FROM votes")
    result = cur.fetchone()
    print(f"\n{col}:")
    print(f"  총 행: {result['total']:,}건")
    print(f"  NULL이 아닌 값: {result['not_null']:,}건")
    
    if result['not_null'] > 0:
        cur.execute(f"SELECT DISTINCT {col} FROM votes WHERE {col} IS NOT NULL LIMIT 5")
        samples = cur.fetchall()
        print(f"  샘플 값: {[row[col] for row in samples]}")

cur.close()
conn.close()


