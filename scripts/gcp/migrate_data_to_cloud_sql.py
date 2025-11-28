#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
로컬 데이터를 Cloud SQL로 마이그레이션
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import os

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 로컬 DB 설정
LOCAL_DB = {
    'host': 'localhost',
    'database': 'mypoly_lawdata',
    'user': 'postgres',
    'password': 'maza_970816',
    'port': 5432
}

# Cloud SQL 설정 (환경 변수 또는 직접 입력)
# 방법 1: 환경 변수 사용
# export CLOUD_DB_HOST=34.50.48.31
# export CLOUD_DB_PASSWORD=Mypoly!2025

# 방법 2: 직접 입력 (환경 변수가 없으면 여기 수정)
CLOUD_DB = {
    'host': os.environ.get('CLOUD_DB_HOST', '34.50.48.31'),  # Cloud SQL 공개 IP (여기 수정!)
    'database': os.environ.get('CLOUD_DB_NAME', 'mypoly_lawdata'),
    'user': os.environ.get('CLOUD_DB_USER', 'postgres'),
    'password': os.environ.get('CLOUD_DB_PASSWORD', 'Mypoly!2025'),  # Cloud SQL 비밀번호 (여기 수정!)
    'port': int(os.environ.get('CLOUD_DB_PORT', '5432'))
}

def migrate_table(local_cur, cloud_cur, table_name):
    """테이블 데이터 마이그레이션"""
    print(f"\n[{table_name}] 마이그레이션 중...")
    
    # 로컬에서 데이터 읽기
    local_cur.execute(f"SELECT * FROM {table_name}")
    rows = local_cur.fetchall()
    
    if not rows:
        print(f"  ⚠️ 데이터 없음 (건너뜀)")
        return
    
    print(f"  📊 총 {len(rows):,}건")
    
    # Cloud SQL에 데이터 삽입
    # 먼저 컬럼 목록 가져오기
    local_cur.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s 
        AND table_schema = 'public'
        ORDER BY ordinal_position
    """, (table_name,))
    
    columns = [row[0] for row in local_cur.fetchall()]
    columns_str = ', '.join(columns)
    placeholders = ', '.join(['%s'] * len(columns))
    
    # 기존 데이터 삭제 (선택사항)
    cloud_cur.execute(f"TRUNCATE TABLE {table_name} CASCADE")
    
    # 데이터 삽입
    inserted = 0
    for row in rows:
        values = [row[col] for col in columns]
        try:
            cloud_cur.execute(
                f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                values
            )
            inserted += 1
        except Exception as e:
            print(f"  ⚠️ 삽입 오류: {e}")
            continue
    
    print(f"  ✅ {inserted:,}건 삽입 완료")

def main():
    """메인 함수"""
    print("=" * 80)
    print("로컬 → Cloud SQL 데이터 마이그레이션")
    print("=" * 80)
    
    # Cloud SQL 비밀번호 확인
    if not CLOUD_DB['password']:
        print("\n⚠️ Cloud SQL 비밀번호가 설정되지 않았습니다.")
        print("환경 변수 CLOUD_DB_PASSWORD를 설정하거나 스크립트를 수정하세요.")
        return
    
    # 로컬 DB 연결
    print("\n[1] 로컬 DB 연결 중...")
    try:
        local_conn = psycopg2.connect(**LOCAL_DB)
        local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ 로컬 DB 연결 성공")
    except Exception as e:
        print(f"❌ 로컬 DB 연결 실패: {e}")
        return
    
    # Cloud SQL 연결
    print("\n[2] Cloud SQL 연결 중...")
    try:
        cloud_conn = psycopg2.connect(**CLOUD_DB)
        cloud_cur = cloud_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ Cloud SQL 연결 성공")
    except Exception as e:
        print(f"❌ Cloud SQL 연결 실패: {e}")
        print("\n💡 Cloud SQL Proxy가 실행 중인지 확인하세요:")
        print("   sudo systemctl start cloud-sql-proxy")
        local_conn.close()
        return
    
    # 마이그레이션할 테이블 목록
    tables = [
        'bills',
        'assembly_members',
        'votes',
        'proc_stage_mapping',
        # 추후 기능용 테이블은 선택사항
        # 'user_votes',
        # 'user_political_profile',
        # 'member_political_profile',
        # 'bill_similarity',
    ]
    
    print("\n[3] 데이터 마이그레이션 시작...")
    print(f"마이그레이션할 테이블: {', '.join(tables)}")
    
    for table in tables:
        try:
            migrate_table(local_cur, cloud_cur, table)
            cloud_conn.commit()
        except Exception as e:
            cloud_conn.rollback()
            print(f"  ❌ 오류: {e}")
    
    # 연결 종료
    local_cur.close()
    local_conn.close()
    cloud_cur.close()
    cloud_conn.close()
    
    print("\n" + "=" * 80)
    print("마이그레이션 완료!")
    print("=" * 80)

if __name__ == '__main__':
    main()

