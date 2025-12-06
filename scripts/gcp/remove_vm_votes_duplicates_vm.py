#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VM에서 실행: VM의 votes 테이블에서 localhost 기준으로 중복 데이터 제거
localhost의 votes 데이터를 직접 비교하여 VM에서 localhost에 없는 데이터를 삭제
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
from dotenv import load_dotenv
load_dotenv()

# VM DB 설정 (VM에서 실행 시)
DB = {
    'host': os.environ.get('DB_HOST'),
    'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD'),
    'port': int(os.environ.get('DB_PORT', '5432'))
}

# localhost DB 설정 (비교용 - localhost에서 실행 시에만 사용)
LOCAL_DB = {
    'host': os.environ.get('LOCAL_DB_HOST', 'localhost'),
    'database': os.environ.get('LOCAL_DB_NAME', 'mypoly_lawdata'),
    'user': os.environ.get('LOCAL_DB_USER', 'postgres'),
    'password': os.environ.get('LOCAL_DB_PASSWORD'),
    'port': int(os.environ.get('LOCAL_DB_PORT', '5432'))
}

def get_localhost_votes():
    """localhost의 votes 고유 키 조회 (localhost에서 실행 시)"""
    try:
        conn = psycopg2.connect(**LOCAL_DB)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT DISTINCT bill_id, member_no, vote_date, vote_result
            FROM votes
        """)
        votes_set = set()
        for row in cur.fetchall():
            key = (row['bill_id'], row['member_no'], row['vote_date'], row['vote_result'])
            votes_set.add(key)
        cur.close()
        conn.close()
        return votes_set
    except Exception as e:
        print(f"⚠️ localhost DB 연결 실패 (무시 가능): {e}")
        return None

def main():
    print("=" * 80)
    print("VM votes 테이블 중복 데이터 제거")
    print("=" * 80)
    
    if not DB['host'] or not DB['password']:
        print("❌ DB_HOST와 DB_PASSWORD 환경 변수가 필요합니다.")
        return
    
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        print("✅ VM DB 연결 성공")
    except Exception as e:
        print(f"❌ VM DB 연결 실패: {e}")
        return
    
    try:
        # localhost votes 조회 시도
        print("\n[1] localhost votes 데이터 조회 시도 중...")
        localhost_votes = get_localhost_votes()
        
        if localhost_votes is None:
            print("⚠️ localhost DB에 접근할 수 없습니다.")
            print("   VM에서 실행 중이므로 localhost 기준 비교를 건너뜁니다.")
            print("   중복 제거만 수행합니다.")
            
            # 중복 제거만 수행
            cur.execute("SELECT COUNT(*) as cnt FROM votes")
            count_before = cur.fetchone()['cnt']
            print(f"\n[2] VM votes (삭제 전): {count_before:,}건")
            
            cur.execute("""
                DELETE FROM votes
                WHERE vote_id NOT IN (
                    SELECT MIN(vote_id)
                    FROM votes
                    GROUP BY bill_id, member_no, vote_date, vote_result
                )
            """)
            deleted = cur.rowcount
            conn.commit()
            print(f"✅ 중복 제거: {deleted:,}건 삭제")
            
            cur.execute("SELECT COUNT(*) as cnt FROM votes")
            count_after = cur.fetchone()['cnt']
            print(f"\n[3] VM votes (삭제 후): {count_after:,}건")
            return
        
        print(f"✅ localhost 고유 votes: {len(localhost_votes):,}건")
        
        # VM의 votes 개수 확인
        print("\n[2] VM votes 개수 확인 중...")
        cur.execute("SELECT COUNT(*) as cnt FROM votes")
        vm_count_before = cur.fetchone()['cnt']
        print(f"✅ VM votes (삭제 전): {vm_count_before:,}건")
        
        # VM에서 localhost에 없는 데이터 삭제
        print("\n[3] VM에서 localhost에 없는 votes 삭제 중...")
        
        # 먼저 중복 제거
        cur.execute("""
            DELETE FROM votes
            WHERE vote_id NOT IN (
                SELECT MIN(vote_id)
                FROM votes
                GROUP BY bill_id, member_no, vote_date, vote_result
            )
        """)
        deleted_duplicates = cur.rowcount
        conn.commit()
        print(f"✅ 중복 제거: {deleted_duplicates:,}건 삭제")
        
        # localhost에 없는 데이터 삭제
        cur.execute("SELECT vote_id, bill_id, member_no, vote_date, vote_result FROM votes")
        all_vm_votes = cur.fetchall()
        
        to_delete = []
        for row in all_vm_votes:
            key = (row['bill_id'], row['member_no'], row['vote_date'], row['vote_result'])
            if key not in localhost_votes:
                to_delete.append(row['vote_id'])
        
        print(f"  삭제 대상: {len(to_delete):,}건")
        
        if len(to_delete) > 0:
            batch_size = 10000
            deleted = 0
            for i in range(0, len(to_delete), batch_size):
                batch = to_delete[i:i+batch_size]
                placeholders = ', '.join(['%s'] * len(batch))
                cur.execute(f"DELETE FROM votes WHERE vote_id IN ({placeholders})", batch)
                deleted += len(batch)
                conn.commit()
                if deleted % 10000 == 0:
                    print(f"  진행 중... {deleted:,}/{len(to_delete):,}건 삭제")
            
            print(f"✅ 완료: {deleted:,}건 삭제")
        
        # 최종 확인
        print("\n[4] 최종 확인 중...")
        cur.execute("SELECT COUNT(*) as cnt FROM votes")
        vm_count_after = cur.fetchone()['cnt']
        print(f"✅ VM votes (삭제 후): {vm_count_after:,}건")
        print(f"✅ localhost votes: {len(localhost_votes):,}건")
        
        if vm_count_after == len(localhost_votes):
            print("✅ votes 데이터가 일치합니다!")
        else:
            diff = abs(vm_count_after - len(localhost_votes))
            print(f"⚠️ 차이가 있습니다: {diff:,}건")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    
    finally:
        cur.close()
        conn.close()
    
    print("\n" + "=" * 80)
    print("✅ votes 테이블 정리 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

