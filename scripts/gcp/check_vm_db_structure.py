#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VM에서 실행: VM의 DB 구조 확인
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
from dotenv import load_dotenv
load_dotenv()

# VM DB 설정 (VM에서 실행 시)
DB = {
    'host': os.environ.get('DB_HOST'),
    'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD'),
    'port': int(os.environ.get('DB_PORT', '5432'))
}

def main():
    print("=" * 80)
    print("VM DB 구조 확인")
    print("=" * 80)
    
    if not DB['host'] or not DB['password']:
        print("❌ DB_HOST와 DB_PASSWORD 환경 변수가 필요합니다.")
        return
    
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        print("✅ VM DB 연결 성공")
    except Exception as e:
        print(f"❌ VM DB 연결 실패: {e}")
        return
    
    try:
        # 테이블 목록
        print("\n[1] 테이블 목록:")
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cur.fetchall()]
        print(f"✅ 총 {len(tables)}개 테이블")
        
        # 주요 테이블 데이터 개수
        print("\n[2] 주요 테이블 데이터 개수:")
        for table in ['bills', 'votes', 'assembly_members', 'proc_stage_mapping']:
            if table == 'bills':
                cur.execute("SELECT COUNT(*) as cnt FROM bills WHERE proposal_date >= '2025-01-01'")
            elif table == 'votes':
                cur.execute("""
                    SELECT COUNT(*) as cnt 
                    FROM votes 
                    WHERE bill_id IN (
                        SELECT bill_id FROM bills WHERE proposal_date >= '2025-01-01'
                    )
                """)
            else:
                cur.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            count = cur.fetchone()['cnt']
            print(f"  {table}: {count:,}건")
        
        # headline 데이터 확인
        print("\n[3] headline 데이터 확인:")
        cur.execute("SELECT COUNT(*) as cnt FROM bills WHERE headline IS NOT NULL AND headline != ''")
        headline_count = cur.fetchone()['cnt']
        print(f"  headline 데이터: {headline_count:,}건")
        
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

