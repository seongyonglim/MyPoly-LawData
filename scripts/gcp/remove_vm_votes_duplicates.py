#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VM의 votes 테이블에서 중복 데이터를 제거하여 localhost와 동일하게 맞추기
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
if sys.platform == 'win32':
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
            except (UnicodeDecodeError, Exception):
                continue
else:
    from dotenv import load_dotenv
    load_dotenv()

# 로컬 DB 설정
LOCAL_DB = {
    'host': os.environ.get('LOCAL_DB_HOST', 'localhost'),
    'database': os.environ.get('LOCAL_DB_NAME', 'mypoly_lawdata'),
    'user': os.environ.get('LOCAL_DB_USER', 'postgres'),
    'password': os.environ.get('LOCAL_DB_PASSWORD'),
    'port': int(os.environ.get('LOCAL_DB_PORT', '5432'))
}

# Cloud SQL 설정
CLOUD_DB = {
    'host': os.environ.get('CLOUD_DB_HOST'),
    'database': os.environ.get('CLOUD_DB_NAME', 'mypoly_lawdata'),
    'user': os.environ.get('CLOUD_DB_USER', 'postgres'),
    'password': os.environ.get('CLOUD_DB_PASSWORD'),
    'port': int(os.environ.get('CLOUD_DB_PORT', '5432'))
}

def main():
    print("=" * 80)
    print("VM votes 테이블 중복 데이터 제거")
    print("=" * 80)
    
    # 로컬 DB 연결
    print("\n[1] localhost DB 연결 중...")
    try:
        local_conn = psycopg2.connect(**LOCAL_DB)
        local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ localhost DB 연결 성공")
    except Exception as e:
        print(f"❌ localhost DB 연결 실패: {e}")
        return
    
    # Cloud SQL 연결
    print("\n[2] VM (Cloud SQL) DB 연결 중...")
    if not CLOUD_DB['host'] or not CLOUD_DB['password']:
        print("❌ CLOUD_DB_HOST와 CLOUD_DB_PASSWORD 환경 변수가 필요합니다.")
        local_conn.close()
        return
    
    try:
        cloud_conn = psycopg2.connect(**CLOUD_DB)
        cloud_cur = cloud_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ VM DB 연결 성공")
    except Exception as e:
        print(f"❌ VM DB 연결 실패: {e}")
        local_conn.close()
        return
    
    try:
        # [1] localhost의 votes 고유 키 조회
        print("\n[3] localhost votes 고유 키 조회 중...")
        local_cur.execute("""
            SELECT DISTINCT bill_id, member_no, vote_date, vote_result
            FROM votes
        """)
        local_votes_set = set()
        for row in local_cur.fetchall():
            key = (row['bill_id'], row['member_no'], row['vote_date'], row['vote_result'])
            local_votes_set.add(key)
        print(f"✅ localhost 고유 votes: {len(local_votes_set):,}건")
        
        # [2] VM의 votes 개수 확인
        print("\n[4] VM votes 개수 확인 중...")
        cloud_cur.execute("SELECT COUNT(*) as cnt FROM votes")
        vm_count_before = cloud_cur.fetchone()['cnt']
        print(f"✅ VM votes (삭제 전): {vm_count_before:,}건")
        
        # [3] VM에서 localhost에 없는 데이터 삭제
        print("\n[5] VM에서 localhost에 없는 votes 삭제 중...")
        
        # 방법 1: NOT IN 사용 (대량 데이터에는 느릴 수 있음)
        # 방법 2: 임시 테이블 사용
        # 방법 3: 직접 비교하여 삭제
        
        # 가장 확실한 방법: UNIQUE 제약조건을 이용한 중복 제거
        print("  중복 제거 중...")
        cloud_cur.execute("""
            DELETE FROM votes
            WHERE vote_id NOT IN (
                SELECT MIN(vote_id)
                FROM votes
                GROUP BY bill_id, member_no, vote_date, vote_result
            )
        """)
        deleted_duplicates = cloud_cur.rowcount
        cloud_conn.commit()
        print(f"✅ 중복 제거: {deleted_duplicates:,}건 삭제")
        
        # [4] localhost에 없는 데이터 삭제
        print("\n[6] localhost에 없는 votes 삭제 중...")
        
        # localhost의 votes를 임시로 확인
        cloud_cur.execute("""
            DELETE FROM votes v
            WHERE NOT EXISTS (
                SELECT 1 FROM (
                    SELECT DISTINCT bill_id, member_no, vote_date, vote_result
                    FROM votes
                ) AS local_votes
                WHERE local_votes.bill_id = v.bill_id
                AND local_votes.member_no = v.member_no
                AND local_votes.vote_date = v.vote_date
                AND local_votes.vote_result = v.vote_result
            )
        """)
        
        # 더 나은 방법: localhost의 데이터를 직접 비교
        # 배치로 처리
        batch_size = 10000
        deleted = 0
        
        cloud_cur.execute("SELECT vote_id, bill_id, member_no, vote_date, vote_result FROM votes")
        all_vm_votes = cloud_cur.fetchall()
        
        to_delete = []
        for row in all_vm_votes:
            key = (row['bill_id'], row['member_no'], row['vote_date'], row['vote_result'])
            if key not in local_votes_set:
                to_delete.append(row['vote_id'])
        
        print(f"  삭제 대상: {len(to_delete):,}건")
        
        if len(to_delete) > 0:
            for i in range(0, len(to_delete), batch_size):
                batch = to_delete[i:i+batch_size]
                placeholders = ', '.join(['%s'] * len(batch))
                cloud_cur.execute(f"DELETE FROM votes WHERE vote_id IN ({placeholders})", batch)
                deleted += len(batch)
                cloud_conn.commit()
                if deleted % 10000 == 0:
                    print(f"  진행 중... {deleted:,}/{len(to_delete):,}건 삭제")
        
        print(f"✅ 완료: {deleted:,}건 삭제")
        
        # [5] 최종 확인
        print("\n[7] 최종 확인 중...")
        cloud_cur.execute("SELECT COUNT(*) as cnt FROM votes")
        vm_count_after = cloud_cur.fetchone()['cnt']
        print(f"✅ VM votes (삭제 후): {vm_count_after:,}건")
        print(f"✅ localhost votes: {len(local_votes_set):,}건")
        
        if vm_count_after == len(local_votes_set):
            print("✅ votes 데이터가 일치합니다!")
        else:
            diff = abs(vm_count_after - len(local_votes_set))
            print(f"⚠️ 차이가 있습니다: {diff:,}건")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        cloud_conn.rollback()
    
    finally:
        local_cur.close()
        local_conn.close()
        cloud_cur.close()
        cloud_conn.close()
    
    print("\n" + "=" * 80)
    print("✅ votes 테이블 정리 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

