#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
localhost와 VM의 DB 구조를 비교하는 스크립트
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# .env 파일 로드
if sys.platform == 'win32':
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_file):
        encodings = ['utf-8', 'utf-8-sig', 'cp949', 'latin-1']
        for encoding in encodings:
            try:
                with open(env_file, 'r', encoding=encoding) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key and value:
                                os.environ[key] = value
                break
            except (UnicodeDecodeError, Exception):
                continue
else:
    from dotenv import load_dotenv
    load_dotenv()

# 로컬 DB 설정
LOCAL_DB = {
    'host': os.environ.get('LOCAL_DB_HOST', 'localhost'),
    'database': os.environ.get('LOCAL_DB_NAME', 'mypoly_lawdata'),
    'user': os.environ.get('LOCAL_DB_USER', 'postgres'),
    'password': os.environ.get('LOCAL_DB_PASSWORD'),
    'port': int(os.environ.get('LOCAL_DB_PORT', '5432'))
}

# Cloud SQL 설정
CLOUD_DB = {
    'host': os.environ.get('CLOUD_DB_HOST'),
    'database': os.environ.get('CLOUD_DB_NAME', 'mypoly_lawdata'),
    'user': os.environ.get('CLOUD_DB_USER', 'postgres'),
    'password': os.environ.get('CLOUD_DB_PASSWORD'),
    'port': int(os.environ.get('CLOUD_DB_PORT', '5432'))
}

def get_tables(conn):
    """테이블 목록 조회"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    return [row['table_name'] for row in cur.fetchall()]

def get_columns(conn, table_name):
    """테이블의 컬럼 정보 조회"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    return cur.fetchall()

def get_row_count(conn, table_name):
    """테이블의 행 개수 조회"""
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cur.fetchone()[0]

def main():
    print("=" * 80)
    print("localhost와 VM의 DB 구조 비교")
    print("=" * 80)
    
    # 로컬 DB 연결
    print("\n[1] localhost DB 연결 중...")
    try:
        local_conn = psycopg2.connect(**LOCAL_DB)
        print("✅ localhost DB 연결 성공")
    except Exception as e:
        print(f"❌ localhost DB 연결 실패: {e}")
        return
    
    # Cloud SQL 연결
    print("\n[2] VM (Cloud SQL) DB 연결 중...")
    if not CLOUD_DB['host'] or not CLOUD_DB['password']:
        print("❌ CLOUD_DB_HOST와 CLOUD_DB_PASSWORD 환경 변수가 필요합니다.")
        local_conn.close()
        return
    
    try:
        cloud_conn = psycopg2.connect(**CLOUD_DB)
        print("✅ VM DB 연결 성공")
    except Exception as e:
        print(f"❌ VM DB 연결 실패: {e}")
        local_conn.close()
        return
    
    # 테이블 목록 비교
    print("\n[3] 테이블 목록 비교...")
    print("=" * 80)
    
    local_tables = set(get_tables(local_conn))
    cloud_tables = set(get_tables(cloud_conn))
    
    print(f"\nlocalhost 테이블 수: {len(local_tables)}")
    print(f"VM 테이블 수: {len(cloud_tables)}")
    
    only_local = local_tables - cloud_tables
    only_cloud = cloud_tables - local_tables
    common_tables = local_tables & cloud_tables
    
    if only_local:
        print(f"\n⚠️ localhost에만 있는 테이블 ({len(only_local)}개):")
        for table in sorted(only_local):
            print(f"  - {table}")
    
    if only_cloud:
        print(f"\n⚠️ VM에만 있는 테이블 ({len(only_cloud)}개):")
        for table in sorted(only_cloud):
            count = get_row_count(cloud_conn, table)
            print(f"  - {table} ({count:,}건)")
    
    print(f"\n✅ 공통 테이블 ({len(common_tables)}개):")
    for table in sorted(common_tables):
        local_count = get_row_count(local_conn, table)
        cloud_count = get_row_count(cloud_conn, table)
        status = "✅" if local_count == cloud_count else "⚠️"
        print(f"  {status} {table}: localhost={local_count:,}, VM={cloud_count:,}")
    
    # 컬럼 구조 비교
    print("\n[4] 주요 테이블의 컬럼 구조 비교...")
    print("=" * 80)
    
    for table in sorted(common_tables):
        local_cols = {col['column_name']: col for col in get_columns(local_conn, table)}
        cloud_cols = {col['column_name']: col for col in get_columns(cloud_conn, table)}
        
        only_local_cols = set(local_cols.keys()) - set(cloud_cols.keys())
        only_cloud_cols = set(cloud_cols.keys()) - set(local_cols.keys())
        
        if only_local_cols or only_cloud_cols:
            print(f"\n⚠️ {table} 테이블 컬럼 차이:")
            if only_local_cols:
                print(f"  localhost에만 있는 컬럼: {sorted(only_local_cols)}")
            if only_cloud_cols:
                print(f"  VM에만 있는 컬럼: {sorted(only_cloud_cols)}")
    
    # 연결 종료
    local_conn.close()
    cloud_conn.close()
    
    print("\n" + "=" * 80)
    print("✅ 비교 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

