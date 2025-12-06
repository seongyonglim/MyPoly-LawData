#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
한글 번역이 없는 컬럼의 실제 데이터 확인
"""

import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host='localhost',
    database='mypoly_lawdata',
    user='postgres',
    password=os.environ.get('DB_PASSWORD'),
    port=5432
)

cur = conn.cursor(cursor_factory=RealDictCursor)

# app.py의 get_column_korean_name 함수에서 정의된 컬럼들
defined_columns = {
    'bills': ['bill_id', 'bill_no', 'title', 'proposal_date', 'proposer_kind', 'proposer_name', 
              'proc_stage_cd', 'pass_gubn', 'proc_date', 'general_result', 'summary_raw', 
              'summary', 'categories', 'vote_for', 'vote_against', 'proc_stage_order', 
              'proposer_count', 'link_url', 'created_at', 'updated_at'],
    'assembly_members': ['member_id', 'name', 'name_chinese', 'name_english', 'party', 'district', 
                         'district_type', 'committee', 'current_committee', 'era', 'election_type', 
                         'gender', 'birth_date', 'birth_type', 'duty_name', 'phone', 'email', 
                         'homepage_url', 'office_room', 'aide_name', 'secretary_name', 
                         'assistant_name', 'photo_url', 'brief_history', 'mona_cd', 'member_no', 
                         'created_at', 'updated_at'],
    'votes': ['vote_id', 'bill_id', 'bill_no', 'bill_name', 'member_no', 'mona_cd', 'member_id', 
              'member_name', 'member_name_chinese', 'party_name', 'party_code', 'district_name', 
              'district_code', 'vote_result', 'vote_date', 'era', 'session_code', 
              'current_committee', 'current_committee_id', 'created_at', 'updated_at'],
    'user_votes': ['user_vote_id', 'bill_id', 'user_id', 'vote_result', 'vote_date'],
    'user_political_profile': ['user_id', 'p_score', 'm_score', 'u_score', 't_score', 'n_score', 
                               's_score', 'o_score', 'r_score', 'test_completed', 'created_at', 'updated_at'],
    'member_political_profile': ['member_id', 'p_score', 'm_score', 'u_score', 't_score', 'n_score', 
                                's_score', 'o_score', 'r_score', 'total_votes', 'last_calculated_at', 
                                'created_at', 'updated_at'],
    'proc_stage_mapping': ['stage_code', 'stage_name', 'stage_order', 'description'],
    'member_id_mapping': ['mapping_id', 'naas_cd', 'member_no', 'mona_cd', 'member_name', 
                          'is_verified', 'created_at', 'updated_at'],
    'bill_similarity': ['bill_id_1', 'bill_id_2', 'similarity_score', 'similarity_method', 'created_at'],
}

print("=" * 80)
print("한글 번역이 없는 컬럼 확인")
print("=" * 80)

# 모든 테이블 조회
cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")

all_tables = [row['table_name'] for row in cur.fetchall()]

for table_name in all_tables:
    # 실제 컬럼 조회
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    
    actual_columns = [row['column_name'] for row in cur.fetchall()]
    defined_cols = defined_columns.get(table_name, [])
    
    missing_cols = [col for col in actual_columns if col not in defined_cols]
    
    if missing_cols:
        print(f"\n[{table_name}] 한글 번역이 없는 컬럼:")
        for col in missing_cols:
            # 실제 데이터 샘플 확인
            try:
                cur.execute(f"SELECT {col} FROM {table_name} WHERE {col} IS NOT NULL LIMIT 5")
                samples = cur.fetchall()
                sample_values = [str(row[col])[:50] for row in samples if row[col] is not None]
                
                # 데이터 타입 확인
                cur.execute("""
                    SELECT data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    AND column_name = %s
                """, (table_name, col))
                col_info = cur.fetchone()
                
                print(f"  - {col} ({col_info['data_type']}, NULL: {col_info['is_nullable']})")
                if sample_values:
                    print(f"    샘플 값: {', '.join(sample_values[:3])}")
                else:
                    print(f"    샘플 값: (모두 NULL)")
            except Exception as e:
                print(f"  - {col} (확인 불가: {e})")

cur.close()
conn.close()


