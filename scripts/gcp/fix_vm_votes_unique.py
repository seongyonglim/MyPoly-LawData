#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VM의 votes 테이블에서 UNIQUE 제약조건을 이용해 중복 제거
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
    print("VM votes 테이블 UNIQUE 제약조건으로 중복 제거")
    print("=" * 80)
    
    if not CLOUD_DB['host'] or not CLOUD_DB['password']:
        print("❌ CLOUD_DB_HOST와 CLOUD_DB_PASSWORD 환경 변수가 필요합니다.")
        return
    
    try:
        cloud_conn = psycopg2.connect(**CLOUD_DB)
        cloud_cur = cloud_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ VM DB 연결 성공")
    except Exception as e:
        print(f"❌ VM DB 연결 실패: {e}")
        return
    
    try:
        # 현재 개수 확인
        cloud_cur.execute("SELECT COUNT(*) as cnt FROM votes")
        count_before = cloud_cur.fetchone()['cnt']
        print(f"\n[1] VM votes (삭제 전): {count_before:,}건")
        
        # UNIQUE 제약조건을 이용한 중복 제거
        print("\n[2] UNIQUE 제약조건으로 중복 제거 중...")
        cloud_cur.execute("""
            DELETE FROM votes
            WHERE vote_id NOT IN (
                SELECT MIN(vote_id)
                FROM votes
                GROUP BY bill_id, member_no, vote_date, vote_result
            )
        """)
        deleted = cloud_cur.rowcount
        cloud_conn.commit()
        print(f"✅ 중복 제거: {deleted:,}건 삭제")
        
        # 최종 확인
        cloud_cur.execute("SELECT COUNT(*) as cnt FROM votes")
        count_after = cloud_cur.fetchone()['cnt']
        print(f"\n[3] VM votes (삭제 후): {count_after:,}건")
        print(f"✅ {deleted:,}건의 중복 데이터가 제거되었습니다")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        cloud_conn.rollback()
    
    finally:
        cloud_cur.close()
        cloud_conn.close()
    
    print("\n" + "=" * 80)
    print("✅ 중복 제거 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

