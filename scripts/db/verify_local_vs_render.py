#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
로컬 DB와 Render DB 비교 검증 스크립트
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == 'win32':
    import io as win_io
    sys.stdout = win_io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = win_io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def get_local_db_config():
    return {
        'host': 'localhost',
        'database': 'mypoly_lawdata',
        'user': 'postgres',
        'password': 'maza_970816',
        'port': 5432
    }

def get_render_db_config():
    host = os.environ.get('DB_HOST', 'dpg-d4jhgdfgi27c739n9m20-a')
    if not host.endswith('.render.com') and not '.' in host:
        host = f"{host}.oregon-postgres.render.com"
    
    return {
        'host': host,
        'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
        'user': os.environ.get('DB_USER', 'mypoly_user'),
        'password': os.environ.get('DB_PASSWORD', 'vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE'),
        'port': int(os.environ.get('DB_PORT', 5432))
    }

def get_table_structure(conn, table_name):
    """테이블 구조 가져오기"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    return cur.fetchall()

def get_table_count(conn, table_name):
    """테이블 데이터 개수"""
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cur.fetchone()[0]

def compare_table_structures(local_conn, render_conn, table_name):
    """테이블 구조 비교"""
    local_cols = {col['column_name']: col for col in get_table_structure(local_conn, table_name)}
    render_cols = {col['column_name']: col for col in get_table_structure(render_conn, table_name)}
    
    local_only = set(local_cols.keys()) - set(render_cols.keys())
    render_only = set(render_cols.keys()) - set(local_cols.keys())
    common = set(local_cols.keys()) & set(render_cols.keys())
    
    differences = []
    for col_name in common:
        local_col = local_cols[col_name]
        render_col = render_cols[col_name]
        if (local_col['data_type'] != render_col['data_type'] or 
            local_col['is_nullable'] != render_col['is_nullable']):
            differences.append({
                'column': col_name,
                'local': local_col,
                'render': render_col
            })
    
    return {
        'local_only': local_only,
        'render_only': render_only,
        'differences': differences,
        'match': len(local_only) == 0 and len(render_only) == 0 and len(differences) == 0
    }

def verify_data():
    """로컬과 Render DB 검증"""
    print("=" * 80)
    print("로컬 DB vs Render DB 검증")
    print("=" * 80)
    
    # 연결
    try:
        local_config = get_local_db_config()
        local_conn = psycopg2.connect(**local_config)
        print("✅ 로컬 DB 연결 성공")
    except Exception as e:
        print(f"❌ 로컬 DB 연결 실패: {e}")
        return
    
    try:
        render_config = get_render_db_config()
        render_conn = psycopg2.connect(**render_config)
        print("✅ Render DB 연결 성공\n")
    except Exception as e:
        print(f"❌ Render DB 연결 실패: {e}")
        print("\n환경 변수를 설정하세요:")
        print("  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        local_conn.close()
        return
    
    # 주요 테이블 목록
    tables = ['bills', 'assembly_members', 'votes', 'member_id_mapping']
    
    print("=" * 80)
    print("1. 테이블 구조 비교")
    print("=" * 80)
    
    structure_issues = []
    for table in tables:
        print(f"\n[{table}]")
        result = compare_table_structures(local_conn, render_conn, table)
        
        if result['match']:
            print("  ✅ 구조 일치")
        else:
            structure_issues.append((table, result))
            if result['local_only']:
                print(f"  ⚠️ 로컬에만 있는 컬럼: {', '.join(result['local_only'])}")
            if result['render_only']:
                print(f"  ⚠️ Render에만 있는 컬럼: {', '.join(result['render_only'])}")
            if result['differences']:
                print(f"  ⚠️ 타입/제약조건 차이:")
                for diff in result['differences']:
                    print(f"    - {diff['column']}:")
                    print(f"      로컬: {diff['local']['data_type']} (NULL: {diff['local']['is_nullable']})")
                    print(f"      Render: {diff['render']['data_type']} (NULL: {diff['render']['is_nullable']})")
    
    print("\n" + "=" * 80)
    print("2. 데이터 개수 비교")
    print("=" * 80)
    
    data_issues = []
    for table in tables:
        local_count = get_table_count(local_conn, table)
        render_count = get_table_count(render_conn, table)
        
        print(f"\n[{table}]")
        print(f"  로컬: {local_count:,}건")
        print(f"  Render: {render_count:,}건")
        
        if local_count == 0:
            print("  ⚠️ 로컬 DB에 데이터가 없습니다!")
        elif render_count == 0:
            print("  ⚠️ Render DB에 데이터가 없습니다!")
            data_issues.append(table)
        elif abs(local_count - render_count) > 10:  # 10건 이상 차이
            diff = abs(local_count - render_count)
            percent = (diff / local_count * 100) if local_count > 0 else 0
            print(f"  ⚠️ 차이: {diff:,}건 ({percent:.1f}%)")
            if percent > 5:  # 5% 이상 차이
                data_issues.append(table)
        else:
            print("  ✅ 데이터 개수 일치")
    
    print("\n" + "=" * 80)
    print("3. 주요 데이터 샘플 비교")
    print("=" * 80)
    
    # bills 테이블 샘플
    print("\n[bills 샘플]")
    local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
    render_cur = render_conn.cursor(cursor_factory=RealDictCursor)
    
    local_cur.execute("""
        SELECT bill_id, title, proposer_kind, proposer_name, proposal_date
        FROM bills
        WHERE proposal_date >= '2025-01-01'
        ORDER BY proposal_date DESC
        LIMIT 3
    """)
    local_samples = local_cur.fetchall()
    
    # proposer_name 컬럼 존재 여부 확인
    render_cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'bills' AND column_name = 'proposer_name'
    """)
    has_proposer_name = render_cur.fetchone() is not None
    
    proposer_select = ", proposer_name" if has_proposer_name else ""
    
    render_cur.execute(f"""
        SELECT bill_id, title, proposer_kind{proposer_select}, proposal_date
        FROM bills
        WHERE proposal_date >= '2025-01-01'
        ORDER BY proposal_date DESC
        LIMIT 3
    """)
    render_samples = render_cur.fetchall()
    
    print("  로컬 샘플:")
    for s in local_samples:
        proposer_info = s.get('proposer_name', 'NULL')
        print(f"    - {s['bill_id'][:20]}... | {s['title'][:30]}... | proposer_name={proposer_info}")
    
    print("  Render 샘플:")
    for s in render_samples:
        proposer_info = s.get('proposer_name', 'NULL (컬럼 없음)' if not has_proposer_name else 'NULL')
        print(f"    - {s['bill_id'][:20]}... | {s['title'][:30]}... | proposer_name={proposer_info}")
    
    # votes 테이블 member_id 매핑 확인
    print("\n[votes member_id 매핑 확인]")
    local_cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(member_id) as with_member_id,
            COUNT(*) - COUNT(member_id) as without_member_id
        FROM votes
    """)
    local_vote_stats = local_cur.fetchone()
    
    render_cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(member_id) as with_member_id,
            COUNT(*) - COUNT(member_id) as without_member_id
        FROM votes
    """)
    render_vote_stats = render_cur.fetchone()
    
    print("  로컬:")
    print(f"    전체: {local_vote_stats['total']:,}건")
    print(f"    member_id 있음: {local_vote_stats['with_member_id']:,}건")
    print(f"    member_id NULL: {local_vote_stats['without_member_id']:,}건")
    
    print("  Render:")
    print(f"    전체: {render_vote_stats['total']:,}건")
    print(f"    member_id 있음: {render_vote_stats['with_member_id']:,}건")
    print(f"    member_id NULL: {render_vote_stats['without_member_id']:,}건")
    
    # 요약
    print("\n" + "=" * 80)
    print("검증 요약")
    print("=" * 80)
    
    if len(structure_issues) == 0 and len(data_issues) == 0:
        print("✅ 모든 검증 통과!")
    else:
        if len(structure_issues) > 0:
            print(f"⚠️ 구조 차이: {len(structure_issues)}개 테이블")
        if len(data_issues) > 0:
            print(f"⚠️ 데이터 문제: {len(data_issues)}개 테이블")
            print(f"   문제 테이블: {', '.join(data_issues)}")
    
    local_cur.close()
    render_cur.close()
    local_conn.close()
    render_conn.close()

if __name__ == '__main__':
    verify_data()

