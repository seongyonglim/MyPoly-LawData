#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
추후 기능에 사용되지 않는 테이블 삭제

삭제 대상:
- member_id_mapping: 과거 매핑 기록, 현재 사용 안 함 (votes.member_id가 이미 모두 매핑됨)

유지할 테이블 (추후 기능용):
- user_votes: Phase 1 - 사용자 투표 기능
- user_political_profile: Phase 3 - 사용자 정치성향 테스트
- member_political_profile: Phase 3 - 의원 정치성향 프로필
- bill_similarity: Phase 3 - 의안 유사도 계산
- proc_stage_mapping: 현재 사용 중 (설정 테이블)
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

DB_CONFIG = {
    'host': 'localhost',
    'database': 'mypoly_lawdata',
    'user': 'postgres',
    'password': 'maza_970816',
    'port': 5432
}

def delete_unused_tables():
    """불필요한 테이블 삭제"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("불필요한 테이블 삭제")
    print("=" * 80)
    
    # 삭제할 테이블 목록
    tables_to_delete = ['member_id_mapping']
    
    for table_name in tables_to_delete:
        # 테이블 존재 확인
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            ) as exists
        """, (table_name,))
        
        exists = cur.fetchone()['exists']
        
        if not exists:
            print(f"\n⚠️ {table_name}: 테이블이 존재하지 않습니다.")
            continue
        
        # 데이터 개수 확인
        cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        count = cur.fetchone()['count']
        
        print(f"\n[{table_name}]")
        print(f"  데이터 개수: {count:,}건")
        print(f"  삭제 사유: 과거 매핑 기록, 현재 사용 안 함")
        
        # 자동 삭제 (사용자 확인 없이)
        print(f"\n  삭제 진행 중...")
        
        # 테이블 삭제
        try:
            cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            conn.commit()
            print(f"  ✅ {table_name} 테이블 삭제 완료")
        except Exception as e:
            conn.rollback()
            print(f"  ❌ 삭제 실패: {e}")
    
    # 유지할 테이블 목록 확인
    print("\n" + "=" * 80)
    print("유지할 테이블 (추후 기능용)")
    print("=" * 80)
    
    future_tables = {
        'user_votes': 'Phase 1 - 사용자 투표 기능',
        'user_political_profile': 'Phase 3 - 사용자 정치성향 테스트',
        'member_political_profile': 'Phase 3 - 의원 정치성향 프로필',
        'bill_similarity': 'Phase 3 - 의안 유사도 계산',
        'proc_stage_mapping': '현재 사용 중 - 진행 단계 매핑'
    }
    
    for table_name, purpose in future_tables.items():
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            ) as exists
        """, (table_name,))
        
        exists = cur.fetchone()['exists']
        status = "✅ 존재" if exists else "❌ 없음"
        
        cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        count = cur.fetchone()['count']
        
        print(f"{status} {table_name}: {count:,}건 - {purpose}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("작업 완료!")
    print("=" * 80)

if __name__ == '__main__':
    delete_unused_tables()

