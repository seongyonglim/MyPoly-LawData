#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
현재 데이터베이스 테이블 구조 확인 스크립트
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()

def get_db_config():
    """환경 변수에서 데이터베이스 설정 가져오기"""
    config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD'),
        'port': int(os.environ.get('DB_PORT', '5432'))
    }
    
    if not config['password']:
        raise ValueError("DB_PASSWORD environment variable is required")
    
    return config

def show_table_structure():
    """모든 테이블의 구조 출력"""
    config = get_db_config()
    conn = psycopg2.connect(**config)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("📊 현재 데이터베이스 테이블 구조")
    print("=" * 80)
    
    # 모든 테이블 목록 조회
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    
    tables = [row['table_name'] for row in cur.fetchall()]
    
    for table_name in tables:
        print(f"\n{'=' * 80}")
        print(f"📋 테이블: {table_name}")
        print('=' * 80)
        
        # 컬럼 정보 조회
        cur.execute("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = cur.fetchall()
        
        print(f"\n컬럼 정보 ({len(columns)}개):")
        print("-" * 80)
        print(f"{'컬럼명':<30} {'타입':<25} {'NULL':<8} {'기본값'}")
        print("-" * 80)
        
        for col in columns:
            col_name = col['column_name']
            data_type = col['data_type']
            
            # 길이 정보 추가
            if col['character_maximum_length']:
                data_type += f"({col['character_maximum_length']})"
            
            is_nullable = "YES" if col['is_nullable'] == 'YES' else "NO"
            default = col['column_default'] or ""
            
            # 기본값이 너무 길면 잘라내기
            if len(default) > 30:
                default = default[:27] + "..."
            
            print(f"{col_name:<30} {data_type:<25} {is_nullable:<8} {default}")
        
        # 인덱스 정보 조회
        cur.execute("""
            SELECT
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = %s
            ORDER BY indexname
        """, (table_name,))
        
        indexes = cur.fetchall()
        
        if indexes:
            print(f"\n인덱스 ({len(indexes)}개):")
            print("-" * 80)
            for idx in indexes:
                idx_name = idx['indexname']
                idx_def = idx['indexdef']
                # 인덱스 정의가 너무 길면 잘라내기
                if len(idx_def) > 70:
                    idx_def = idx_def[:67] + "..."
                print(f"  - {idx_name}")
                print(f"    {idx_def}")
        
        # 외래키 정보 조회
        cur.execute("""
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
            AND tc.table_name = %s
        """, (table_name,))
        
        foreign_keys = cur.fetchall()
        
        if foreign_keys:
            print(f"\n외래키 ({len(foreign_keys)}개):")
            print("-" * 80)
            for fk in foreign_keys:
                print(f"  - {fk['column_name']} → {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        # 데이터 개수
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cur.fetchone()['count']
        print(f"\n데이터 개수: {row_count:,}건")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("테이블 구조 확인 완료!")
    print("=" * 80)

if __name__ == '__main__':
    show_table_structure()

