#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
로컬 DB에서 데이터를 읽어서 INSERT 문으로 변환
이 파일을 GCP 콘솔에서 가져오기
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

def escape_value(val):
    """SQL 값 이스케이프"""
    if val is None:
        return 'NULL'
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, bool):
        return 'TRUE' if val else 'FALSE'
    # 문자열
    val_str = str(val).replace("'", "''").replace('\\', '\\\\')
    return f"'{val_str}'"

def export_table_to_insert(table_name, output_file):
    """테이블을 INSERT 문으로 변환"""
    print(f"\n[{table_name}] 변환 중...")
    
    try:
        conn = psycopg2.connect(**LOCAL_DB)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 데이터 읽기
        cur.execute(f"SELECT * FROM {table_name}")
        rows = cur.fetchall()
        
        if not rows:
            print(f"  ⚠️ 데이터 없음")
            return
        
        print(f"  📊 총 {len(rows):,}건")
        
        # 컬럼 목록
        columns = list(rows[0].keys())
        columns_str = ', '.join(columns)
        
        # INSERT 문 생성
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"-- {table_name} 테이블 데이터\n")
            f.write(f"TRUNCATE TABLE {table_name} CASCADE;\n\n")
            
            batch_size = 1000
            for i in range(0, len(rows), batch_size):
                batch = rows[i:min(i+batch_size, len(rows))]
                
                f.write(f"INSERT INTO {table_name} ({columns_str}) VALUES\n")
                
                values_list = []
                for row in batch:
                    values = [escape_value(row[col]) for col in columns]
                    values_list.append(f"({', '.join(values)})")
                
                f.write(',\n'.join(values_list))
                f.write(';\n\n')
                
                print(f"  진행: {min(i+batch_size, len(rows)):,}/{len(rows):,}건", end='\r')
        
        print(f"\n  ✅ 완료: {output_file}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"  ❌ 오류: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("=" * 80)
    print("로컬 DB → INSERT 문 변환")
    print("=" * 80)
    
    # 테이블 목록
    tables = [
        'proc_stage_mapping',
        'assembly_members',
        'bills',
        'votes',
    ]
    
    # 단일 파일로 생성
    output_file = 'local_data_inserts.sql'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("-- 데이터 마이그레이션용 INSERT 문\n")
        f.write("-- 생성일: " + str(os.popen('date /t').read().strip() if sys.platform == 'win32' else 'date') + "\n\n")
    
    for table in tables:
        export_table_to_insert(table, output_file)
    
    # 파일 크기 확인
    file_size = os.path.getsize(output_file) / (1024 * 1024)
    print(f"\n파일 크기: {file_size:.2f} MB")
    print(f"파일 위치: {os.path.abspath(output_file)}")
    
    print("\n" + "=" * 80)
    print("완료!")
    print("=" * 80)
    print(f"\n이제 GCP 콘솔에서 {output_file} 파일을 가져오세요.")

if __name__ == '__main__':
    main()

