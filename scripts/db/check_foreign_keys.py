#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
실제 외래키 관계 확인
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

cur.execute("""
    SELECT 
        tc.table_name,
        kcu.column_name as from_column,
        ccu.table_name AS to_table,
        ccu.column_name AS to_column,
        rc.delete_rule as on_delete
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
    LEFT JOIN information_schema.referential_constraints AS rc
        ON rc.constraint_name = tc.constraint_name
        AND rc.constraint_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
    ORDER BY tc.table_name, kcu.column_name
""")

fks = cur.fetchall()

print("=" * 60)
print("실제 외래키 관계")
print("=" * 60)

for fk in fks:
    print(f"{fk['table_name']}.{fk['from_column']} -> {fk['to_table']}.{fk['to_column']} (ON DELETE: {fk['on_delete']})")

print(f"\n총 {len(fks)}개의 외래키 관계가 있습니다.")

cur.close()
conn.close()

