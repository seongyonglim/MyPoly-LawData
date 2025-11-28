#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
최종 데이터 검증 스크립트
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor
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

def validate_data():
    """데이터 검증"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("데이터 최종 검증 리포트")
    print(f"검증일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # 1. 기본 데이터 존재 확인
    print("\n[1] 기본 데이터 존재 확인")
    print("-" * 80)
    
    cur.execute("SELECT COUNT(*) as count FROM bills")
    bills_count = cur.fetchone()['count']
    if bills_count == 0:
        errors.append("bills 테이블에 데이터가 없습니다")
    else:
        print(f"✅ bills: {bills_count:,}건")
    
    cur.execute("SELECT COUNT(*) as count FROM assembly_members")
    members_count = cur.fetchone()['count']
    if members_count == 0:
        errors.append("assembly_members 테이블에 데이터가 없습니다")
    else:
        print(f"✅ assembly_members: {members_count:,}건")
    
    cur.execute("SELECT COUNT(*) as count FROM votes")
    votes_count = cur.fetchone()['count']
    if votes_count == 0:
        errors.append("votes 테이블에 데이터가 없습니다")
    else:
        print(f"✅ votes: {votes_count:,}건")
    
    # 2. 외래키 무결성 확인
    print("\n[2] 외래키 무결성 확인")
    print("-" * 80)
    
    # votes.bill_id가 bills.bill_id를 참조하는지 확인
    cur.execute("""
        SELECT COUNT(*) as count
        FROM votes v
        LEFT JOIN bills b ON v.bill_id = b.bill_id
        WHERE b.bill_id IS NULL
    """)
    orphan_votes = cur.fetchone()['count']
    if orphan_votes > 0:
        errors.append(f"votes 테이블에 매핑되지 않은 bill_id가 {orphan_votes:,}건 있습니다")
    else:
        print("✅ votes.bill_id → bills.bill_id: 모든 표결이 의안과 매핑됨")
    
    # votes.member_id가 assembly_members.member_id를 참조하는지 확인
    cur.execute("""
        SELECT COUNT(*) as count
        FROM votes v
        WHERE v.member_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM assembly_members am WHERE am.member_id = v.member_id
        )
    """)
    orphan_member_ids = cur.fetchone()['count']
    if orphan_member_ids > 0:
        warnings.append(f"votes 테이블에 매핑되지 않은 member_id가 {orphan_member_ids:,}건 있습니다")
    else:
        print("✅ votes.member_id → assembly_members.member_id: 모든 의원 ID가 매핑됨")
    
    # 3. 필수 필드 NULL 확인
    print("\n[3] 필수 필드 NULL 확인")
    print("-" * 80)
    
    cur.execute("SELECT COUNT(*) as count FROM bills WHERE bill_id IS NULL OR title IS NULL")
    null_bills = cur.fetchone()['count']
    if null_bills > 0:
        errors.append(f"bills 테이블에 필수 필드가 NULL인 행이 {null_bills:,}건 있습니다")
    else:
        print("✅ bills: 필수 필드 모두 존재")
    
    cur.execute("SELECT COUNT(*) as count FROM assembly_members WHERE member_id IS NULL OR name IS NULL")
    null_members = cur.fetchone()['count']
    if null_members > 0:
        errors.append(f"assembly_members 테이블에 필수 필드가 NULL인 행이 {null_members:,}건 있습니다")
    else:
        print("✅ assembly_members: 필수 필드 모두 존재")
    
    cur.execute("SELECT COUNT(*) as count FROM votes WHERE vote_id IS NULL OR bill_id IS NULL")
    null_votes = cur.fetchone()['count']
    if null_votes > 0:
        errors.append(f"votes 테이블에 필수 필드가 NULL인 행이 {null_votes:,}건 있습니다")
    else:
        print("✅ votes: 필수 필드 모두 존재")
    
    # 4. 중복 데이터 확인
    print("\n[4] 중복 데이터 확인")
    print("-" * 80)
    
    cur.execute("""
        SELECT bill_id, COUNT(*) as count
        FROM bills
        GROUP BY bill_id
        HAVING COUNT(*) > 1
    """)
    duplicate_bills = cur.fetchall()
    if duplicate_bills:
        errors.append(f"bills 테이블에 중복된 bill_id가 {len(duplicate_bills)}개 있습니다")
    else:
        print("✅ bills: 중복 없음")
    
    cur.execute("""
        SELECT member_id, COUNT(*) as count
        FROM assembly_members
        GROUP BY member_id
        HAVING COUNT(*) > 1
    """)
    duplicate_members = cur.fetchall()
    if duplicate_members:
        errors.append(f"assembly_members 테이블에 중복된 member_id가 {len(duplicate_members)}개 있습니다")
    else:
        print("✅ assembly_members: 중복 없음")
    
    # 5. 데이터 일관성 확인
    print("\n[5] 데이터 일관성 확인")
    print("-" * 80)
    
    # votes의 bill_id가 bills에 존재하는지 확인
    cur.execute("""
        SELECT COUNT(DISTINCT v.bill_id) as vote_bills,
               (SELECT COUNT(*) FROM bills) as total_bills
        FROM votes v
    """)
    stats = cur.fetchone()
    print(f"✅ 표결이 있는 의안: {stats['vote_bills']:,}건")
    print(f"✅ 전체 의안: {stats['total_bills']:,}건")
    
    # 6. 최종 결과
    print("\n" + "=" * 80)
    print("검증 결과 요약")
    print("=" * 80)
    
    if errors:
        print(f"\n❌ 오류: {len(errors)}개")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ 오류 없음")
    
    if warnings:
        print(f"\n⚠️ 경고: {len(warnings)}개")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("\n✅ 경고 없음")
    
    if not errors and not warnings:
        print("\n✅ 모든 데이터 검증 통과!")
    
    cur.close()
    conn.close()
    
    return len(errors) == 0

if __name__ == '__main__':
    validate_data()


