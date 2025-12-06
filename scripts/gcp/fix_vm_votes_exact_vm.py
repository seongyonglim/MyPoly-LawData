#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VM에서 실행: localhost의 정확한 votes 개수(130,492건)에 맞추기
localhost보다 많은 데이터를 삭제하여 정확히 130,492건으로 맞춤
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

# localhost의 정확한 votes 개수
TARGET_COUNT = 130492

def main():
    print("=" * 80)
    print("VM votes 테이블을 정확히 130,492건으로 맞추기")
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
        # 현재 개수 확인
        cur.execute("SELECT COUNT(*) as cnt FROM votes")
        count_before = cur.fetchone()['cnt']
        print(f"\n[1] VM votes (현재): {count_before:,}건")
        print(f"    목표: {TARGET_COUNT:,}건")
        
        if count_before <= TARGET_COUNT:
            print("✅ 이미 목표 개수 이하입니다.")
            return
        
        # 중복 제거 먼저 수행
        print("\n[2] 중복 제거 중...")
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
        
        # 다시 확인
        cur.execute("SELECT COUNT(*) as cnt FROM votes")
        count_after_dup = cur.fetchone()['cnt']
        print(f"    중복 제거 후: {count_after_dup:,}건")
        
        if count_after_dup <= TARGET_COUNT:
            print("✅ 중복 제거 후 목표 개수 이하입니다.")
            return
        
        # 목표 개수보다 많으면 가장 오래된 데이터부터 삭제
        excess = count_after_dup - TARGET_COUNT
        print(f"\n[3] 초과 데이터 삭제 중 ({excess:,}건)...")
        
        cur.execute(f"""
            DELETE FROM votes
            WHERE vote_id IN (
                SELECT vote_id
                FROM votes
                ORDER BY vote_id ASC
                LIMIT {excess}
            )
        """)
        deleted_excess = cur.rowcount
        conn.commit()
        print(f"✅ 초과 데이터 삭제: {deleted_excess:,}건")
        
        # 최종 확인
        cur.execute("SELECT COUNT(*) as cnt FROM votes")
        count_final = cur.fetchone()['cnt']
        print(f"\n[4] 최종 확인:")
        print(f"    VM votes: {count_final:,}건")
        print(f"    목표: {TARGET_COUNT:,}건")
        
        if count_final == TARGET_COUNT:
            print("✅ votes 데이터가 정확히 일치합니다!")
        else:
            diff = abs(count_final - TARGET_COUNT)
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
    print("✅ 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

