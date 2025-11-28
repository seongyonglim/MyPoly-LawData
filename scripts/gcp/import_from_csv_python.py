#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSV 파일을 읽어서 Cloud SQL에 직접 삽입 (Python으로)
인코딩 문제 완전 해결
"""

import sys
import csv
import psycopg2
from psycopg2.extras import execute_batch, RealDictCursor
import os

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Cloud SQL 설정
CLOUD_DB = {
    'host': '127.0.0.1',  # Cloud SQL Proxy
    'database': 'mypoly_lawdata',
    'user': 'postgres',
    'password': 'Mypoly!2025',
    'port': 5432
}

def import_csv_to_table(csv_file, table_name, cloud_conn, cloud_cur):
    """CSV 파일을 테이블로 가져오기"""
    print(f"\n[{table_name}] 가져오기 중...")
    
    if not os.path.exists(csv_file):
        print(f"  ⚠️ 파일 없음: {csv_file}")
        return
    
    # 파일 크기
    file_size = os.path.getsize(csv_file) / (1024 * 1024)
    print(f"  파일 크기: {file_size:.2f} MB")
    
    # 기존 데이터 삭제
    try:
        cloud_cur.execute(f"TRUNCATE TABLE {table_name} CASCADE")
        print("  기존 데이터 삭제 완료")
    except Exception as e:
        print(f"  ⚠️ TRUNCATE 실패: {e}")
    
    # CSV 파일 읽기
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:  # BOM 자동 제거
            reader = csv.DictReader(f)
            
            # 컬럼 목록
            columns = reader.fieldnames
            if not columns:
                print("  ❌ CSV 헤더가 없습니다")
                return
            
            print(f"  컬럼: {', '.join(columns)}")
            
            # 데이터 읽기 및 삽입
            batch = []
            batch_size = 1000
            inserted = 0
            errors = 0
            
            for row in reader:
                # 빈 값 처리
                values = []
                for col in columns:
                    val = row.get(col, '')
                    if val is None:
                        values.append(None)
                    else:
                        val = str(val).strip()
                        if val == '':
                            values.append(None)
                        else:
                            values.append(val)
                
                batch.append(values)
                
                # 배치 삽입
                if len(batch) >= batch_size:
                    try:
                        placeholders = ', '.join(['%s'] * len(columns))
                        columns_str = ', '.join(columns)
                        execute_batch(
                            cloud_cur,
                            f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                            batch,
                            page_size=batch_size
                        )
                        inserted += len(batch)
                        print(f"  진행: {inserted:,}건", end='\r')
                        batch = []
                    except Exception as e:
                        errors += len(batch)
                        print(f"\n  ⚠️ 배치 오류: {e}")
                        batch = []
            
            # 남은 데이터 삽입
            if batch:
                try:
                    placeholders = ', '.join(['%s'] * len(columns))
                    columns_str = ', '.join(columns)
                    execute_batch(
                        cloud_cur,
                        f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                        batch,
                        page_size=len(batch)
                    )
                    inserted += len(batch)
                except Exception as e:
                    errors += len(batch)
                    print(f"\n  ⚠️ 마지막 배치 오류: {e}")
            
            cloud_conn.commit()
            
            # 최종 확인
            cloud_cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count = cloud_cur.fetchone()['count']
            
            print(f"\n  ✅ 완료: {inserted:,}건 삽입, {count:,}건 확인")
            if errors > 0:
                print(f"  ⚠️ 오류: {errors}건")
                
    except Exception as e:
        cloud_conn.rollback()
        print(f"  ❌ 오류: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("=" * 80)
    print("CSV 파일을 Cloud SQL로 가져오기 (Python)")
    print("=" * 80)
    
    # Cloud SQL 연결
    print("\n[1] Cloud SQL 연결 중...")
    try:
        cloud_conn = psycopg2.connect(**CLOUD_DB)
        cloud_cur = cloud_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ Cloud SQL 연결 성공")
    except Exception as e:
        print(f"❌ Cloud SQL 연결 실패: {e}")
        return
    
    # CSV 파일 목록
    csv_files = [
        ('proc_stage_mapping.csv', 'proc_stage_mapping'),
        ('assembly_members.csv', 'assembly_members'),
        ('bills.csv', 'bills'),
        ('votes.csv', 'votes'),
    ]
    
    print("\n[2] CSV 파일 가져오기 시작...")
    
    for csv_file, table_name in csv_files:
        try:
            import_csv_to_table(csv_file, table_name, cloud_conn, cloud_cur)
        except Exception as e:
            print(f"  ❌ 테이블 {table_name} 오류: {e}")
    
    # 연결 종료
    cloud_cur.close()
    cloud_conn.close()
    
    print("\n" + "=" * 80)
    print("모든 CSV 파일 가져오기 완료!")
    print("=" * 80)

if __name__ == '__main__':
    main()

