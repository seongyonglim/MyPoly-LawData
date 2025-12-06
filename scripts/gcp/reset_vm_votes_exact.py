#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VM의 votes 테이블을 완전히 비우고 localhost 데이터만 정확히 복사
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
    print("VM votes 테이블 완전 초기화 및 localhost 데이터 정확히 복사")
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
        # [1] VM의 votes 완전 삭제
        print("\n[3] VM votes 테이블 완전 삭제 중...")
        try:
            cloud_cur.execute("ALTER TABLE votes DISABLE TRIGGER ALL;")
            cloud_conn.commit()
        except:
            cloud_conn.rollback()
        
        cloud_cur.execute("TRUNCATE TABLE votes CASCADE")
        cloud_conn.commit()
        
        # 시퀀스 리셋
        try:
            cloud_cur.execute("ALTER SEQUENCE votes_vote_id_seq RESTART WITH 1")
            cloud_conn.commit()
        except:
            cloud_conn.rollback()
        
        cloud_cur.execute("SELECT COUNT(*) as cnt FROM votes")
        count = cloud_cur.fetchone()['cnt']
        print(f"✅ VM votes 삭제 완료 (현재: {count:,}건)")
        
        # [2] localhost 데이터 읽기
        print("\n[4] localhost votes 데이터 읽는 중...")
        local_cur.execute("SELECT COUNT(*) as cnt FROM votes")
        local_count = local_cur.fetchone()['cnt']
        print(f"✅ localhost votes: {local_count:,}건")
        
        # 컬럼 확인 (vote_id 제외)
        local_cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'votes' 
            AND table_schema = 'public'
            AND column_name != 'vote_id'
            ORDER BY ordinal_position
        """)
        columns = [row['column_name'] for row in local_cur.fetchall()]
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        print(f"✅ 삽입할 컬럼: {len(columns)}개")
        
        # [3] localhost 데이터 읽기
        local_cur.execute(f"SELECT {columns_str} FROM votes ORDER BY bill_id, member_no, vote_date")
        all_votes = local_cur.fetchall()
        print(f"✅ {len(all_votes):,}건 읽기 완료")
        
        # [4] VM에 삽입
        print("\n[5] VM에 votes 데이터 삽입 중...")
        batch_size = 5000
        inserted = 0
        
        for i in range(0, len(all_votes), batch_size):
            batch = all_votes[i:i+batch_size]
            values_list = []
            
            for row in batch:
                values = [row[col] for col in columns]
                values_list.append(tuple(values))
            
            insert_sql = f"""
                INSERT INTO votes ({columns_str})
                VALUES ({placeholders})
            """
            
            execute_batch(cloud_cur, insert_sql, values_list, page_size=batch_size)
            cloud_conn.commit()
            inserted += len(batch)
            
            if inserted % 10000 == 0:
                print(f"  진행 중... {inserted:,}/{len(all_votes):,}건 삽입")
        
        print(f"\n✅ 완료: {inserted:,}건 삽입")
        
        # [5] 최종 확인
        print("\n[6] 최종 확인 중...")
        cloud_cur.execute("SELECT COUNT(*) as cnt FROM votes")
        vm_count = cloud_cur.fetchone()['cnt']
        print(f"✅ VM votes: {vm_count:,}건")
        print(f"✅ localhost votes: {local_count:,}건")
        
        if vm_count == local_count:
            print("✅ votes 데이터가 정확히 일치합니다!")
        else:
            print(f"⚠️ 차이가 있습니다: {abs(vm_count - local_count):,}건")
        
        # 트리거 재활성화
        try:
            cloud_cur.execute("ALTER TABLE votes ENABLE TRIGGER ALL;")
            cloud_conn.commit()
        except:
            cloud_conn.rollback()
        
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
    print("✅ votes 테이블 초기화 및 복사 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

