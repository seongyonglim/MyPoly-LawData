#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
로컬에서 실행하여 VM의 Cloud SQL Proxy를 통해 데이터 마이그레이션
SSH 터널링 사용
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
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

def migrate_table(local_cur, cloud_cur, table_name, cloud_conn):
    """테이블 데이터 마이그레이션"""
    print(f"\n[{table_name}] 마이그레이션 중...")
    
    try:
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
        
        # 기존 데이터 삭제
        try:
            cloud_cur.execute(f"TRUNCATE TABLE {table_name} CASCADE")
        except Exception as e:
            print(f"  ⚠️ TRUNCATE 실패 (무시): {e}")
            cloud_conn.rollback()
        
        # 배치로 데이터 삽입 (1000개씩)
        batch_size = 1000
        inserted = 0
        
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            values_list = []
            
            for row in batch:
                values = [row[col] for col in columns]
                values_list.append(values)
            
            try:
                execute_batch(
                    cloud_cur,
                    f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                    values_list,
                    page_size=batch_size
                )
                inserted += len(batch)
                print(f"  진행: {inserted:,}/{len(rows):,}건 ({inserted*100//len(rows)}%)", end='\r')
                cloud_conn.commit()
            except Exception as e:
                cloud_conn.rollback()
                print(f"\n  ⚠️ 배치 삽입 오류: {e}")
                # 개별 삽입 시도
                for row in batch:
                    values = [row[col] for col in columns]
                    try:
                        cloud_cur.execute(
                            f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                            values
                        )
                        inserted += 1
                        cloud_conn.commit()
                    except Exception as e2:
                        print(f"  ⚠️ 개별 삽입 오류 (건너뜀): {e2}")
                        cloud_conn.rollback()
        
        print(f"\n  ✅ {inserted:,}건 삽입 완료")
        
    except Exception as e:
        cloud_conn.rollback()
        print(f"  ❌ 오류: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("=" * 80)
    print("로컬 → Cloud SQL 데이터 마이그레이션 (SSH 터널링)")
    print("=" * 80)
    print("\n⚠️ 먼저 SSH 터널링을 설정하세요:")
    print("   새 PowerShell 창에서:")
    print("   ssh -L 5433:127.0.0.1:5432 seongyonglim3@34.64.212.103")
    print("   (그 창은 계속 열어두세요)")
    print("\n그 다음 이 스크립트를 실행하세요.")
    print("\n계속하시겠습니까? (y/n): ", end='')
    
    # 자동 진행
    # response = input().strip().lower()
    # if response != 'y':
    #     print("취소되었습니다.")
    #     return
    
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
    print(f"   호스트: {CLOUD_DB['host']}:{CLOUD_DB['port']} (SSH 터널)")
    try:
        cloud_conn = psycopg2.connect(**CLOUD_DB)
        cloud_cur = cloud_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ Cloud SQL 연결 성공")
    except Exception as e:
        print(f"❌ Cloud SQL 연결 실패: {e}")
        print("\n💡 SSH 터널링이 설정되어 있는지 확인하세요:")
        print("   ssh -L 5433:127.0.0.1:5432 seongyonglim3@34.64.212.103")
        local_conn.close()
        return
    
    # 마이그레이션할 테이블 목록 (순서 중요!)
    tables = [
        'proc_stage_mapping',
        'assembly_members',
        'bills',
        'votes',
    ]
    
    print("\n[3] 데이터 마이그레이션 시작...")
    print(f"마이그레이션할 테이블: {', '.join(tables)}")
    
    for table in tables:
        try:
            migrate_table(local_cur, cloud_cur, table, cloud_conn)
        except Exception as e:
            print(f"  ❌ 테이블 {table} 오류: {e}")
    
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

