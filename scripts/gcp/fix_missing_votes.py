#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
localhost에 있지만 VM에 없는 votes 찾아서 삽입
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch

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

LOCAL_DB = {
    'host': os.environ.get('LOCAL_DB_HOST', 'localhost'),
    'database': os.environ.get('LOCAL_DB_NAME', 'mypoly_lawdata'),
    'user': os.environ.get('LOCAL_DB_USER', 'postgres'),
    'password': os.environ.get('LOCAL_DB_PASSWORD'),
    'port': int(os.environ.get('LOCAL_DB_PORT', '5432'))
}

CLOUD_DB = {
    'host': os.environ.get('CLOUD_DB_HOST'),
    'database': os.environ.get('CLOUD_DB_NAME', 'mypoly_lawdata'),
    'user': os.environ.get('CLOUD_DB_USER', 'postgres'),
    'password': os.environ.get('CLOUD_DB_PASSWORD'),
    'port': int(os.environ.get('CLOUD_DB_PORT', '5432'))
}

def main():
    print("=" * 80)
    print("localhost에 있지만 VM에 없는 votes 찾아서 삽입")
    print("=" * 80)
    
    local_conn = psycopg2.connect(**LOCAL_DB)
    local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
    
    cloud_conn = psycopg2.connect(**CLOUD_DB)
    cloud_cur = cloud_conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # localhost의 모든 votes 가져오기
        print("\n[1] localhost votes 읽는 중...")
        local_cur.execute("SELECT * FROM votes ORDER BY vote_id")
        local_votes = local_cur.fetchall()
        print(f"   localhost: {len(local_votes):,}건")
        
        # VM의 기존 votes 가져오기 (bill_id, member_no, vote_date, vote_result로 비교)
        print("\n[2] VM votes 읽는 중...")
        cloud_cur.execute("SELECT bill_id, member_no, vote_date, vote_result FROM votes")
        vm_votes_set = set()
        for row in cloud_cur.fetchall():
            vm_votes_set.add((row['bill_id'], row['member_no'], row['vote_date'], row['vote_result']))
        print(f"   VM: {len(vm_votes_set):,}건")
        
        # localhost에 있지만 VM에 없는 votes 찾기
        print("\n[3] 누락된 votes 찾는 중...")
        missing_votes = []
        for vote in local_votes:
            key = (vote['bill_id'], vote['member_no'], vote['vote_date'], vote['vote_result'])
            if key not in vm_votes_set:
                missing_votes.append(vote)
        
        print(f"   누락된 votes: {len(missing_votes):,}건")
        
        if not missing_votes:
            print("   ✅ 누락된 데이터가 없습니다!")
            return
        
        # 누락된 votes 삽입
        print(f"\n[4] 누락된 votes 삽입 중...")
        columns = list(missing_votes[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        
        batch = [tuple(vote.values()) for vote in missing_votes]
        query = f"""
            INSERT INTO votes ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT (bill_id, member_no, vote_date, vote_result) DO NOTHING
        """
        
        execute_batch(cloud_cur, query, batch, page_size=5000)
        cloud_conn.commit()
        
        print(f"   ✅ {len(missing_votes):,}건 삽입 완료")
        
        # 최종 확인
        print("\n[5] 최종 확인...")
        local_cur.execute("SELECT COUNT(*) as cnt FROM votes")
        local_count = local_cur.fetchone()['cnt']
        
        cloud_cur.execute("SELECT COUNT(*) as cnt FROM votes")
        cloud_count = cloud_cur.fetchone()['cnt']
        
        print(f"   localhost: {local_count:,}건")
        print(f"   VM: {cloud_count:,}건")
        
        if local_count == cloud_count:
            print("   ✅ 데이터가 일치합니다!")
        else:
            print(f"   ⚠️ 차이: {abs(local_count - cloud_count):,}건")
        
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
    print("✅ 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

