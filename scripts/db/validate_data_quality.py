#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
데이터 품질 검증 스크립트
"""

import sys
import psycopg2

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
from dotenv import load_dotenv

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

config = get_db_config()
conn = psycopg2.connect(**config)
cur = conn.cursor()

print("=" * 60)
print("데이터 품질 검증")
print("=" * 60)

# 1. bills 검증
print("\n1. bills 테이블 검증:")
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(bill_id) as has_bill_id,
        COUNT(title) as has_title,
        COUNT(summary) as has_summary,
        COUNT(categories) as has_categories
    FROM bills
""")
bills_stats = cur.fetchone()
print(f"  총 의안: {bills_stats[0]}건")
print(f"  bill_id 있음: {bills_stats[1]}건")
print(f"  title 있음: {bills_stats[2]}건")
print(f"  summary 있음: {bills_stats[3]}건 (AI 처리)")
print(f"  categories 있음: {bills_stats[4]}건 (AI 처리)")

# 2. assembly_members 검증
print("\n2. assembly_members 테이블 검증:")
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(member_id) as has_member_id,
        COUNT(name) as has_name,
        COUNT(party) as has_party,
        COUNT(DISTINCT name) as unique_names
    FROM assembly_members
""")
members_stats = cur.fetchone()
print(f"  총 의원: {members_stats[0]}명")
print(f"  member_id 있음: {members_stats[1]}명")
print(f"  name 있음: {members_stats[2]}명")
print(f"  party 있음: {members_stats[3]}명")
print(f"  고유 이름: {members_stats[4]}명")

# 22대 의원 수
cur.execute("""
    SELECT COUNT(*) 
    FROM assembly_members
    WHERE era LIKE '%%22대%%' OR era LIKE '%%제22대%%'
""")
era_22_count = cur.fetchone()[0]
print(f"  22대 포함 의원: {era_22_count}명")

# 3. votes 검증
print("\n3. votes 테이블 검증:")
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(bill_id) as has_bill_id,
        COUNT(member_id) as has_member_id,
        COUNT(member_name) as has_member_name,
        COUNT(party_name) as has_party_name,
        COUNT(vote_result) as has_vote_result
    FROM votes
""")
votes_stats = cur.fetchone()
print(f"  총 표결: {votes_stats[0]}건")
print(f"  bill_id 있음: {votes_stats[1]}건")
print(f"  member_id 있음: {votes_stats[2]}건 ({votes_stats[2]*100/votes_stats[0]:.1f}%)")
print(f"  member_name 있음: {votes_stats[3]}건")
print(f"  party_name 있음: {votes_stats[4]}건")
print(f"  vote_result 있음: {votes_stats[5]}건")

# 4. 외래키 무결성 검증
print("\n4. 외래키 무결성 검증:")

# bills와 votes 연결
cur.execute("""
    SELECT COUNT(*) 
    FROM votes v
    LEFT JOIN bills b ON v.bill_id = b.bill_id
    WHERE b.bill_id IS NULL
""")
orphan_votes = cur.fetchone()[0]
print(f"  orphan votes (bills 없음): {orphan_votes}건")

# votes와 assembly_members 연결
cur.execute("""
    SELECT COUNT(*) 
    FROM votes v
    WHERE v.member_id IS NOT NULL
    AND NOT EXISTS (
        SELECT 1 FROM assembly_members a 
        WHERE a.member_id = v.member_id
    )
""")
invalid_member_ids = cur.fetchone()[0]
print(f"  invalid member_id: {invalid_member_ids}건")

# 5. 중복 데이터 검증
print("\n5. 중복 데이터 검증:")

# bills 중복
cur.execute("""
    SELECT bill_id, COUNT(*) as cnt
    FROM bills
    GROUP BY bill_id
    HAVING COUNT(*) > 1
""")
duplicate_bills = cur.fetchall()
print(f"  중복 bills: {len(duplicate_bills)}건")

# votes 중복 (unique constraint 위반)
cur.execute("""
    SELECT bill_id, member_no, vote_date, COUNT(*) as cnt
    FROM votes
    GROUP BY bill_id, member_no, vote_date
    HAVING COUNT(*) > 1
""")
duplicate_votes = cur.fetchall()
print(f"  중복 votes: {len(duplicate_votes)}건")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("데이터 품질 검증 완료!")
print("=" * 60)

