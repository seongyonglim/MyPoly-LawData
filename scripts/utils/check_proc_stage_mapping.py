#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
proc_stage_mapping 확인 및 proc_stage_order 계산
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

def get_db_config():
    return {
        'host': os.environ.get('LOCAL_DB_HOST', 'localhost'),
        'database': os.environ.get('LOCAL_DB_NAME', 'mypoly_lawdata'),
        'user': os.environ.get('LOCAL_DB_USER', 'postgres'),
        'password': os.environ.get('LOCAL_DB_PASSWORD'),
        'port': int(os.environ.get('LOCAL_DB_PORT', '5432'))
    }

def main():
    print("=" * 80)
    print("proc_stage_mapping 확인")
    print("=" * 80)
    
    db_config = get_db_config()
    
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # proc_stage_mapping 테이블 구조 확인
        print("\n[1] proc_stage_mapping 테이블 구조:")
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'proc_stage_mapping'
            ORDER BY ordinal_position
        """)
        cols = cur.fetchall()
        for col in cols:
            print(f"  {col['column_name']}: {col['data_type']}")
        
        # proc_stage_mapping 데이터 확인
        print("\n[2] proc_stage_mapping 데이터:")
        cur.execute("SELECT * FROM proc_stage_mapping")
        mappings = cur.fetchall()
        
        if mappings:
            for m in mappings:
                print(f"  {m}")
        else:
            print("  테이블이 비어있습니다.")
        
        # 실제 bills의 proc_stage_cd 값 확인
        print("\n[2] 실제 bills의 proc_stage_cd 값:")
        cur.execute("""
            SELECT proc_stage_cd, COUNT(*) as cnt
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            GROUP BY proc_stage_cd
            ORDER BY cnt DESC
        """)
        stages = cur.fetchall()
        
        for s in stages:
            print(f"  {s['proc_stage_cd']}: {s['cnt']:,}건")
        
        # proc_stage_order가 NULL인 것 확인
        print("\n[3] proc_stage_order 상태:")
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE proc_stage_order IS NOT NULL) as has_order,
                COUNT(*) FILTER (WHERE proc_stage_order IS NULL) as null_order
            FROM bills
            WHERE proposal_date >= '2025-01-01'
        """)
        result = cur.fetchone()
        
        print(f"  전체: {result['total']:,}건")
        print(f"  proc_stage_order 있음: {result['has_order']:,}건")
        print(f"  proc_stage_order NULL: {result['null_order']:,}건")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cur.close()
        conn.close()
    
    print("\n" + "=" * 80)
    print("✅ 확인 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

