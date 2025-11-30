#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
표결정보에서 mona_cd와 member_no를 가져와서 assembly_members에 업데이트
표결정보 API에서만 제공하는 필드들을 매핑
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def get_db_config():
    """환경 변수에서 데이터베이스 설정 가져오기 (app.py와 동일한 방식)"""
    # GCP 환경 변수 확인 (VM에서 Cloud SQL Proxy 사용 시)
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_name = os.environ.get('DB_NAME', 'mypoly_lawdata')
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', 'maza_970816')
    db_port = int(os.environ.get('DB_PORT', '5432'))
    
    return {
        'host': db_host,
        'database': db_name,
        'user': db_user,
        'password': db_password,
        'port': db_port
    }

def get_db_connection():
    config = get_db_config()
    return psycopg2.connect(**config)

def update_member_ids_from_votes():
    """표결정보에서 mona_cd와 member_no를 가져와서 assembly_members에 업데이트"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("표결정보에서 의원 식별자 매핑 업데이트")
    print("=" * 80)
    
    try:
        # votes 테이블에서 member_id별로 mona_cd와 member_no를 가져옴
        # 가장 최근 표결 정보를 우선 사용
        cur.execute("""
            SELECT DISTINCT ON (member_id)
                member_id,
                mona_cd,
                member_no
            FROM votes
            WHERE member_id IS NOT NULL
                AND (mona_cd IS NOT NULL OR member_no IS NOT NULL)
            ORDER BY member_id, vote_date DESC NULLS LAST
        """)
        
        vote_mappings = cur.fetchall()
        print(f"\n표결정보에서 {len(vote_mappings)}건의 매핑 정보 발견")
        
        updated_count = 0
        
        for mapping in vote_mappings:
            member_id = mapping['member_id']
            mona_cd = mapping['mona_cd']
            member_no = mapping['member_no']
            
            # assembly_members에 업데이트
            update_fields = []
            update_values = []
            
            if mona_cd:
                update_fields.append("mona_cd = %s")
                update_values.append(mona_cd)
            
            if member_no:
                update_fields.append("member_no = %s")
                update_values.append(member_no)
            
            if update_fields:
                update_values.append(member_id)
                update_sql = f"""
                    UPDATE assembly_members
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE member_id = %s
                        AND (mona_cd IS NULL OR member_no IS NULL)
                """
                
                cur.execute(update_sql, update_values)
                if cur.rowcount > 0:
                    updated_count += 1
        
        conn.commit()
        
        print(f"\n✅ 업데이트 완료: {updated_count}건")
        
        # 업데이트 결과 확인
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(mona_cd) as has_mona_cd,
                COUNT(member_no) as has_member_no
            FROM assembly_members
        """)
        result = cur.fetchone()
        
        print(f"\n현재 상태:")
        print(f"  - 전체 의원: {result['total']}명")
        print(f"  - MONA 코드 있음: {result['has_mona_cd']}명 ({result['has_mona_cd']/result['total']*100:.1f}%)")
        print(f"  - 의원번호 있음: {result['has_member_no']}명 ({result['has_member_no']/result['total']*100:.1f}%)")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        conn.rollback()
        raise
    
    finally:
        cur.close()
        conn.close()
    
    print("=" * 80)

if __name__ == '__main__':
    update_member_ids_from_votes()


