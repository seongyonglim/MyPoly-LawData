#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
votes 테이블만 다시 이관
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
import os
from datetime import datetime

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
    print("votes 테이블만 다시 이관")
    print("=" * 80)
    
    # DB 연결
    print("\n[1] DB 연결 중...")
    try:
        local_conn = psycopg2.connect(**LOCAL_DB)
        local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ localhost DB 연결 성공")
    except Exception as e:
        print(f"❌ localhost DB 연결 실패: {e}")
        return
    
    try:
        cloud_conn = psycopg2.connect(**CLOUD_DB)
        cloud_cur = cloud_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ Cloud SQL 연결 성공")
    except Exception as e:
        print(f"❌ Cloud SQL 연결 실패: {e}")
        local_cur.close()
        local_conn.close()
        return
    
    try:
        # VM votes 테이블 완전 삭제
        print("\n[2] VM votes 테이블 삭제 중...")
        cloud_cur.execute("TRUNCATE TABLE votes CASCADE")
        cloud_conn.commit()
        print("✅ VM votes 테이블 삭제 완료")
        
        # localhost votes 데이터 읽기
        print("\n[3] localhost votes 데이터 읽는 중...")
        local_cur.execute("SELECT * FROM votes ORDER BY vote_id")
        
        total = 0
        batch_size = 5000
        batch = []
        
        while True:
            rows = local_cur.fetchmany(batch_size)
            if not rows:
                break
            
            for row in rows:
                batch.append(tuple(row.values()))
            
            if len(batch) >= batch_size:
                # 배치 삽입
                columns = list(rows[0].keys())
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join(columns)
                
                query = f"""
                    INSERT INTO votes ({columns_str})
                    VALUES ({placeholders})
                    ON CONFLICT (bill_id, member_no, vote_date, vote_result) DO NOTHING
                """
                
                try:
                    execute_batch(cloud_cur, query, batch)
                    cloud_conn.commit()
                    total += len(batch)
                    print(f"  진행 중... {total:,}건 삽입")
                except Exception as e:
                    print(f"  ⚠️ 배치 삽입 실패: {e}")
                    cloud_conn.rollback()
                
                batch = []
        
        # 남은 데이터 삽입
        if batch:
            columns = list(rows[0].keys())
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)
            
            query = f"""
                INSERT INTO votes ({columns_str})
                VALUES ({placeholders})
                ON CONFLICT (bill_id, member_no, vote_date, vote_result) DO NOTHING
            """
            
            try:
                execute_batch(cloud_cur, query, batch)
                cloud_conn.commit()
                total += len(batch)
            except Exception as e:
                print(f"  ⚠️ 마지막 배치 삽입 실패: {e}")
                cloud_conn.rollback()
        
        print(f"\n✅ 완료: {total:,}건 삽입")
        
        # 확인
        local_cur.execute("SELECT COUNT(*) as cnt FROM votes")
        local_count = local_cur.fetchone()['cnt']
        
        cloud_cur.execute("SELECT COUNT(*) as cnt FROM votes")
        cloud_count = cloud_cur.fetchone()['cnt']
        
        print(f"\n[4] 최종 확인:")
        print(f"    localhost: {local_count:,}건")
        print(f"    VM: {cloud_count:,}건")
        
        if local_count == cloud_count:
            print("    ✅ 데이터가 일치합니다!")
        else:
            print(f"    ⚠️ 차이: {abs(local_count - cloud_count):,}건")
        
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

