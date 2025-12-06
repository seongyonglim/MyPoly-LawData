#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
로컬 PC에서 실행: 로컬 DB에서 데이터를 읽어서 Cloud SQL 공개 IP로 직접 삽입
GCP 방화벽 규칙에 로컬 PC의 공개 IP를 추가해야 함
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
import os
from datetime import datetime
import socket

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import sys

# Windows에서 .env 파일 인코딩 문제 해결
# dotenv 대신 직접 파일 읽기
if sys.platform == 'win32':
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_file):
        # 여러 인코딩 시도
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

# Cloud SQL 설정 (공개 IP 직접 사용)
# GCP 콘솔에서 방화벽 규칙에 로컬 PC의 공개 IP를 추가해야 함
CLOUD_DB = {
    'host': os.environ.get('CLOUD_DB_HOST'),  # Cloud SQL 공개 IP (GCP 콘솔에서 확인)
    'database': os.environ.get('CLOUD_DB_NAME', 'mypoly_lawdata'),
    'user': os.environ.get('CLOUD_DB_USER', 'postgres'),
    'password': os.environ.get('CLOUD_DB_PASSWORD'),
    'port': int(os.environ.get('CLOUD_DB_PORT', '5432'))
}

def get_table_columns(cur, table_name):
    """테이블의 컬럼 목록 가져오기"""
    cur.execute(f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'public'
        ORDER BY ordinal_position;
    """, (table_name,))
    rows = cur.fetchall()
    # RealDictCursor를 사용하므로 딕셔너리로 접근
    if rows and isinstance(rows[0], dict):
        return {row['column_name']: row['data_type'] for row in rows}
    else:
        # 일반 cursor인 경우 튜플로 접근
        return {row[0]: row[1] for row in rows}

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
        
        # 기존 데이터 삭제
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
    print("로컬 DB → Cloud SQL 데이터 마이그레이션 (공개 IP 직접 사용)")
    print("=" * 80)
    
    # 환경 변수 확인
    if not LOCAL_DB['password']:
        print("❌ 오류: LOCAL_DB_PASSWORD 환경 변수가 필요합니다.")
        print("   .env 파일에 다음을 추가하세요:")
        print("   LOCAL_DB_PASSWORD=your_local_password")
        return
    
    if not CLOUD_DB['host'] or not CLOUD_DB['password']:
        print("❌ 오류: CLOUD_DB_HOST와 CLOUD_DB_PASSWORD 환경 변수가 필요합니다.")
        print("   .env 파일에 다음을 추가하세요:")
        print("   CLOUD_DB_HOST=34.50.48.31")
        print("   CLOUD_DB_PASSWORD=your_cloud_password")
        return
    
    print("\n⚠️ 사전 준비:")
    print("1. GCP 콘솔 → Cloud SQL → 인스턴스 → 연결")
    print("2. '승인된 네트워크'에 로컬 PC의 공개 IP 추가")
    print("3. 공개 IP 확인: https://www.whatismyip.com/")
    print("=" * 80)
    
    # 로컬 DB 연결 (타임아웃 10초)
    print(f"\n[1] 로컬 DB 연결 중... (localhost:5432)")
    print("   연결 확인 중...", end='', flush=True)
    try:
        # 포트 연결 확인
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((LOCAL_DB['host'], LOCAL_DB['port']))
        sock.close()
        if result != 0:
            print(f"\n❌ 로컬 DB 포트 연결 실패 (포트 {LOCAL_DB['port']}가 열려있지 않음)")
            print("   PostgreSQL이 실행 중인지 확인하세요.")
            return
        print(" ✓", flush=True)
        
        # 실제 DB 연결
        local_conn = psycopg2.connect(**LOCAL_DB, connect_timeout=10)
        local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ 로컬 DB 연결 성공")
    except psycopg2.OperationalError as e:
        print(f"\n❌ 로컬 DB 연결 실패: {e}")
        print("   - PostgreSQL이 실행 중인지 확인")
        print("   - 비밀번호가 올바른지 확인")
        return
    except Exception as e:
        print(f"\n❌ 로컬 DB 연결 실패: {e}")
        return
    
    # Cloud SQL 연결 (타임아웃 10초)
    cloud_host = CLOUD_DB.get('host', '')
    cloud_port = CLOUD_DB.get('port', 5432)
    print(f"\n[2] Cloud SQL 연결 중... ({cloud_host}:{cloud_port})")
    print("   연결 확인 중...", end='', flush=True)
    try:
        # 포트 연결 확인
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((cloud_host, cloud_port))
        sock.close()
        if result != 0:
            print(f"\n❌ Cloud SQL 포트 연결 실패")
            print("   - GCP 방화벽 규칙 확인 필요")
            print("   - 공개 IP가 '승인된 네트워크'에 추가되었는지 확인")
            local_conn.close()
            return
        print(" ✓", flush=True)
        
        # 실제 DB 연결
        cloud_conn = psycopg2.connect(**CLOUD_DB, connect_timeout=10)
        cloud_cur = cloud_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ Cloud SQL 연결 성공")
    except psycopg2.OperationalError as e:
        print(f"\n❌ Cloud SQL 연결 실패: {e}")
        print("\n💡 GCP 콘솔에서 방화벽 규칙 확인:")
        print("   Cloud SQL → 인스턴스 → 연결 → 승인된 네트워크")
        print("   로컬 PC의 공개 IP 추가 필요")
        print("   공개 IP 확인: https://www.whatismyip.com/")
        local_conn.close()
        return
    except Exception as e:
        print(f"\n❌ Cloud SQL 연결 실패: {e}")
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

