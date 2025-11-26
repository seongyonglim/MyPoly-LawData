#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 데이터베이스 설정 스크립트
테이블 생성 및 초기 데이터 수집
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

# Render PostgreSQL 연결 정보
# 연결 문자열을 직접 사용 (더 안정적)
DATABASE_URL = "postgresql://mypoly_user:vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE@dpg-d4jhgdfgi27c739n9m20-a/mypoly_lawdata"

def get_db_connection():
    """데이터베이스 연결"""
    # 연결 문자열을 직접 사용
    return psycopg2.connect(DATABASE_URL)

def create_tables():
    """테이블 생성"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        print("=" * 60)
        print("Render PostgreSQL 테이블 생성 시작")
        print("=" * 60)
        
        # SQL 파일 읽기
        sql_file = 'scripts/db/create_tables_postgresql.sql'
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # SQL 실행 (세미콜론으로 구분된 각 문장 실행)
        statements = sql_content.split(';')
        
        for i, statement in enumerate(statements, 1):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cur.execute(statement)
                    conn.commit()
                    print(f"✅ 문장 {i} 실행 완료")
                except Exception as e:
                    print(f"⚠️ 문장 {i} 실행 중 오류 (무시 가능): {e}")
                    conn.rollback()
        
        print("\n" + "=" * 60)
        print("테이블 생성 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def check_tables():
    """생성된 테이블 확인"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        
        print("\n생성된 테이블:")
        print("-" * 60)
        for table in tables:
            print(f"  - {table['table_name']}")
        print(f"\n총 {len(tables)}개 테이블 생성됨")
        
    except Exception as e:
        print(f"❌ 테이블 확인 중 오류: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    print("Render PostgreSQL 데이터베이스 설정")
    print("=" * 60)
    
    # 연결 테스트
    try:
        conn = get_db_connection()
        conn.close()
        print("✅ 데이터베이스 연결 성공")
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        sys.exit(1)
    
    # 테이블 생성
    create_tables()
    
    # 테이블 확인
    check_tables()
    
    print("\n" + "=" * 60)
    print("다음 단계:")
    print("1. 데이터 수집 (선택사항):")
    print("   python scripts/db/collect_22nd_members_complete.py")
    print("   python scripts/db/collect_bills_from_date.py 20250801")
    print("   python scripts/db/collect_votes_from_date.py 20251015")
    print("2. Render.com에서 웹 서비스 배포")
    print("=" * 60)

