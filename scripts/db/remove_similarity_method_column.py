#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
bill_similarity 테이블에서 similarity_method 컬럼 제거
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
from dotenv import load_dotenv

load_dotenv()

def get_db_config():
    return {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD'),
        'port': int(os.environ.get('DB_PORT', '5432'))
    }

def remove_similarity_method_column():
    """similarity_method 컬럼 제거"""
    config = get_db_config()
    if not config['password']:
        raise ValueError("DB_PASSWORD environment variable is required")
    conn = psycopg2.connect(**config)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("bill_similarity 테이블에서 similarity_method 컬럼 제거")
    print("=" * 80)
    
    try:
        # 테이블 존재 확인
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'bill_similarity'
            ) as exists
        """)
        
        exists = cur.fetchone()['exists']
        
        if not exists:
            print("⚠️ bill_similarity 테이블이 존재하지 않습니다.")
            return
        
        # 컬럼 존재 확인
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'bill_similarity'
                AND column_name = 'similarity_method'
            ) as exists
        """)
        
        col_exists = cur.fetchone()['exists']
        
        if not col_exists:
            print("✅ similarity_method 컬럼이 이미 존재하지 않습니다.")
            return
        
        # 인덱스 제거 (먼저 인덱스가 있으면 제거)
        try:
            cur.execute("DROP INDEX IF EXISTS idx_similarity_method")
            print("✅ idx_similarity_method 인덱스 제거 완료")
        except Exception as e:
            print(f"⚠️ 인덱스 제거 중 오류 (무시 가능): {e}")
        
        # 컬럼 제거
        cur.execute("ALTER TABLE bill_similarity DROP COLUMN IF EXISTS similarity_method")
        conn.commit()
        
        print("✅ similarity_method 컬럼 제거 완료")
        
        # 최종 확인
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'bill_similarity'
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        print("\n현재 bill_similarity 테이블 컬럼:")
        for col in columns:
            print(f"  - {col['column_name']} ({col['data_type']})")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cur.close()
        conn.close()
    
    print("\n" + "=" * 80)
    print("작업 완료!")
    print("=" * 80)

if __name__ == '__main__':
    remove_similarity_method_column()

