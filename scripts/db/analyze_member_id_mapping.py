#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
member_id_mapping 테이블 분석
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
print("member_id_mapping 테이블 분석")
print("=" * 80)

# 1. 기본 통계
print("\n[1] 기본 통계")
print("-" * 80)
cur.execute("SELECT COUNT(*) as total, COUNT(DISTINCT naas_cd) as unique_naas, COUNT(DISTINCT member_no) as unique_member_no, COUNT(DISTINCT mona_cd) as unique_mona FROM member_id_mapping")
stats = cur.fetchone()
print(f"총 레코드: {stats['total']:,}건")
print(f"고유 NAAS_CD: {stats['unique_naas']:,}개")
print(f"고유 MEMBER_NO: {stats['unique_member_no']:,}개")
print(f"고유 MONA_CD: {stats['unique_mona']:,}개")

# 2. 검증 상태
print("\n[2] 검증 상태")
print("-" * 80)
cur.execute("SELECT is_verified, COUNT(*) as count FROM member_id_mapping GROUP BY is_verified")
verified_stats = cur.fetchall()
for row in verified_stats:
    print(f"검증 {'완료' if row['is_verified'] else '미완료'}: {row['count']:,}건")

# 3. 샘플 데이터
print("\n[3] 샘플 데이터 (상위 10개)")
print("-" * 80)
cur.execute("""
    SELECT naas_cd, member_no, mona_cd, member_name, is_verified
    FROM member_id_mapping
    ORDER BY created_at DESC
    LIMIT 10
""")
samples = cur.fetchall()
for i, row in enumerate(samples, 1):
    print(f"\n{i}. NAAS_CD: {row['naas_cd']}")
    print(f"   MEMBER_NO: {row['member_no'] or '(NULL)'}")
    print(f"   MONA_CD: {row['mona_cd'] or '(NULL)'}")
    print(f"   의원명: {row['member_name'] or '(NULL)'}")
    print(f"   검증: {'완료' if row['is_verified'] else '미완료'}")

# 4. assembly_members와의 관계 확인
print("\n[4] assembly_members 테이블과의 관계")
print("-" * 80)
cur.execute("""
    SELECT 
        COUNT(DISTINCT m.naas_cd) as mapping_naas,
        COUNT(DISTINCT am.member_id) as members_total,
        COUNT(DISTINCT CASE WHEN am.member_id = m.naas_cd THEN am.member_id END) as matched
    FROM member_id_mapping m
    LEFT JOIN assembly_members am ON am.member_id = m.naas_cd
""")
relation = cur.fetchone()
print(f"member_id_mapping의 NAAS_CD: {relation['mapping_naas']:,}개")
print(f"assembly_members의 member_id: {relation['members_total']:,}개")
print(f"매칭된 개수: {relation['matched']:,}개")

# 5. votes 테이블과의 관계 확인
print("\n[5] votes 테이블과의 관계")
print("-" * 80)
# votes 테이블에서 member_no나 mona_cd를 사용하는지 확인
cur.execute("""
    SELECT 
        COUNT(*) as total_votes,
        COUNT(DISTINCT member_no) as unique_member_no,
        COUNT(DISTINCT mona_cd) as unique_mona_cd,
        COUNT(DISTINCT member_id) as unique_member_id
    FROM votes
""")
votes_stats = cur.fetchone()
print(f"votes 테이블:")
print(f"  총 표결: {votes_stats['total_votes']:,}건")
print(f"  고유 MEMBER_NO: {votes_stats['unique_member_no']:,}개")
print(f"  고유 MONA_CD: {votes_stats['unique_mona_cd']:,}개")
print(f"  고유 member_id (매핑된): {votes_stats['unique_member_id']:,}개")

# member_id_mapping을 통해 매핑이 가능한지 확인
cur.execute("""
    SELECT 
        COUNT(DISTINCT v.member_no) as votes_member_no,
        COUNT(DISTINCT m.member_no) as mapping_member_no,
        COUNT(DISTINCT CASE WHEN v.member_no = m.member_no THEN v.member_no END) as matched_member_no
    FROM votes v
    LEFT JOIN member_id_mapping m ON v.member_no = m.member_no
    WHERE v.member_no IS NOT NULL
""")
mapping_check = cur.fetchone()
print(f"\nMEMBER_NO 매핑 가능성:")
print(f"  votes의 고유 MEMBER_NO: {mapping_check['votes_member_no']:,}개")
print(f"  mapping의 고유 MEMBER_NO: {mapping_check['mapping_member_no']:,}개")
print(f"  매칭 가능: {mapping_check['matched_member_no']:,}개")

# 6. 실제 사용 여부 확인
print("\n[6] 실제 사용 여부 확인")
print("-" * 80)
# votes 테이블의 member_id가 이미 매핑되어 있는지 확인
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(member_id) as has_member_id,
        COUNT(CASE WHEN member_id IS NOT NULL THEN 1 END) as mapped_count
    FROM votes
""")
usage = cur.fetchone()
print(f"votes 테이블:")
print(f"  총 표결: {usage['total']:,}건")
print(f"  member_id가 있는 표결: {usage['mapped_count']:,}건 ({usage['mapped_count']/usage['total']*100:.1f}%)")
print(f"\n결론: votes 테이블의 member_id가 이미 매핑되어 있으므로,")
print(f"      member_id_mapping 테이블은 현재 사용되지 않는 것으로 보입니다.")

cur.close()
conn.close()


