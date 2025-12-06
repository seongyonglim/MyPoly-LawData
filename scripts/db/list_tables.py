#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""현재 테이블 목록 확인"""

import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host='localhost',
    database='mypoly_lawdata',
    user='postgres',
    password=os.environ.get('DB_PASSWORD'),
    port=5432
)

cur = conn.cursor(cursor_factory=RealDictCursor)

cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE' 
    ORDER BY table_name
""")

tables = [row['table_name'] for row in cur.fetchall()]

print("현재 테이블 목록:")
for t in tables:
    print(f"  - {t}")

print(f"\n총 {len(tables)}개 테이블")

cur.close()
conn.close()

