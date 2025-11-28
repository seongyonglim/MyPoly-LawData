#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSV 파일을 Cloud SQL로 가져오기 (간단 버전)
VM에서 실행
"""

import sys
import csv
import psycopg2
from psycopg2.extras import execute_batch, RealDictCursor
import io

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Cloud SQL 설정
CLOUD_DB = {
    'host': '127.0.0.1',
    'database': 'mypoly_lawdata',
    'user': 'postgres',
    'password': 'Mypoly!2025',
    'port': 5432
}

def import_csv(csv_file, table_name):
    """CSV 파일을 테이블로 가져오기"""
    print(f"\n[{table_name}] 가져오기 중...")
    
    try:
        conn = psycopg2.connect(**CLOUD_DB)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 기존 데이터 삭제
        cur.execute(f"TRUNCATE TABLE {table_name} CASCADE")
        conn.commit()
        print("  기존 데이터 삭제 완료")
        
        # CSV 파일 읽기 (여러 인코딩 시도)
        data = None
        for encoding in ['utf-8-sig', 'utf-8', 'cp949', 'latin-1']:
            try:
                with open(csv_file, 'r', encoding=encoding, errors='replace') as f:
                    data = list(csv.DictReader(f))
                print(f"  인코딩: {encoding}")
                break
            except:
                continue
        
        if not data:
            print("  ❌ CSV 파일을 읽을 수 없습니다")
            return
        
        if not data:
            print("  ⚠️ 데이터 없음")
            return
        
        print(f"  총 {len(data):,}건")
        
        # 컬럼 목록
        columns = list(data[0].keys())
        print(f"  컬럼: {len(columns)}개")
        
        # 배치 삽입
        batch_size = 1000
        inserted = 0
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            values_list = []
            
            for row in batch:
                values = []
                for col in columns:
                    val = row.get(col)
                    if val is None or val == '':
                        values.append(None)
                    else:
                        # 문자열 정리
                        val = str(val).strip()
                        if val == '':
                            values.append(None)
                        else:
                            values.append(val)
                values_list.append(values)
            
            try:
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join(columns)
                execute_batch(
                    cur,
                    f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                    values_list,
                    page_size=batch_size
                )
                inserted += len(batch)
                print(f"  진행: {inserted:,}/{len(data):,}건 ({inserted*100//len(data)}%)", end='\r')
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"\n  ⚠️ 배치 오류: {e}")
                # 개별 삽입 시도
                for row in batch:
                    values = []
                    for col in columns:
                        val = row.get(col)
                        if val is None or val == '':
                            values.append(None)
                        else:
                            val = str(val).strip()
                            values.append(val if val else None)
                    try:
                        placeholders = ', '.join(['%s'] * len(columns))
                        columns_str = ', '.join(columns)
                        cur.execute(
                            f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                            values
                        )
                        inserted += 1
                        conn.commit()
                    except Exception as e2:
                        print(f"  ⚠️ 개별 오류 (건너뜀): {e2}")
                        conn.rollback()
        
        # 확인
        cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        count = cur.fetchone()['count']
        
        print(f"\n  ✅ 완료: {inserted:,}건 삽입, {count:,}건 확인")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"  ❌ 오류: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("=" * 80)
    print("CSV 파일을 Cloud SQL로 가져오기")
    print("=" * 80)
    
    # 테이블 순서대로 (외래키 고려)
    tables = [
        ('proc_stage_mapping.csv', 'proc_stage_mapping'),
        ('assembly_members.csv', 'assembly_members'),
        ('bills.csv', 'bills'),
        ('votes.csv', 'votes'),
    ]
    
    for csv_file, table_name in tables:
        import_csv(csv_file, table_name)
    
    print("\n" + "=" * 80)
    print("완료!")
    print("=" * 80)

if __name__ == '__main__':
    main()

