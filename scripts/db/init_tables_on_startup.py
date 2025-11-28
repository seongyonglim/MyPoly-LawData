#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
앱 시작 시 테이블이 없으면 자동으로 생성하는 스크립트
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def get_db_config():
    """환경 변수에서 데이터베이스 설정 가져오기"""
    # Railway는 DATABASE_URL 제공
    if 'DATABASE_URL' in os.environ:
        from urllib.parse import urlparse
        db_url = urlparse(os.environ['DATABASE_URL'])
        return {
            'host': db_url.hostname,
            'database': db_url.path[1:],
            'user': db_url.username,
            'password': db_url.password,
            'port': db_url.port or 5432
        }
    # Render는 개별 환경 변수 제공
    elif 'DB_HOST' in os.environ:
        return {
            'host': os.environ.get('DB_HOST'),
            'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': os.environ.get('DB_PASSWORD'),
            'port': int(os.environ.get('DB_PORT', 5432))
        }
    # 로컬 개발용
    else:
        return {
            'host': 'localhost',
            'database': 'mypoly_lawdata',
            'user': 'postgres',
            'password': 'maza_970816',
            'port': 5432
        }

def check_tables_exist():
    """테이블이 존재하는지 확인"""
    try:
        config = get_db_config()
        conn = psycopg2.connect(**config)
        cur = conn.cursor()
        
        # bills 테이블 존재 여부 확인
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'bills'
            );
        """)
        
        exists = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        return exists
    except Exception as e:
        print(f"테이블 확인 중 오류: {e}")
        return False

def create_tables():
    """테이블 생성"""
    try:
        config = get_db_config()
        conn = psycopg2.connect(**config)
        cur = conn.cursor()
        
        print("=" * 60)
        print("데이터베이스 테이블 자동 생성 시작")
        print("=" * 60)
        
        # SQL 파일 읽기
        sql_file_path = os.path.join(os.path.dirname(__file__), 'create_tables_postgresql.sql')
        if not os.path.exists(sql_file_path):
            # 상대 경로로 찾기
            sql_file_path = 'scripts/db/create_tables_postgresql.sql'
        
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # SQL 실행 (세미콜론으로 구분된 각 문장 실행)
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
        
        executed = 0
        for statement in statements:
            if statement:
                try:
                    cur.execute(statement)
                    executed += 1
                except Exception as e:
                    # 일부 오류는 무시 (예: 이미 존재하는 확장 기능, 테이블 등)
                    if 'already exists' not in str(e).lower() and 'duplicate' not in str(e).lower():
                        print(f"⚠️ 문장 실행 중 오류 (무시 가능): {e}")
        
        conn.commit()
        print(f"✅ {executed}개 SQL 문장 실행 완료")
        print("=" * 60)
        
        cur.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"❌ 테이블 생성 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if not check_tables_exist():
        print("테이블이 없습니다. 테이블을 생성합니다...")
        if create_tables():
            print("✅ 테이블 생성 완료!")
        else:
            print("❌ 테이블 생성 실패")
            sys.exit(1)
    else:
        print("✅ 테이블이 이미 존재합니다.")


