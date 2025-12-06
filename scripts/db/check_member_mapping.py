#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
의원 매핑 상태 확인 스크립트
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == 'win32':
    import io as win_io
    sys.stdout = win_io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = win_io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def get_db_config():
    """데이터베이스 설정 가져오기"""
    if 'DATABASE_URL' in os.environ:
        from urllib.parse import urlparse
        db_url = urlparse(os.environ['DATABASE_URL'])
        return {
            'host': db_url.hostname,
            'database': db_url.path[1:],
            'user': db_url.username,
            'password': db_url.password,
            'port': db_url.port or 5432
        }
    elif 'DB_HOST' in os.environ:
        host = os.environ.get('DB_HOST', '')
        if not host.endswith('.render.com') and not '.' in host:
            host = f"{host}.oregon-postgres.render.com"
        return {
            'host': host,
            'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': os.environ.get('DB_PASSWORD'),
            'port': int(os.environ.get('DB_PORT', 5432))
        }
    else:
        password = os.environ.get('DB_PASSWORD')
        if not password:
            raise ValueError("DB_PASSWORD environment variable is required")
        return {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': password,
            'port': int(os.environ.get('DB_PORT', '5432'))
        }

def check_member_mapping():
    """의원 매핑 상태 확인"""
    config = get_db_config()
    conn = psycopg2.connect(**config)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 60)
    print("의원 매핑 상태 확인")
    print("=" * 60)
    
    # 1. votes 테이블의 member_id NULL 개수
    cur.execute("""
        SELECT 
            COUNT(*) as total_votes,
            COUNT(member_id) as votes_with_member_id,
            COUNT(*) - COUNT(member_id) as votes_without_member_id,
            COUNT(DISTINCT member_no) as unique_member_no,
            COUNT(DISTINCT member_id) as unique_member_id
        FROM votes
    """)
    vote_stats = cur.fetchone()
    print("\n[1] votes 테이블 상태:")
    print(f"  전체 표결: {vote_stats['total_votes']:,}건")
    print(f"  member_id 있음: {vote_stats['votes_with_member_id']:,}건")
    print(f"  member_id NULL: {vote_stats['votes_without_member_id']:,}건")
    print(f"  고유 member_no: {vote_stats['unique_member_no']:,}개")
    print(f"  고유 member_id: {vote_stats['unique_member_id']:,}개")
    
    # 2. member_id_mapping 테이블 상태
    cur.execute("SELECT COUNT(*) as count FROM member_id_mapping")
    mapping_count = cur.fetchone()['count']
    print(f"\n[2] member_id_mapping 테이블:")
    print(f"  매핑 데이터: {mapping_count:,}건")
    
    # 3. assembly_members 테이블 상태
    cur.execute("SELECT COUNT(*) as count FROM assembly_members")
    member_count = cur.fetchone()['count']
    print(f"\n[3] assembly_members 테이블:")
    print(f"  의원 데이터: {member_count:,}건")
    
    # 4. member_id가 assembly_members에 없는 votes 개수
    cur.execute("""
        SELECT COUNT(*) as count
        FROM votes v
        LEFT JOIN assembly_members am ON v.member_id = am.member_id
        WHERE v.member_id IS NOT NULL
        AND am.member_id IS NULL
    """)
    unmapped = cur.fetchone()['count']
    print(f"\n[4] 매핑되지 않은 표결:")
    print(f"  member_id가 있지만 assembly_members에 없는 표결: {unmapped:,}건")
    
    # 5. 정상 매핑된 표결 개수
    cur.execute("""
        SELECT COUNT(*) as count
        FROM votes v
        INNER JOIN assembly_members am ON v.member_id = am.member_id
    """)
    mapped = cur.fetchone()['count']
    print(f"  정상 매핑된 표결: {mapped:,}건")
    
    # 6. 샘플 데이터 확인
    print("\n[5] 샘플 데이터:")
    cur.execute("""
        SELECT v.member_no, v.member_id, am.name, am.party
        FROM votes v
        LEFT JOIN assembly_members am ON v.member_id = am.member_id
        WHERE v.member_id IS NOT NULL
        LIMIT 5
    """)
    samples = cur.fetchall()
    for s in samples:
        print(f"  member_no={s['member_no']}, member_id={s['member_id']}, "
              f"mapped_id={s['mapped_id']}, name={s['name']}")
    
    cur.close()
    conn.close()
    
    return {
        'unmapped': unmapped,
        'mappable': mappable,
        'total_votes': vote_stats['total_votes']
    }

if __name__ == '__main__':
    check_member_mapping()

