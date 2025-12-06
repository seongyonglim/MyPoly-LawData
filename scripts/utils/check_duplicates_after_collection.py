#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
수집 후 중복 데이터 확인
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
try:
    from dotenv import load_dotenv
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
    load_dotenv(override=True)
except ImportError:
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_file):
        encodings = ['utf-8', 'utf-8-sig', 'cp949', 'latin-1']
        for encoding in encodings:
            try:
                with open(env_file, 'r', encoding=encoding) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key and value:
                                os.environ[key] = value
                break
            except:
                continue

conn = psycopg2.connect(
    host=os.environ.get('LOCAL_DB_HOST', 'localhost'),
    database=os.environ.get('LOCAL_DB_NAME', 'mypoly_lawdata'),
    user=os.environ.get('LOCAL_DB_USER', 'postgres'),
    password=os.environ.get('LOCAL_DB_PASSWORD') or os.environ.get('DB_PASSWORD'),
    port=int(os.environ.get('LOCAL_DB_PORT', '5432'))
)
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("수집 후 중복 데이터 확인")
print("=" * 80)

# 의안 데이터 중복 확인
print("\n[1] 의안 데이터 중복 확인")
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT bill_id) as distinct_bills
    FROM bills
    WHERE proposal_date >= '2025-01-01'
""")
bill_stats = cur.fetchone()
duplicate_bills = bill_stats['total'] - bill_stats['distinct_bills']
print(f"  총 의안 레코드: {bill_stats['total']:,}건")
print(f"  고유 의안: {bill_stats['distinct_bills']:,}건")
if duplicate_bills > 0:
    print(f"  ⚠️ 중복 의안: {duplicate_bills:,}건")
else:
    print(f"  ✅ 중복 없음")

# 표결 데이터 중복 확인
print("\n[2] 표결 데이터 중복 확인")
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT (bill_id, member_no, vote_date, vote_result)) as distinct_votes
    FROM votes
    WHERE bill_id IN (SELECT bill_id FROM bills WHERE proposal_date >= '2025-01-01')
""")
vote_stats = cur.fetchone()
duplicate_votes = vote_stats['total'] - vote_stats['distinct_votes']
print(f"  총 표결 레코드: {vote_stats['total']:,}건")
print(f"  고유 표결: {vote_stats['distinct_votes']:,}건")
if duplicate_votes > 0:
    print(f"  ⚠️ 중복 표결: {duplicate_votes:,}건")
    print("\n  중복 상세 (상위 10개):")
    cur.execute("""
        SELECT 
            bill_id, member_no, vote_date, vote_result,
            COUNT(*) as cnt
        FROM votes
        WHERE bill_id IN (SELECT bill_id FROM bills WHERE proposal_date >= '2025-01-01')
        GROUP BY bill_id, member_no, vote_date, vote_result
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        LIMIT 10
    """)
    for dup in cur.fetchall():
        print(f"    bill_id: {dup['bill_id'][:30]}..., member_no: {dup['member_no']}, 중복: {dup['cnt']}회")
else:
    print(f"  ✅ 중복 없음")

# 최신 데이터 확인
print("\n[3] 최신 데이터 확인")
cur.execute("""
    SELECT 
        MAX(proposal_date) as latest_bill_date,
        COUNT(*) FILTER (WHERE proposal_date >= CURRENT_DATE - INTERVAL '7 days') as recent_bills
    FROM bills
    WHERE proposal_date >= '2025-01-01'
""")
latest = cur.fetchone()
print(f"  최신 의안 제안일: {latest['latest_bill_date']}")
print(f"  최근 7일 의안: {latest['recent_bills']:,}건")

cur.execute("""
    SELECT 
        MAX(vote_date) as latest_vote_date,
        COUNT(*) FILTER (WHERE vote_date >= CURRENT_DATE - INTERVAL '7 days') as recent_votes
    FROM votes
    WHERE bill_id IN (SELECT bill_id FROM bills WHERE proposal_date >= '2025-01-01')
      AND vote_date IS NOT NULL
""")
latest_vote = cur.fetchone()
if latest_vote['latest_vote_date']:
    print(f"  최신 표결일: {latest_vote['latest_vote_date']}")
    print(f"  최근 7일 표결: {latest_vote['recent_votes']:,}건")

cur.close()
conn.close()

print("\n" + "=" * 80)
if duplicate_bills == 0 and duplicate_votes == 0:
    print("✅ 중복 데이터 없음 - 모든 데이터가 정상입니다!")
else:
    print("⚠️ 중복 데이터가 발견되었습니다. 확인이 필요합니다.")
print("=" * 80)

