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
    """테이블 데이터 마이그레이션 (스트리밍 방식으로 최적화)"""
    print(f"\n[{table_name}] 마이그레이션 중...")
    
    try:
        # 먼저 총 행 수 확인
        print(f"  📊 데이터 개수 확인 중...", end='', flush=True)
        step_start = datetime.now()
        local_cur.execute(f"SELECT COUNT(*) as cnt FROM {table_name}")
        total_rows = local_cur.fetchone()['cnt']
        print(f" (완료, {datetime.now() - step_start}) - 총 {total_rows:,}건", flush=True)
        
        if total_rows == 0:
            print(f"  ⚠️ 데이터 없음 (건너뜀)")
            return
        
        # Cloud SQL 테이블 구조 확인
        print(f"  🔍 Cloud SQL 테이블 구조 확인 중...", end='', flush=True)
        step_start = datetime.now()
        cloud_columns = get_table_columns(cloud_cur, table_name)
        cloud_column_names = list(cloud_columns.keys())
        print(f" (완료, {datetime.now() - step_start})", flush=True)
        
        # 로컬 테이블의 첫 번째 행으로 컬럼 정보 확인
        print(f"  🔍 로컬 테이블 컬럼 확인 중...", end='', flush=True)
        step_start = datetime.now()
        local_cur.execute(f"SELECT * FROM {table_name} LIMIT 1")
        sample_row = local_cur.fetchone()
        if not sample_row:
            print(f" (데이터 없음)", flush=True)
            return
        columns = list(sample_row.keys())
        print(f" (완료, {datetime.now() - step_start})", flush=True)
        
        # 공통 컬럼만 사용
        common_columns = [col for col in columns if col in cloud_column_names]
        if not common_columns:
            print(f"  ⚠️ 공통 컬럼 없음 (건너뜀)")
            return
        
        columns_str = ', '.join(common_columns)
        placeholders = ', '.join(['%s'] * len(common_columns))
        
        # 스트리밍 방식으로 데이터 읽기 및 삽입
        print(f"  💾 데이터 삽입 시작 (스트리밍 방식)...")
        batch_size = 5000  # 배치 크기 증가
        commit_interval = 3  # 3개 배치마다 커밋
        local_cur.itersize = batch_size  # 서버 사이드 커서 크기 설정
        
        inserted = 0
        error_count = 0
        batch_count = 0
        start_time = datetime.now()
        
        # votes 테이블인 경우 외래키 제약조건 일시 비활성화
        if table_name == 'votes':
            print(f"  🔧 외래키 제약조건 일시 비활성화 중...", end='', flush=True)
            try:
                cloud_cur.execute("ALTER TABLE votes DISABLE TRIGGER ALL;")
                cloud_conn.commit()
                print(f" (완료)", flush=True)
            except Exception as e:
                print(f" (경고: {str(e)[:50]})", flush=True)
        
        # 스트리밍 방식으로 데이터 읽기
        print(f"  📖 쿼리 실행 중...", end='', flush=True)
        query_start = datetime.now()
        local_cur.execute(f"SELECT * FROM {table_name}")
        print(f" (완료, {datetime.now() - query_start})", flush=True)
        
        values_buffer = []  # 커밋 전 버퍼
        
        while True:
            print(f"  📥 배치 {batch_count + 1} 데이터 읽는 중...", end='', flush=True)
            fetch_start = datetime.now()
            batch = local_cur.fetchmany(batch_size)
            fetch_time = (datetime.now() - fetch_start).total_seconds()
            
            if not batch:
                print(f" (데이터 없음, {fetch_time:.2f}s)", flush=True)
                break
            
            batch_count += 1
            print(f" ({len(batch):,}건 읽음, {fetch_time:.2f}s)", flush=True)
            
            # 배치 데이터 준비
            print(f"    → 데이터 준비 중...", end='', flush=True)
            batch_prep_start = datetime.now()
            values_list = []
            for row in batch:
                values = []
                for col in common_columns:
                    val = row[col]
                    # 딕셔너리나 리스트는 JSON 문자열로 변환
                    if isinstance(val, (dict, list)):
                        import json
                        val = json.dumps(val, ensure_ascii=False)
                    values.append(val)
                values_list.append(tuple(values))  # 튜플로 변환
            prep_time = (datetime.now() - batch_prep_start).total_seconds()
            print(f" (완료, {prep_time:.2f}s)", flush=True)
            
            # 버퍼에 추가
            values_buffer.extend(values_list)
            
            # 배치 삽입 실행 (중복 키는 무시)
            print(f"    → Cloud SQL에 삽입 중...", end='', flush=True)
            batch_insert_start = datetime.now()
            try:
                # 중복 키가 있을 수 있으므로 ON CONFLICT DO NOTHING 사용
                # 단, primary key 컬럼이 있는 경우에만
                insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                
                # primary key 컬럼 찾기
                cloud_cur.execute(f"""
                    SELECT column_name 
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
                    WHERE tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY'
                    LIMIT 1
                """, (table_name,))
                pk_result = cloud_cur.fetchone()
                
                if pk_result:
                    pk_column = pk_result['column_name'] if isinstance(pk_result, dict) else pk_result[0]
                    if pk_column in common_columns:
                        # ON CONFLICT 사용
                        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT ({pk_column}) DO NOTHING"
                
                execute_batch(
                    cloud_cur,
                    insert_sql,
                    values_list,
                    page_size=batch_size
                )
                insert_time = (datetime.now() - batch_insert_start).total_seconds()
                inserted += len(batch)
                print(f" (완료, {insert_time:.2f}s)", flush=True)
                
                # 커밋 간격마다 커밋 (네트워크 오버헤드 감소)
                if batch_count % commit_interval == 0:
                    print(f"    → 커밋 중...", end='', flush=True)
                    commit_start = datetime.now()
                    cloud_conn.commit()
                    commit_time = (datetime.now() - commit_start).total_seconds()
                    values_buffer = []  # 버퍼 초기화
                    print(f" (완료, {commit_time:.2f}s)", flush=True)
                else:
                    commit_time = 0
                
                # 진행률 계산
                progress = (inserted * 100) // total_rows if total_rows > 0 else 0
                elapsed = (datetime.now() - start_time).total_seconds()
                speed = inserted / elapsed if elapsed > 0 else 0
                remaining = total_rows - inserted
                eta = remaining / speed if speed > 0 else 0
                
                # 진행 상황 요약
                print(f"  ✅ 배치 {batch_count} 완료: {inserted:,}/{total_rows:,}건 ({progress}%) | "
                      f"속도: {speed:,.0f}건/초 | 예상 남은 시간: {eta:.0f}초", flush=True)
                
            except Exception as e:
                cloud_conn.rollback()
                error_count += len(batch)
                error_msg = str(e)
                print(f"    ❌ 삽입 실패: {error_msg[:200]}", flush=True)
                print(f"  ⚠️ 배치 {batch_count} 전체 실패, 다음 배치로 진행...", flush=True)
                # 개별 삽입은 시도하지 않고 건너뜀 (너무 느림)
                # 필요시 수동으로 재시도
                continue
        
        # 남은 버퍼 커밋
        if values_buffer:
            print(f"  💾 남은 데이터 커밋 중...", end='', flush=True)
            try:
                cloud_conn.commit()
                print(f" (완료)", flush=True)
            except Exception as e:
                cloud_conn.rollback()
                print(f" (실패: {e})", flush=True)
        
        # votes 테이블인 경우 외래키 제약조건 재활성화
        if table_name == 'votes':
            print(f"  🔧 외래키 제약조건 재활성화 중...", end='', flush=True)
            try:
                cloud_cur.execute("ALTER TABLE votes ENABLE TRIGGER ALL;")
                cloud_conn.commit()
                print(f" (완료)", flush=True)
            except Exception as e:
                print(f" (경고: {str(e)[:50]})", flush=True)
        
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
    
    # 먼저 VM의 모든 기존 데이터를 완전히 삭제 (외래키 역순)
    print("\n[3] VM 기존 데이터 완전 삭제 중...")
    print("=" * 80)
    delete_tables = ['votes', 'bills', 'assembly_members', 'proc_stage_mapping']
    
    try:
        # 외래키 제약조건 일시 비활성화
        print("  🔧 외래키 제약조건 일시 비활성화 중...", end='', flush=True)
        try:
            cloud_cur.execute("SET session_replication_role = replica;")
            cloud_conn.commit()
            print(" (완료)", flush=True)
        except Exception as e:
            print(f" (경고: {str(e)[:50]})", flush=True)
            # 대안: 각 테이블의 트리거 비활성화
            try:
                cloud_cur.execute("ALTER TABLE votes DISABLE TRIGGER ALL;")
                cloud_cur.execute("ALTER TABLE bills DISABLE TRIGGER ALL;")
                cloud_conn.commit()
                print("  (트리거 비활성화 완료)", flush=True)
            except:
                pass
        
        # 역순으로 데이터 삭제 (외래키 고려)
        for table in delete_tables:
            print(f"  🗑️ {table} 테이블 데이터 삭제 중...", end='', flush=True)
            try:
                # 먼저 데이터 개수 확인
                cloud_cur.execute(f"SELECT COUNT(*) as cnt FROM {table}")
                count = cloud_cur.fetchone()['cnt']
                cloud_conn.commit()  # COUNT 쿼리 후 커밋
                
                if count > 0:
                    try:
                        cloud_cur.execute(f"TRUNCATE TABLE {table} CASCADE")
                        cloud_conn.commit()
                        print(f" (완료, {count:,}건 삭제)", flush=True)
                    except Exception as e_truncate:
                        cloud_conn.rollback()
                        # TRUNCATE 실패 시 DELETE 시도
                        try:
                            cloud_cur.execute(f"DELETE FROM {table}")
                            cloud_conn.commit()
                            print(f" (DELETE로 완료, {count:,}건 삭제)", flush=True)
                        except Exception as e_delete:
                            cloud_conn.rollback()
                            print(f" (경고: {str(e_delete)[:50]})", flush=True)
                else:
                    print(" (이미 비어있음)", flush=True)
            except Exception as e:
                cloud_conn.rollback()
                print(f" (오류: {str(e)[:50]})", flush=True)
        
        # 외래키 제약조건 재활성화
        print("  🔧 외래키 제약조건 재활성화 중...", end='', flush=True)
        try:
            cloud_conn.rollback()  # 이전 트랜잭션 정리
            try:
                cloud_cur.execute("SET session_replication_role = DEFAULT;")
                cloud_conn.commit()
            except:
                cloud_conn.rollback()
            try:
                cloud_cur.execute("ALTER TABLE votes ENABLE TRIGGER ALL;")
                cloud_conn.commit()
            except:
                cloud_conn.rollback()
            try:
                cloud_cur.execute("ALTER TABLE bills ENABLE TRIGGER ALL;")
                cloud_conn.commit()
            except:
                cloud_conn.rollback()
            print(" (완료)", flush=True)
        except Exception as e:
            cloud_conn.rollback()
            print(f" (경고: {str(e)[:50]})", flush=True)
    except Exception as e:
        print(f"  ⚠️ 데이터 삭제 중 오류 발생: {e}")
        cloud_conn.rollback()
        print("  (계속 진행합니다...)")
    
    print("\n[4] 데이터 마이그레이션 시작...")
    print("=" * 80)
    overall_start_time = datetime.now()
    
    for idx, table in enumerate(tables, 1):
        print(f"\n[{idx}/{len(tables)}] {table} 테이블 처리 중...")
        try:
            migrate_table(local_cur, cloud_cur, cloud_conn, table)
        except Exception as e:
            print(f"  ❌ 테이블 {table} 오류: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    
    overall_elapsed = datetime.now() - overall_start_time
    
    # 연결 종료
    local_cur.close()
    local_conn.close()
    cloud_cur.close()
    cloud_conn.close()
    
    print("\n" + "=" * 80)
    print(f"✅ 마이그레이션 완료!")
    print(f"   총 소요 시간: {overall_elapsed}")
    print(f"   평균 처리 속도: {overall_elapsed.total_seconds() / len(tables):.2f}초/테이블")
    print("=" * 80)

if __name__ == '__main__':
    main()

