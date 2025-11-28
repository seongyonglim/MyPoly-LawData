#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
사용되지 않는 테이블 분석
"""

import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host='localhost',
    database='mypoly_lawdata',
    user='postgres',
    password='maza_970816',
    port=5432
)

cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("테이블 사용 현황 분석")
print("=" * 80)

# 모든 테이블 목록
cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")

all_tables = [row['table_name'] for row in cur.fetchall()]

# 외래키 관계가 있는 테이블
cur.execute("""
    SELECT DISTINCT tc.table_name
    FROM information_schema.table_constraints AS tc
    WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
""")
tables_with_fk = [row['table_name'] for row in cur.fetchall()]

# 외래키를 참조하는 테이블 (다른 테이블에서 참조되는 테이블)
cur.execute("""
    SELECT DISTINCT ccu.table_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
""")
referenced_tables = [row['table_name'] for row in cur.fetchall()]

print("\n[1] 핵심 테이블 (외래키 관계 있음):")
core_tables = ['bills', 'assembly_members', 'votes']
for table in core_tables:
    if table in all_tables:
        cur.execute(f"SELECT COUNT(*) as count FROM {table}")
        count = cur.fetchone()['count']
        has_fk = table in tables_with_fk
        is_referenced = table in referenced_tables
        print(f"  [사용중] {table}: {count:,}건 (FK: {has_fk}, 참조됨: {is_referenced})")

print("\n[2] 사용자 관련 테이블 (추후 기능용):")
user_tables = ['user_votes', 'user_political_profile', 'member_political_profile']
for table in user_tables:
    if table in all_tables:
        cur.execute(f"SELECT COUNT(*) as count FROM {table}")
        count = cur.fetchone()['count']
        has_fk = table in tables_with_fk
        is_referenced = table in referenced_tables
        status = "[미사용]" if count == 0 else "[사용중]"
        print(f"  {status} {table}: {count:,}건 (FK: {has_fk}, 참조됨: {is_referenced})")
        if count == 0:
            print(f"    → 추후 기능: 사용자 투표/정치성향 테스트 기능")

print("\n[3] 매핑/설정 테이블:")
mapping_tables = ['proc_stage_mapping', 'member_id_mapping', 'bill_similarity']
for table in mapping_tables:
    if table in all_tables:
        cur.execute(f"SELECT COUNT(*) as count FROM {table}")
        count = cur.fetchone()['count']
        has_fk = table in tables_with_fk
        is_referenced = table in referenced_tables
        
        if table == 'proc_stage_mapping':
            print(f"  [설정] {table}: {count:,}건 (설정 테이블)")
            print(f"    → 용도: bills.proc_stage_cd 코드를 단계명으로 변환")
            print(f"    → 현재: 외래키 없음 (코드 매핑용)")
        elif table == 'member_id_mapping':
            print(f"  [매핑] {table}: {count:,}건 (매핑 테이블)")
            print(f"    → 용도: 표결정보 API의 MEMBER_NO와 의원정보 API의 NAAS_CD 매핑")
            print(f"    → 현재: votes.member_id가 이미 매핑되어 있어 사용 안 함")
        elif table == 'bill_similarity':
            print(f"  [미사용] {table}: {count:,}건 (추후 기능용)")
            print(f"    → 용도: 의안 유사도 계산 결과 저장")
            print(f"    → 현재: 미사용")

print("\n" + "=" * 80)
print("정리 권장 사항")
print("=" * 80)

print("\n[삭제 가능] 테이블:")
print("  1. user_votes - 사용자 투표 기능 미구현 (데이터 0건)")
print("  2. user_political_profile - 사용자 정치성향 테스트 미구현 (데이터 5건, 테스트용?)")
print("  3. member_political_profile - 의원 정치성향 계산 미구현 (데이터 0건)")
print("  4. bill_similarity - 의안 유사도 계산 미구현 (데이터 0건)")

print("\n[검토 필요] 테이블:")
print("  1. member_id_mapping - votes.member_id가 이미 매핑되어 있어 불필요할 수 있음")
print("     → 현재 votes 테이블의 member_id가 정상적으로 매핑되어 있으면 삭제 가능")

print("\n[유지 필요] 테이블:")
print("  1. proc_stage_mapping - 진행 단계 코드 매핑용 (설정 테이블)")
print("     → bills.proc_stage_cd를 읽기 쉬운 단계명으로 변환하는데 사용 가능")

cur.close()
conn.close()

