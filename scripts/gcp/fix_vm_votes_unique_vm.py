#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VM에서 실행: VM의 votes 테이블에서 UNIQUE 제약조건을 이용해 중복 제거
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

def main():
    print("=" * 80)
    print("VM votes 테이블 UNIQUE 제약조건으로 중복 제거")
    print("=" * 80)
    
    if not DB['host'] or not DB['password']:
        print("❌ DB_HOST와 DB_PASSWORD 환경 변수가 필요합니다.")
        print("   .env 파일에 다음을 확인하세요:")
        print("   DB_HOST=your_cloud_sql_ip")
        print("   DB_PASSWORD=your_cloud_password")
        return
    
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        print("✅ VM DB 연결 성공")
    except Exception as e:
        print(f"❌ VM DB 연결 실패: {e}")
        return
    
    try:
        # 현재 개수 확인
        cur.execute("SELECT COUNT(*) as cnt FROM votes")
        count_before = cur.fetchone()['cnt']
        print(f"\n[1] VM votes (삭제 전): {count_before:,}건")
        
        # UNIQUE 제약조건을 이용한 중복 제거
        print("\n[2] UNIQUE 제약조건으로 중복 제거 중...")
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
        
        # 최종 확인
        cur.execute("SELECT COUNT(*) as cnt FROM votes")
        count_after = cur.fetchone()['cnt']
        print(f"\n[3] VM votes (삭제 후): {count_after:,}건")
        print(f"✅ {deleted:,}건의 중복 데이터가 제거되었습니다")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    
    finally:
        cur.close()
        conn.close()
    
    print("\n" + "=" * 80)
    print("✅ 중복 제거 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

