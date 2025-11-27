#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Render DB 문제 수정 스크립트
1. proposer_name 컬럼 추가
2. 누락된 votes 데이터 이전
3. member_id_mapping 데이터 이전
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch

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

def fix_render_db():
    """Render DB 문제 수정"""
    print("=" * 80)
    print("Render DB 문제 수정")
    print("=" * 80)
    
    # 연결
    local_config = get_local_db_config()
    render_config = get_render_db_config()
    
    local_conn = psycopg2.connect(**local_config)
    render_conn = psycopg2.connect(**render_config)
    
    local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
    render_cur = render_conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. proposer_name 컬럼 추가
        print("\n[1] proposer_name 컬럼 추가 중...")
        try:
            render_cur.execute("""
                ALTER TABLE bills 
                ADD COLUMN IF NOT EXISTS proposer_name VARCHAR(100)
            """)
            render_conn.commit()
            print("  ✅ proposer_name 컬럼 추가 완료")
        except Exception as e:
            print(f"  ⚠️ proposer_name 컬럼 추가 오류 (이미 존재할 수 있음): {e}")
            render_conn.rollback()
        
        # 2. proposer_name 데이터 업데이트 (로컬에서 Render로)
        print("\n[2] proposer_name 데이터 업데이트 중...")
        local_cur.execute("""
            SELECT bill_id, proposer_name
            FROM bills
            WHERE proposer_name IS NOT NULL
        """)
        local_proposers = local_cur.fetchall()
        
        updated = 0
        for row in local_proposers:
            try:
                render_cur.execute("""
                    UPDATE bills
                    SET proposer_name = %s
                    WHERE bill_id = %s
                """, (row['proposer_name'], row['bill_id']))
                if render_cur.rowcount > 0:
                    updated += 1
            except Exception as e:
                print(f"  ⚠️ 업데이트 오류 (bill_id={row['bill_id']}): {e}")
        
        render_conn.commit()
        print(f"  ✅ {updated:,}건 업데이트 완료")
        
        # 3. 누락된 votes 데이터 이전
        print("\n[3] 누락된 votes 데이터 이전 중...")
        local_cur.execute("SELECT COUNT(*) FROM votes")
        local_total = local_cur.fetchone()[0]
        
        render_cur.execute("SELECT COUNT(*) FROM votes")
        render_total = render_cur.fetchone()[0]
        
        print(f"  로컬: {local_total:,}건")
        print(f"  Render: {render_total:,}건")
        print(f"  누락: {local_total - render_total:,}건")
        
        if local_total > render_total:
            # Render에 없는 votes 찾기
            local_cur.execute("""
                SELECT v.*
                FROM votes v
                WHERE NOT EXISTS (
                    SELECT 1 FROM votes r
                    WHERE r.bill_id = v.bill_id
                    AND r.member_no = v.member_no
                    AND r.vote_date = v.vote_date
                )
                LIMIT 10000
            """)
            
            # Render의 votes 테이블 구조 확인
            render_cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'votes'
                ORDER BY ordinal_position
            """)
            render_cols = [row[0] for row in render_cur.fetchall()]
            
            local_cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'votes'
                ORDER BY ordinal_position
            """)
            local_cols = [row[0] for row in local_cur.fetchall()]
            
            common_cols = [col for col in local_cols if col in render_cols]
            print(f"  공통 컬럼: {len(common_cols)}개")
            
            # 배치로 삽입
            batch_size = 1000
            inserted = 0
            
            while True:
                rows = local_cur.fetchmany(batch_size)
                if not rows:
                    break
                
                batch_values = []
                for row in rows:
                    row_dict = dict(row)
                    values = tuple(row_dict.get(col) for col in common_cols)
                    batch_values.append(values)
                
                col_names = ', '.join(common_cols)
                placeholders = ', '.join(['%s'] * len(common_cols))
                
                insert_query = f"""
                    INSERT INTO votes ({col_names})
                    VALUES ({placeholders})
                    ON CONFLICT (bill_id, member_no, vote_date) DO NOTHING
                """
                
                try:
                    execute_batch(render_cur, insert_query, batch_values, page_size=batch_size)
                    render_conn.commit()
                    inserted += len(batch_values)
                    print(f"  진행 중... {inserted:,}건 삽입")
                except Exception as e:
                    print(f"  ⚠️ 배치 삽입 오류: {e}")
                    render_conn.rollback()
                    break
            
            print(f"  ✅ {inserted:,}건 추가 완료")
        
        # 4. member_id_mapping 데이터 이전
        print("\n[4] member_id_mapping 데이터 이전 중...")
        local_cur.execute("SELECT COUNT(*) FROM member_id_mapping")
        local_mapping_count = local_cur.fetchone()[0]
        
        render_cur.execute("SELECT COUNT(*) FROM member_id_mapping")
        render_mapping_count = render_cur.fetchone()[0]
        
        print(f"  로컬: {local_mapping_count:,}건")
        print(f"  Render: {render_mapping_count:,}건")
        
        if local_mapping_count > render_mapping_count:
            local_cur.execute("SELECT * FROM member_id_mapping")
            mappings = local_cur.fetchall()
            
            render_cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'member_id_mapping'
                ORDER BY ordinal_position
            """)
            render_cols = [row[0] for row in render_cur.fetchall()]
            
            inserted = 0
            for mapping in mappings:
                mapping_dict = dict(mapping)
                cols = [col for col in mapping_dict.keys() if col in render_cols]
                values = [mapping_dict[col] for col in cols]
                
                col_names = ', '.join(cols)
                placeholders = ', '.join(['%s'] * len(cols))
                
                try:
                    render_cur.execute(f"""
                        INSERT INTO member_id_mapping ({col_names})
                        VALUES ({placeholders})
                        ON CONFLICT (naas_cd) DO NOTHING
                    """, values)
                    if render_cur.rowcount > 0:
                        inserted += 1
                except Exception as e:
                    print(f"  ⚠️ 삽입 오류: {e}")
            
            render_conn.commit()
            print(f"  ✅ {inserted:,}건 추가 완료")
        
        print("\n" + "=" * 80)
        print("✅ 모든 수정 완료!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        render_conn.rollback()
    finally:
        local_cur.close()
        render_cur.close()
        local_conn.close()
        render_conn.close()

if __name__ == '__main__':
    fix_render_db()

