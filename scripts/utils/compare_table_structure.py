#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
테이블 구조와 인덱스 비교
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

def get_local_db_config():
    return {
        'host': os.environ.get('LOCAL_DB_HOST', 'localhost'),
        'database': os.environ.get('LOCAL_DB_NAME', 'mypoly_lawdata'),
        'user': os.environ.get('LOCAL_DB_USER', 'postgres'),
        'password': os.environ.get('LOCAL_DB_PASSWORD'),
        'port': int(os.environ.get('LOCAL_DB_PORT', '5432'))
    }

def get_vm_db_config():
    return {
        'host': os.environ.get('CLOUD_DB_HOST'),
        'database': os.environ.get('CLOUD_DB_NAME', 'mypoly_lawdata'),
        'user': os.environ.get('CLOUD_DB_USER', 'postgres'),
        'password': os.environ.get('CLOUD_DB_PASSWORD'),
        'port': int(os.environ.get('CLOUD_DB_PORT', '5432'))
    }

def main():
    print("=" * 80)
    print("테이블 구조 및 인덱스 비교")
    print("=" * 80)
    
    local_config = get_local_db_config()
    vm_config = get_vm_db_config()
    
    local_conn = psycopg2.connect(**local_config)
    local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
    
    vm_conn = psycopg2.connect(**vm_config)
    vm_cur = vm_conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 테이블 목록 비교
        print("\n[1] 테이블 목록 비교:")
        print("=" * 80)
        
        local_cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        local_tables = set(row['table_name'] for row in local_cur.fetchall())
        
        vm_cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        vm_tables = set(row['table_name'] for row in vm_cur.fetchall())
        
        only_local = local_tables - vm_tables
        only_vm = vm_tables - local_tables
        
        if only_local:
            print(f"  ❌ localhost에만 있는 테이블: {only_local}")
        if only_vm:
            print(f"  ❌ VM에만 있는 테이블: {only_vm}")
        if not only_local and not only_vm:
            print(f"  ✅ 테이블 목록 일치: {len(local_tables)}개")
        
        # bills 테이블 컬럼 비교
        print("\n[2] bills 테이블 컬럼 비교:")
        print("=" * 80)
        
        local_cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'bills' AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        local_columns = {row['column_name']: row for row in local_cur.fetchall()}
        
        vm_cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'bills' AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        vm_columns = {row['column_name']: row for row in vm_cur.fetchall()}
        
        only_local_cols = set(local_columns.keys()) - set(vm_columns.keys())
        only_vm_cols = set(vm_columns.keys()) - set(local_columns.keys())
        
        if only_local_cols:
            print(f"  ❌ localhost에만 있는 컬럼: {only_local_cols}")
        if only_vm_cols:
            print(f"  ❌ VM에만 있는 컬럼: {only_vm_cols}")
        
        different_types = []
        for col in set(local_columns.keys()) & set(vm_columns.keys()):
            if local_columns[col]['data_type'] != vm_columns[col]['data_type']:
                different_types.append({
                    'column': col,
                    'local': local_columns[col]['data_type'],
                    'vm': vm_columns[col]['data_type']
                })
        
        if different_types:
            print(f"  ❌ 데이터 타입이 다른 컬럼:")
            for diff in different_types:
                print(f"    {diff['column']}: local={diff['local']}, vm={diff['vm']}")
        
        if not only_local_cols and not only_vm_cols and not different_types:
            print(f"  ✅ bills 테이블 컬럼 일치: {len(local_columns)}개")
        
        # 인덱스 비교
        print("\n[3] 인덱스 비교:")
        print("=" * 80)
        
        local_cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = 'bills'
            ORDER BY indexname
        """)
        local_indexes = {row['indexname']: row['indexdef'] for row in local_cur.fetchall()}
        
        vm_cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = 'bills'
            ORDER BY indexname
        """)
        vm_indexes = {row['indexname']: row['indexdef'] for row in vm_cur.fetchall()}
        
        only_local_idx = set(local_indexes.keys()) - set(vm_indexes.keys())
        only_vm_idx = set(vm_indexes.keys()) - set(local_indexes.keys())
        
        if only_local_idx:
            print(f"  ❌ localhost에만 있는 인덱스: {only_local_idx}")
        if only_vm_idx:
            print(f"  ❌ VM에만 있는 인덱스: {only_vm_idx}")
        if not only_local_idx and not only_vm_idx:
            print(f"  ✅ bills 인덱스 일치: {len(local_indexes)}개")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        local_cur.close()
        local_conn.close()
        vm_cur.close()
        vm_conn.close()
    
    print("\n" + "=" * 80)
    print("✅ 비교 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

