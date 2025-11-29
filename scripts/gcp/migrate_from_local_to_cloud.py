#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
로컬 PC에서 실행: 로컬 DB에서 데이터를 읽어서 Cloud SQL에 삽입
SSH 터널링을 통해 Cloud SQL Proxy에 연결
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

# 로컬 DB 설정
LOCAL_DB = {
    'host': 'localhost',
    'database': 'mypoly_lawdata',
    'user': 'postgres',
    'password': 'maza_970816',
    'port': 5432
}

# Cloud SQL 설정 (SSH 터널링을 통해)
# 로컬에서: ssh -L 5433:127.0.0.1:5432 seongyonglim3@34.64.212.103
# 그 다음 127.0.0.1:5433로 연결
CLOUD_DB = {
    'host': '127.0.0.1',
    'database': 'mypoly_lawdata',
    'user': 'postgres',
    'password': 'Mypoly!2025',
    'port': 5433  # SSH 터널 포트
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
    print("로컬 DB → Cloud SQL 데이터 마이그레이션 (로컬 PC에서 실행)")
    print("=" * 80)
    print("\n⚠️ 사전 준비:")
    print("1. PowerShell에서 SSH 터널 생성:")
    print("   ssh -N -L 5433:127.0.0.1:5432 seongyonglim3@34.64.212.103")
    print("2. 터널 창은 계속 열어두세요")
    print("3. 이 스크립트를 새 터미널에서 실행하세요")
    print("=" * 80)
    
    # 로컬 DB 연결
    print(f"\n[1] 로컬 DB 연결 중... (localhost:5432)")
    try:
        local_conn = psycopg2.connect(**LOCAL_DB)
        local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ 로컬 DB 연결 성공")
    except Exception as e:
        print(f"❌ 로컬 DB 연결 실패: {e}")
        return
    
    # Cloud SQL 연결 (SSH 터널을 통해)
    print("\n[2] Cloud SQL 연결 중... (127.0.0.1:5433 via SSH Tunnel)")
    try:
        cloud_conn = psycopg2.connect(**CLOUD_DB)
        cloud_cur = cloud_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ Cloud SQL 연결 성공")
    except Exception as e:
        print(f"❌ Cloud SQL 연결 실패: {e}")
        print("\n💡 SSH 터널이 실행 중인지 확인하세요:")
        print("   ssh -N -L 5433:127.0.0.1:5432 seongyonglim3@34.64.212.103")
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

