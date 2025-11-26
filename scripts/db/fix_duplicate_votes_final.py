#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
중복 표결 데이터 최종 정리 스크립트
"""

import sys
import psycopg2
from datetime import datetime

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

def fix_duplicate_votes():
    """중복 표결 데이터 정리"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("=" * 80)
    print("중복 표결 데이터 정리 시작")
    print("=" * 80)
    
    # 1. 중복 데이터 확인
    print("\n1. 중복 데이터 확인 중...")
    cur.execute("""
        SELECT 
            bill_id, 
            member_no, 
            COALESCE(vote_date, '1900-01-01'::timestamp) as vote_date,
            COUNT(*) as cnt
        FROM votes
        GROUP BY bill_id, member_no, COALESCE(vote_date, '1900-01-01'::timestamp)
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        LIMIT 10
    """)
    
    duplicates = cur.fetchall()
    print(f"   중복 그룹 수: {len(duplicates)}개 (샘플 10개)")
    
    if len(duplicates) == 0:
        print("   ✅ 중복 데이터가 없습니다!")
        cur.close()
        conn.close()
        return
    
    # 전체 중복 개수 확인
    cur.execute("""
        SELECT COUNT(*) 
        FROM (
            SELECT bill_id, member_no, COALESCE(vote_date, '1900-01-01'::timestamp) as vote_date
            FROM votes
            GROUP BY bill_id, member_no, COALESCE(vote_date, '1900-01-01'::timestamp)
            HAVING COUNT(*) > 1
        ) as dup_groups
    """)
    total_duplicate_groups = cur.fetchone()[0]
    
    cur.execute("""
        SELECT SUM(cnt - 1)
        FROM (
            SELECT bill_id, member_no, COALESCE(vote_date, '1900-01-01'::timestamp) as vote_date, COUNT(*) as cnt
            FROM votes
            GROUP BY bill_id, member_no, COALESCE(vote_date, '1900-01-01'::timestamp)
            HAVING COUNT(*) > 1
        ) as dup_counts
    """)
    total_duplicate_records = cur.fetchone()[0] or 0
    
    print(f"   중복 그룹: {total_duplicate_groups:,}개")
    print(f"   삭제할 레코드: {total_duplicate_records:,}건")
    
    # 2. 중복 데이터 삭제 전략
    # - 같은 bill_id, member_no, vote_date 조합에서
    # - member_id가 있는 것을 우선 유지
    # - 모두 member_id가 없으면 가장 최근 것 유지
    print("\n2. 중복 데이터 정리 중...")
    
    # 중복 데이터 중 하나만 남기고 나머지 삭제
    # 우선순위: member_id가 있는 것 > created_at이 최신인 것
    cur.execute("""
        DELETE FROM votes
        WHERE vote_id IN (
            SELECT vote_id
            FROM (
                SELECT 
                    vote_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY bill_id, member_no, COALESCE(vote_date, '1900-01-01'::timestamp)
                        ORDER BY 
                            CASE WHEN member_id IS NOT NULL AND member_id != '' THEN 0 ELSE 1 END,
                            created_at DESC
                    ) as rn
                FROM votes
            ) as ranked
            WHERE rn > 1
        )
    """)
    
    deleted_count = cur.rowcount
    conn.commit()
    
    print(f"   ✅ {deleted_count:,}건의 중복 데이터 삭제 완료")
    
    # 3. 최종 검증
    print("\n3. 최종 검증 중...")
    cur.execute("""
        SELECT 
            bill_id, 
            member_no, 
            COALESCE(vote_date, '1900-01-01'::timestamp) as vote_date,
            COUNT(*) as cnt
        FROM votes
        GROUP BY bill_id, member_no, COALESCE(vote_date, '1900-01-01'::timestamp)
        HAVING COUNT(*) > 1
    """)
    
    remaining_duplicates = cur.fetchall()
    
    if len(remaining_duplicates) == 0:
        print("   ✅ 모든 중복 데이터가 정리되었습니다!")
    else:
        print(f"   ⚠️ 남은 중복: {len(remaining_duplicates)}개")
    
    # 4. 최종 통계
    cur.execute("SELECT COUNT(*) FROM votes")
    final_count = cur.fetchone()[0]
    
    print("\n4. 최종 통계:")
    print(f"   현재 표결 데이터: {final_count:,}건")
    print(f"   삭제된 중복 데이터: {deleted_count:,}건")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("중복 표결 데이터 정리 완료!")
    print("=" * 80)

if __name__ == '__main__':
    fix_duplicate_votes()

