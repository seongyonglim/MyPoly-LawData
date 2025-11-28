#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VM에서 실행: 로컬 DB에서 데이터를 읽어서 Cloud SQL에 삽입
로컬 PC의 공개 IP를 통해 접속
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

# 로컬 DB 설정 (로컬 PC의 공개 IP 필요)
# 사용자가 환경 변수로 설정하거나 직접 입력
LOCAL_DB_IP = os.environ.get('LOCAL_DB_IP', '')
LOCAL_DB_PASSWORD = os.environ.get('LOCAL_DB_PASSWORD', 'maza_970816')

LOCAL_DB = {
    'host': LOCAL_DB_IP,
    'database': 'mypoly_lawdata',
    'user': 'postgres',
    'password': LOCAL_DB_PASSWORD,
    'port': 5432,
    'connect_timeout': 10
}

# Cloud SQL 설정 (Cloud SQL Proxy를 통해)
CLOUD_DB = {
    'host': '127.0.0.1',  # Cloud SQL Proxy
    'database': 'mypoly_lawdata',
    'user': 'postgres',
    'password': os.environ.get('CLOUD_DB_PASSWORD', 'Mypoly!2025'),
    'port': 5432
}

def get_table_columns(cur, table_name):
    """테이블의 컬럼 목록 가져오기"""
    cur.execute(f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'public'
        ORDER BY ordinal_position;
    """, (table_name,))
    return {row[0]: row[1] for row in cur.fetchall()}

def migrate_table(local_cur, cloud_cur, cloud_conn, table_name):
    """테이블 데이터 마이그레이션"""
    print(f"\n[{table_name}] 마이그레이션 중...")
    
    try:
        # 로컬에서 데이터 읽기
        print(f"  📖 로컬 DB에서 데이터 읽는 중...")
        local_cur.execute(f"SELECT * FROM {table_name} ORDER BY 1")
        rows = local_cur.fetchall()
        
        if not rows:
            print(f"  ⚠️ 데이터 없음 (건너뜀)")
            return
        
        total_rows = len(rows)
        print(f"  📊 총 {total_rows:,}건")
        
        # 컬럼 정보
        columns = list(rows[0].keys())
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        # Cloud SQL 테이블 구조 확인
        cloud_columns = get_table_columns(cloud_cur, table_name)
        cloud_column_names = list(cloud_columns.keys())
        
        # 공통 컬럼만 사용
        common_columns = [col for col in columns if col in cloud_column_names]
        if not common_columns:
            print(f"  ⚠️ 공통 컬럼 없음 (건너뜀)")
            return
        
        columns_str = ', '.join(common_columns)
        placeholders = ', '.join(['%s'] * len(common_columns))
        
        # 기존 데이터 삭제 (TRUNCATE는 권한 문제 없음)
        print(f"  🗑️ 기존 데이터 삭제 중...")
        try:
            cloud_cur.execute(f"TRUNCATE TABLE {table_name} CASCADE")
            cloud_conn.commit()
            print(f"  ✅ 기존 데이터 삭제 완료")
        except Exception as e:
            print(f"  ⚠️ TRUNCATE 실패 (계속 진행): {e}")
            cloud_conn.rollback()
        
        # 배치 삽입
        print(f"  💾 데이터 삽입 중...")
        batch_size = 1000
        inserted = 0
        error_count = 0
        
        for i in range(0, total_rows, batch_size):
            batch = rows[i:min(i+batch_size, total_rows)]
            values_list = []
            
            for row in batch:
                values = [row[col] for col in common_columns]
                values_list.append(values)
            
            try:
                execute_batch(
                    cloud_cur,
                    f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                    values_list,
                    page_size=batch_size
                )
                inserted += len(batch)
                cloud_conn.commit()
                
                progress = (inserted * 100) // total_rows
                print(f"  진행: {inserted:,}/{total_rows:,}건 ({progress}%)", end='\r')
                
            except Exception as e:
                cloud_conn.rollback()
                error_count += len(batch)
                if error_count < 10:
                    print(f"\n  ⚠️ 배치 오류 (건너뜀): {str(e)[:100]}")
                # 개별 삽입 시도
                for row in batch:
                    values = [row[col] for col in common_columns]
                    try:
                        cloud_cur.execute(
                            f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                            values
                        )
                        cloud_conn.commit()
                        inserted += 1
                        error_count -= 1
                    except:
                        cloud_conn.rollback()
                        continue
        
        print(f"\n  ✅ 완료: {inserted:,}건 삽입, {error_count:,}건 오류")
        
    except Exception as e:
        cloud_conn.rollback()
        print(f"  ❌ 오류: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("=" * 80)
    print("로컬 DB → Cloud SQL 데이터 마이그레이션 (VM에서 실행)")
    print("=" * 80)
    
    # 로컬 DB IP 확인
    if not LOCAL_DB_IP:
        print("\n❌ 로컬 DB IP가 설정되지 않았습니다.")
        print("\n📋 설정 방법:")
        print("1. 로컬 PC의 공개 IP 확인:")
        print("   Windows: https://www.whatismyip.com/ 접속")
        print("   또는 PowerShell: (Invoke-WebRequest -Uri 'https://api.ipify.org').Content")
        print("\n2. 로컬 PostgreSQL 외부 접속 허용:")
        print("   - postgresql.conf: listen_addresses = '*'")
        print("   - pg_hba.conf: host all all 0.0.0.0/0 md5")
        print("   - PostgreSQL 재시작")
        print("\n3. Windows 방화벽에서 포트 5432 허용")
        print("\n4. VM에서 실행:")
        print("   export LOCAL_DB_IP='로컬PC공개IP'")
        print("   python scripts/gcp/migrate_direct_python.py")
        return
    
    print(f"\n로컬 DB IP: {LOCAL_DB_IP}")
    
    # 로컬 DB 연결
    print(f"\n[1] 로컬 DB 연결 중... ({LOCAL_DB_IP}:5432)")
    try:
        local_conn = psycopg2.connect(**LOCAL_DB)
        local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ 로컬 DB 연결 성공")
    except Exception as e:
        print(f"❌ 로컬 DB 연결 실패: {e}")
        print("\n💡 확인 사항:")
        print("1. 로컬 PostgreSQL이 외부 접속을 허용하는지")
        print("2. Windows 방화벽에서 포트 5432가 열려있는지")
        print("3. 로컬 PC의 공개 IP가 올바른지")
        return
    
    # Cloud SQL 연결
    print("\n[2] Cloud SQL 연결 중... (127.0.0.1:5432 via Proxy)")
    try:
        cloud_conn = psycopg2.connect(**CLOUD_DB)
        cloud_cur = cloud_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ Cloud SQL 연결 성공")
    except Exception as e:
        print(f"❌ Cloud SQL 연결 실패: {e}")
        print("\n💡 Cloud SQL Proxy가 실행 중인지 확인:")
        print("   ps aux | grep cloud_sql_proxy")
        local_conn.close()
        return
    
    # 마이그레이션할 테이블 (외래키 순서 고려)
    tables = [
        'proc_stage_mapping',
        'assembly_members',
        'bills',
        'votes',
    ]
    
    print("\n[3] 데이터 마이그레이션 시작...")
    start_time = datetime.now()
    
    for table in tables:
        try:
            migrate_table(local_cur, cloud_cur, cloud_conn, table)
        except Exception as e:
            print(f"  ❌ 테이블 {table} 오류: {e}")
    
    elapsed = datetime.now() - start_time
    
    # 연결 종료
    local_cur.close()
    local_conn.close()
    cloud_cur.close()
    cloud_conn.close()
    
    print("\n" + "=" * 80)
    print(f"마이그레이션 완료! (소요 시간: {elapsed})")
    print("=" * 80)

if __name__ == '__main__':
    main()

