#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
로컬 DB 데이터를 Render DB로 이전하는 스크립트
pg_dump + psql 방식 또는 Python 직접 복사 방식
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def get_local_db_config():
    """로컬 DB 설정"""
    return {
        'host': 'localhost',
        'database': 'mypoly_lawdata',
        'user': 'postgres',
        'password': 'maza_970816',
        'port': 5432
    }

def get_render_db_config():
    """Render DB 설정 (환경 변수에서)"""
    if 'DB_HOST' in os.environ:
        return {
            'host': os.environ.get('DB_HOST'),
            'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': os.environ.get('DB_PASSWORD'),
            'port': int(os.environ.get('DB_PORT', 5432))
        }
    else:
        print("⚠️ Render DB 환경 변수가 설정되지 않았습니다.")
        print("다음 환경 변수를 설정하세요:")
        print("  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        return None

def check_local_data():
    """로컬 DB 데이터 확인"""
    try:
        config = get_local_db_config()
        conn = psycopg2.connect(**config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=" * 60)
        print("로컬 DB 데이터 확인")
        print("=" * 60)
        
        # 각 테이블 데이터 개수 확인
        tables = ['bills', 'assembly_members', 'votes']
        counts = {}
        
        for table in tables:
            cur.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cur.fetchone()['count']
            counts[table] = count
            print(f"  {table}: {count:,}건")
        
        cur.close()
        conn.close()
        
        total = sum(counts.values())
        print(f"\n총 데이터: {total:,}건")
        print("=" * 60)
        
        return counts
        
    except Exception as e:
        print(f"❌ 로컬 DB 연결 오류: {e}")
        return None

def transfer_table_data(table_name, local_conn, render_conn, batch_size=1000):
    """테이블 데이터 이전"""
    local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
    render_cur = render_conn.cursor()
    
    try:
        # 로컬에서 데이터 개수 확인
        local_cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        total_count = local_cur.fetchone()['count']
        
        if total_count == 0:
            print(f"  {table_name}: 데이터 없음 (건너뜀)")
            return 0
        
        print(f"  {table_name}: {total_count:,}건 이전 중...")
        
        # 컬럼 정보 가져오기
        local_cur.execute(f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        columns = [row['column_name'] for row in local_cur.fetchall()]
        
        # Render에서 기존 데이터 개수 확인
        render_cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        existing_count = render_cur.fetchone()[0]
        
        if existing_count > 0:
            print(f"    ⚠️ Render DB에 이미 {existing_count:,}건의 데이터가 있습니다.")
            response = input("    계속 진행하시겠습니까? (y/n): ")
            if response.lower() != 'y':
                print("    건너뜀")
                return 0
        
        # 배치로 데이터 읽기 및 삽입
        offset = 0
        inserted = 0
        updated = 0
        
        while offset < total_count:
            # 로컬에서 배치 읽기
            local_cur.execute(f"""
                SELECT * FROM {table_name}
                ORDER BY {columns[0]}
                LIMIT %s OFFSET %s
            """, (batch_size, offset))
            
            rows = local_cur.fetchall()
            if not rows:
                break
            
            # Render에 삽입
            for row in rows:
                row_dict = dict(row)
                values = [row_dict.get(col) for col in columns]
                placeholders = ', '.join(['%s'] * len(columns))
                col_names = ', '.join(columns)
                
                # ON CONFLICT 처리 (PK가 있는 경우)
                if table_name == 'bills':
                    conflict_clause = f"""
                        ON CONFLICT (bill_id) 
                        DO UPDATE SET
                            bill_no = EXCLUDED.bill_no,
                            title = EXCLUDED.title,
                            proposal_date = EXCLUDED.proposal_date,
                            proposer_kind = EXCLUDED.proposer_kind,
                            proc_stage_cd = EXCLUDED.proc_stage_cd,
                            pass_gubn = EXCLUDED.pass_gubn,
                            proc_date = EXCLUDED.proc_date,
                            general_result = EXCLUDED.general_result,
                            summary_raw = EXCLUDED.summary_raw,
                            link_url = EXCLUDED.link_url,
                            updated_at = CURRENT_TIMESTAMP
                    """
                elif table_name == 'assembly_members':
                    conflict_clause = f"""
                        ON CONFLICT (member_id) 
                        DO UPDATE SET
                            name = EXCLUDED.name,
                            party = EXCLUDED.party,
                            district = EXCLUDED.district,
                            updated_at = CURRENT_TIMESTAMP
                    """
                elif table_name == 'votes':
                    conflict_clause = f"""
                        ON CONFLICT (bill_id, member_no, vote_date) 
                        DO UPDATE SET
                            vote_result = EXCLUDED.vote_result,
                            member_name = EXCLUDED.member_name,
                            party_name = EXCLUDED.party_name,
                            district_name = EXCLUDED.district_name
                    """
                else:
                    conflict_clause = ""
                
                try:
                    query = f"""
                        INSERT INTO {table_name} ({col_names})
                        VALUES ({placeholders})
                        {conflict_clause}
                    """
                    render_cur.execute(query, values)
                    
                    if "INSERT" in str(render_cur.statusmessage):
                        inserted += 1
                    else:
                        updated += 1
                        
                except Exception as e:
                    print(f"    ⚠️ 행 삽입 오류: {str(e)[:100]}")
                    continue
            
            render_conn.commit()
            offset += batch_size
            
            if offset % (batch_size * 10) == 0:
                print(f"    진행 중... {offset:,}/{total_count:,} ({inserted:,} 삽입, {updated:,} 업데이트)")
        
        print(f"    ✅ 완료: {inserted:,}건 삽입, {updated:,}건 업데이트")
        return inserted + updated
        
    except Exception as e:
        print(f"    ❌ 오류: {e}")
        render_conn.rollback()
        import traceback
        traceback.print_exc()
        return 0
    finally:
        local_cur.close()
        render_cur.close()

def transfer_all_data():
    """모든 데이터 이전"""
    # 로컬 DB 데이터 확인
    local_counts = check_local_data()
    if not local_counts:
        return
    
    total_local = sum(local_counts.values())
    if total_local == 0:
        print("\n⚠️ 로컬 DB에 데이터가 없습니다.")
        return
    
    # Render DB 설정 확인
    render_config = get_render_db_config()
    if not render_config:
        return
    
    print("\n" + "=" * 60)
    print("Render DB 연결 테스트")
    print("=" * 60)
    
    try:
        render_conn = psycopg2.connect(**render_config)
        print("✅ Render DB 연결 성공")
        render_conn.close()
    except Exception as e:
        print(f"❌ Render DB 연결 실패: {e}")
        print("\n환경 변수를 확인하세요:")
        print("  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        return
    
    # 사용자 확인
    print("\n" + "=" * 60)
    print("데이터 이전 시작")
    print("=" * 60)
    print(f"로컬 → Render DB")
    print(f"  bills: {local_counts.get('bills', 0):,}건")
    print(f"  assembly_members: {local_counts.get('assembly_members', 0):,}건")
    print(f"  votes: {local_counts.get('votes', 0):,}건")
    print("\n계속하시겠습니까? (y/n): ", end='')
    response = input()
    
    if response.lower() != 'y':
        print("취소되었습니다.")
        return
    
    # 연결
    local_config = get_local_db_config()
    local_conn = psycopg2.connect(**local_config)
    render_conn = psycopg2.connect(**render_config)
    
    try:
        print("\n" + "=" * 60)
        print("데이터 이전 진행 중...")
        print("=" * 60)
        
        # 각 테이블 이전
        tables = ['bills', 'assembly_members', 'votes']
        total_transferred = 0
        
        for table in tables:
            if local_counts.get(table, 0) > 0:
                count = transfer_table_data(table, local_conn, render_conn)
                total_transferred += count
                print()
        
        print("=" * 60)
        print(f"✅ 데이터 이전 완료!")
        print(f"  총 {total_transferred:,}건 이전됨")
        print("=" * 60)
        
    finally:
        local_conn.close()
        render_conn.close()

if __name__ == '__main__':
    transfer_all_data()

