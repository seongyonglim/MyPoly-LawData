#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""제안자 정보 최종 확인"""

import sys
import os
from dotenv import load_dotenv
import psycopg2

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()

def get_db_connection():
    try:
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_name = os.environ.get('DB_NAME', 'mypoly_lawdata')
        db_user = os.environ.get('DB_USER', 'postgres')
        db_password = os.environ.get('DB_PASSWORD')
        if not db_password:
            raise ValueError("DB_PASSWORD environment variable is required")
        db_port = int(os.environ.get('DB_PORT', '5432'))
        
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        return conn
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        raise

conn = get_db_connection()
cur = conn.cursor()

print("=" * 80)
print("제안자 정보 최종 통계")
print("=" * 80)

# 전체 통계
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN proposer_name IS NOT NULL AND proposer_name != '' THEN 1 END) as has_name,
        COUNT(CASE WHEN proposer_kind IS NOT NULL AND proposer_kind != '' THEN 1 END) as has_kind
    FROM bills
    WHERE proposal_date >= '2025-01-01'
""")

result = cur.fetchone()
total = result[0]
has_name = result[1]
has_kind = result[2]

print(f"\n전체 의안: {total:,}건")
print(f"제안자 이름 있음: {has_name:,}건 ({has_name/total*100:.1f}%)")
print(f"제안자 구분 있음: {has_kind:,}건 ({has_kind/total*100:.1f}%)")

# 제안자 구분별 통계
cur.execute("""
    SELECT 
        proposer_kind,
        COUNT(*) as count,
        COUNT(CASE WHEN proposer_name IS NOT NULL AND proposer_name != '' THEN 1 END) as has_name
    FROM bills
    WHERE proposal_date >= '2025-01-01'
    GROUP BY proposer_kind
    ORDER BY count DESC
""")

print("\n제안자 구분별 통계:")
for row in cur.fetchall():
    kind, count, has_name_count = row
    kind_display = kind if kind else '(NULL)'
    name_rate = (has_name_count / count * 100) if count > 0 else 0
    print(f"  {kind_display}: {count:,}건 (이름 있음: {has_name_count:,}건, {name_rate:.1f}%)")

# 제안자 이름이 없는 의안 샘플
cur.execute("""
    SELECT bill_id, title, proposer_kind
    FROM bills
    WHERE proposal_date >= '2025-01-01'
    AND (proposer_name IS NULL OR proposer_name = '')
    LIMIT 5
""")

missing = cur.fetchall()
if missing:
    print(f"\n제안자 이름이 없는 의안 샘플 (최대 5건):")
    for bill_id, title, kind in missing:
        print(f"  - {title[:50]}... (구분: {kind or 'NULL'})")

cur.close()
conn.close()

print("\n" + "=" * 80)

