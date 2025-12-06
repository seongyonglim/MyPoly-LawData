#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
의원 매핑 개선 스크립트
- 이름과 정당으로 정확한 매핑
- member_no, mona_cd로 매핑
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()

def get_db_connection():
    """데이터베이스 연결 생성"""
    try:
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_name = os.environ.get('DB_NAME', 'mypoly_lawdata')
        db_user = os.environ.get('DB_USER', 'postgres')
        db_password = os.environ.get('DB_PASSWORD')
        if not db_password:
            raise ValueError("DB_PASSWORD environment variable is required")
        db_port = int(os.environ.get('DB_PORT', '5432'))
        
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        return conn
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        raise

def improve_member_mapping(conn):
    """의원 매핑 개선"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("의원 매핑 개선")
    print("=" * 80)
    
    # 1. votes에서 member_no/mona_cd로 assembly_members 매핑
    print("\n[1] member_no/mona_cd로 매핑")
    
    cur.execute("""
        UPDATE votes v
        SET member_id = am.member_id
        FROM assembly_members am
        WHERE v.member_id IS NULL
        AND (
            (v.member_no IS NOT NULL AND am.member_no = v.member_no) OR
            (v.mona_cd IS NOT NULL AND am.mona_cd = v.mona_cd)
        )
    """)
    
    updated_count = cur.rowcount
    conn.commit()
    print(f"  ✅ {updated_count:,}건의 표결에 member_id 매핑 완료")
    
    # 2. 이름과 정당으로 매핑 (member_no/mona_cd가 없는 경우)
    print("\n[2] 이름과 정당으로 매핑")
    
    cur.execute("""
        UPDATE votes v
        SET member_id = am.member_id
        FROM assembly_members am
        WHERE v.member_id IS NULL
        AND v.member_name IS NOT NULL
        AND v.member_name != ''
        AND v.party_name IS NOT NULL
        AND v.party_name != ''
        AND am.name = v.member_name
        AND am.party = v.party_name
        AND NOT EXISTS (
            SELECT 1 FROM assembly_members am2
            WHERE am2.name = v.member_name
            AND am2.party != v.party_name
        )
    """)
    
    updated_count = cur.rowcount
    conn.commit()
    print(f"  ✅ {updated_count:,}건의 표결에 member_id 매핑 완료")
    
    # 3. assembly_members에 member_no, mona_cd 업데이트
    print("\n[3] assembly_members에 member_no, mona_cd 업데이트")
    
    cur.execute("""
        UPDATE assembly_members am
        SET 
            member_no = v.member_no,
            mona_cd = v.mona_cd,
            updated_at = CURRENT_TIMESTAMP
        FROM (
            SELECT DISTINCT ON (member_name, party_name)
                member_name,
                party_name,
                member_no,
                mona_cd
            FROM votes
            WHERE member_no IS NOT NULL OR mona_cd IS NOT NULL
            ORDER BY member_name, party_name, vote_date DESC
        ) v
        WHERE am.name = v.member_name
        AND am.party = v.party_name
        AND (am.member_no IS NULL OR am.mona_cd IS NULL)
    """)
    
    updated_count = cur.rowcount
    conn.commit()
    print(f"  ✅ {updated_count:,}건의 의원 정보 업데이트 완료")
    
    # 4. 최종 통계
    print("\n[4] 최종 통계")
    
    cur.execute("""
        SELECT 
            COUNT(*) as total_votes,
            COUNT(member_id) as mapped_votes
        FROM votes
    """)
    
    vote_stats = cur.fetchone()
    total_votes = vote_stats['total_votes']
    mapped_votes = vote_stats['mapped_votes']
    unmapped_votes = total_votes - mapped_votes
    
    print(f"  전체 표결: {total_votes:,}건")
    if total_votes > 0:
        print(f"  매핑된 표결: {mapped_votes:,}건 ({mapped_votes/total_votes*100:.1f}%)")
        print(f"  미매핑 표결: {unmapped_votes:,}건 ({unmapped_votes/total_votes*100:.1f}%)")
    
    cur.execute("""
        SELECT 
            COUNT(*) as total_members,
            COUNT(member_no) as has_member_no,
            COUNT(mona_cd) as has_mona_cd
        FROM assembly_members
    """)
    
    member_stats = cur.fetchone()
    total_members = member_stats['total_members']
    has_member_no = member_stats['has_member_no']
    has_mona_cd = member_stats['has_mona_cd']
    
    print(f"\n  전체 의원: {total_members:,}명")
    if total_members > 0:
        print(f"  member_no 있음: {has_member_no:,}명 ({has_member_no/total_members*100:.1f}%)")
        print(f"  mona_cd 있음: {has_mona_cd:,}명 ({has_mona_cd/total_members*100:.1f}%)")
    
    # 5. 미매핑 표결 상세 확인
    if unmapped_votes > 0:
        print("\n[5] 미매핑 표결 상세")
        
        cur.execute("""
            SELECT 
                member_name,
                party_name,
                member_no,
                mona_cd,
                COUNT(*) as vote_count
            FROM votes
            WHERE member_id IS NULL
            GROUP BY member_name, party_name, member_no, mona_cd
            ORDER BY vote_count DESC
            LIMIT 10
        """)
        
        unmapped = cur.fetchall()
        print(f"  상위 10개 미매핑 표결:")
        for item in unmapped:
            print(f"    - {item['member_name']} ({item['party_name']}): {item['vote_count']:,}건")
    
    cur.close()

def main():
    """메인 함수"""
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    conn = get_db_connection()
    
    try:
        improve_member_mapping(conn)
        
        print("\n" + "=" * 80)
        print("작업 완료")
        print("=" * 80)
        print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    main()

