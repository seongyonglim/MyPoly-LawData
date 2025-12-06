#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
bills 테이블의 proposer 관련 컬럼 확인
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == 'win32':
    import io as win_io
    sys.stdout = win_io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = win_io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def get_db_config():
    if 'DATABASE_URL' in os.environ:
        from urllib.parse import urlparse
        db_url = urlparse(os.environ['DATABASE_URL'])
        return {
            'host': db_url.hostname,
            'database': db_url.path[1:],
            'user': db_url.username,
            'password': db_url.password,
            'port': db_url.port or 5432
        }
    elif 'DB_HOST' in os.environ:
        host = os.environ.get('DB_HOST', '')
        if not host.endswith('.render.com') and not '.' in host:
            host = f"{host}.oregon-postgres.render.com"
        return {
            'host': host,
            'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': os.environ.get('DB_PASSWORD'),
            'port': int(os.environ.get('DB_PORT', 5432))
        }
    else:
        password = os.environ.get('DB_PASSWORD')
        if not password:
            raise ValueError("DB_PASSWORD environment variable is required")
        return {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': password,
            'port': int(os.environ.get('DB_PORT', '5432'))
        }

def check_proposer_column():
    config = get_db_config()
    conn = psycopg2.connect(**config)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 60)
    print("bills 테이블 proposer 관련 컬럼 확인")
    print("=" * 60)
    
    # proposer 관련 컬럼 확인
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'bills'
        AND (column_name LIKE '%proposer%' OR column_name LIKE '%제안%')
        ORDER BY ordinal_position
    """)
    
    columns = cur.fetchall()
    print("\n[1] proposer 관련 컬럼:")
    if columns:
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} (NULL: {col['is_nullable']})")
    else:
        print("  proposer 관련 컬럼이 없습니다!")
    
    # 샘플 데이터 확인
    print("\n[2] 샘플 데이터:")
    cur.execute("""
        SELECT bill_id, title, proposer_kind
        FROM bills
        LIMIT 5
    """)
    samples = cur.fetchall()
    for s in samples:
        print(f"  bill_id={s['bill_id']}")
        print(f"    title={s['title'][:50]}...")
        print(f"    proposer_kind={s['proposer_kind']}")
        print()
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    check_proposer_column()

