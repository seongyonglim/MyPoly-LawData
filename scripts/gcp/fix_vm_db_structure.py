#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VM의 DB 구조를 localhost와 동일하게 맞추는 스크립트
- bills 테이블에 headline 컬럼 추가
- 불필요한 테이블 삭제
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

def check_column_exists(cur, table_name, column_name):
    """컬럼이 존재하는지 확인"""
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        AND column_name = %s
    """, (table_name, column_name))
    return cur.fetchone() is not None

def main():
    print("=" * 80)
    print("VM DB 구조 수정 (localhost와 동일하게 맞추기)")
    print("=" * 80)
    
    if not CLOUD_DB['host'] or not CLOUD_DB['password']:
        print("❌ CLOUD_DB_HOST와 CLOUD_DB_PASSWORD 환경 변수가 필요합니다.")
        return
    
    # Cloud SQL 연결
    print("\n[1] VM (Cloud SQL) DB 연결 중...")
    try:
        cloud_conn = psycopg2.connect(**CLOUD_DB)
        cloud_cur = cloud_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ VM DB 연결 성공")
    except Exception as e:
        print(f"❌ VM DB 연결 실패: {e}")
        return
    
    try:
        # [1] bills 테이블에 headline 컬럼 추가
        print("\n[2] bills 테이블에 headline 컬럼 추가 중...")
        if not check_column_exists(cloud_cur, 'bills', 'headline'):
            try:
                cloud_cur.execute("""
                    ALTER TABLE bills 
                    ADD COLUMN headline TEXT
                """)
                cloud_conn.commit()
                print("✅ headline 컬럼 추가 완료")
            except Exception as e:
                print(f"❌ headline 컬럼 추가 실패: {e}")
                cloud_conn.rollback()
        else:
            print("✅ headline 컬럼이 이미 존재합니다")
        
        # [2] 불필요한 테이블 삭제 (member_id_mapping)
        print("\n[3] 불필요한 테이블 삭제 중...")
        cloud_cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            AND table_name = 'member_id_mapping'
        """)
        if cloud_cur.fetchone():
            try:
                # 먼저 데이터 개수 확인
                cloud_cur.execute("SELECT COUNT(*) FROM member_id_mapping")
                result = cloud_cur.fetchone()
                count = result[0] if isinstance(result, tuple) else result['count']
                if count == 0:
                    # CASCADE로 외래키 제약조건도 함께 삭제
                    cloud_cur.execute("DROP TABLE IF EXISTS member_id_mapping CASCADE")
                    cloud_conn.commit()
                    print("✅ member_id_mapping 테이블 삭제 완료 (0건이었음)")
                else:
                    print(f"⚠️ member_id_mapping 테이블에 {count}건의 데이터가 있어 삭제하지 않습니다")
            except Exception as e:
                print(f"❌ member_id_mapping 테이블 삭제 실패: {e}")
                import traceback
                traceback.print_exc()
                cloud_conn.rollback()
        else:
            print("✅ member_id_mapping 테이블이 이미 없습니다")
        
        # [3] 컬럼 코멘트 추가 (선택사항)
        print("\n[4] headline 컬럼 코멘트 추가 중...")
        try:
            cloud_cur.execute("""
                COMMENT ON COLUMN bills.headline IS 'AI 헤드라인'
            """)
            cloud_conn.commit()
            print("✅ headline 컬럼 코멘트 추가 완료")
        except Exception as e:
            print(f"⚠️ 코멘트 추가 실패 (무시 가능): {e}")
            cloud_conn.rollback()
        
        print("\n" + "=" * 80)
        print("✅ VM DB 구조 수정 완료!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        cloud_conn.rollback()
    
    finally:
        cloud_cur.close()
        cloud_conn.close()

if __name__ == '__main__':
    main()

