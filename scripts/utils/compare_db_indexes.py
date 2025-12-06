#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
localhost와 VM의 인덱스 구조를 비교하는 스크립트
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

def get_indexes(conn, table_name):
    """테이블의 인덱스 정보 조회"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT 
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename = %s
        ORDER BY indexname
    """, (table_name,))
    return cur.fetchall()

def main():
    print("=" * 80)
    print("localhost와 VM의 인덱스 구조 비교")
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
    
    # 주요 테이블 목록
    tables = ['bills', 'votes', 'assembly_members', 'proc_stage_mapping']
    
    print("\n[3] 인덱스 구조 비교...")
    print("=" * 80)
    
    for table in tables:
        print(f"\n📊 {table} 테이블 인덱스:")
        local_indexes = {idx['indexname']: idx['indexdef'] for idx in get_indexes(local_conn, table)}
        cloud_indexes = {idx['indexname']: idx['indexdef'] for idx in get_indexes(cloud_conn, table)}
        
        only_local = set(local_indexes.keys()) - set(cloud_indexes.keys())
        only_cloud = set(cloud_indexes.keys()) - set(local_indexes.keys())
        common = set(local_indexes.keys()) & set(cloud_indexes.keys())
        
        if only_local:
            print(f"  ⚠️ localhost에만 있는 인덱스 ({len(only_local)}개):")
            for idx_name in sorted(only_local):
                print(f"    - {idx_name}")
                print(f"      {local_indexes[idx_name]}")
        
        if only_cloud:
            print(f"  ⚠️ VM에만 있는 인덱스 ({len(only_cloud)}개):")
            for idx_name in sorted(only_cloud):
                print(f"    - {idx_name}")
                print(f"      {cloud_indexes[idx_name]}")
        
        if not only_local and not only_cloud:
            print(f"  ✅ 인덱스 일치 ({len(common)}개)")
    
    # headline 데이터 확인
    print("\n[4] headline 데이터 확인...")
    print("=" * 80)
    
    local_cur = local_conn.cursor()
    cloud_cur = cloud_conn.cursor()
    
    # localhost
    local_cur.execute("SELECT COUNT(*) FROM bills WHERE headline IS NOT NULL AND headline != ''")
    local_headline_count = local_cur.fetchone()[0]
    
    # VM
    cloud_cur.execute("SELECT COUNT(*) FROM bills WHERE headline IS NOT NULL AND headline != ''")
    cloud_headline_count = cloud_cur.fetchone()[0]
    
    print(f"\nlocalhost headline 데이터: {local_headline_count:,}건")
    print(f"VM headline 데이터: {cloud_headline_count:,}건")
    
    if local_headline_count > 0 and cloud_headline_count == 0:
        print("\n⚠️ localhost에는 headline 데이터가 있지만 VM에는 없습니다!")
        print("   headline 데이터를 VM으로 마이그레이션해야 합니다.")
    
    # 연결 종료
    local_conn.close()
    cloud_conn.close()
    
    print("\n" + "=" * 80)
    print("✅ 비교 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

