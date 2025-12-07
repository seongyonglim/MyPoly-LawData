#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
원문내용(summary_raw) 필드 차이 확인
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

def get_local_db_config():
    return {
        'host': os.environ.get('LOCAL_DB_HOST', 'localhost'),
        'database': os.environ.get('LOCAL_DB_NAME', 'mypoly_lawdata'),
        'user': os.environ.get('LOCAL_DB_USER', 'postgres'),
        'password': os.environ.get('LOCAL_DB_PASSWORD'),
        'port': int(os.environ.get('LOCAL_DB_PORT', '5432'))
    }

def get_vm_db_config():
    return {
        'host': os.environ.get('CLOUD_DB_HOST'),
        'database': os.environ.get('CLOUD_DB_NAME', 'mypoly_lawdata'),
        'user': os.environ.get('CLOUD_DB_USER', 'postgres'),
        'password': os.environ.get('CLOUD_DB_PASSWORD'),
        'port': int(os.environ.get('CLOUD_DB_PORT', '5432'))
    }

def main():
    print("=" * 80)
    print("원문내용(summary_raw) 필드 차이 확인")
    print("=" * 80)
    
    local_config = get_local_db_config()
    vm_config = get_vm_db_config()
    
    local_conn = psycopg2.connect(**local_config)
    local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
    
    vm_conn = psycopg2.connect(**vm_config)
    vm_cur = vm_conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # localhost 원문내용 통계
        print("\n[1] localhost 원문내용 통계:")
        local_cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE summary_raw IS NOT NULL) as not_null,
                COUNT(*) FILTER (WHERE summary_raw IS NOT NULL AND TRIM(summary_raw) != '') as not_empty,
                COUNT(*) FILTER (WHERE summary_raw IS NULL) as is_null,
                COUNT(*) FILTER (WHERE summary_raw IS NOT NULL AND TRIM(summary_raw) = '') as is_empty
            FROM bills
            WHERE proposal_date >= '2025-01-01'
        """)
        local_stats = local_cur.fetchone()
        
        print(f"  전체: {local_stats['total']:,}건")
        print(f"  NULL이 아닌 것: {local_stats['not_null']:,}건")
        print(f"  빈 문자열이 아닌 것: {local_stats['not_empty']:,}건 ({local_stats['not_empty']/local_stats['total']*100:.1f}%)")
        print(f"  NULL인 것: {local_stats['is_null']:,}건")
        print(f"  빈 문자열인 것: {local_stats['is_empty']:,}건")
        
        # VM 원문내용 통계
        print("\n[2] VM 원문내용 통계:")
        vm_cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE summary_raw IS NOT NULL) as not_null,
                COUNT(*) FILTER (WHERE summary_raw IS NOT NULL AND TRIM(summary_raw) != '') as not_empty,
                COUNT(*) FILTER (WHERE summary_raw IS NULL) as is_null,
                COUNT(*) FILTER (WHERE summary_raw IS NOT NULL AND TRIM(summary_raw) = '') as is_empty
            FROM bills
            WHERE proposal_date >= '2025-01-01'
        """)
        vm_stats = vm_cur.fetchone()
        
        print(f"  전체: {vm_stats['total']:,}건")
        print(f"  NULL이 아닌 것: {vm_stats['not_null']:,}건")
        print(f"  빈 문자열이 아닌 것: {vm_stats['not_empty']:,}건 ({vm_stats['not_empty']/vm_stats['total']*100:.1f}%)")
        print(f"  NULL인 것: {vm_stats['is_null']:,}건")
        print(f"  빈 문자열인 것: {vm_stats['is_empty']:,}건")
        
        # 차이점 확인
        print("\n[3] 차이점:")
        print("=" * 80)
        
        if local_stats['not_empty'] != vm_stats['not_empty']:
            print(f"  ❌ 빈 문자열이 아닌 것 차이: {abs(local_stats['not_empty'] - vm_stats['not_empty']):,}건")
            
            # localhost에만 있는 것 (빈 문자열이 아닌데 VM은 NULL이거나 빈 문자열)
            local_cur.execute("""
                SELECT bill_id, bill_no, title, 
                       CASE WHEN summary_raw IS NULL THEN 'NULL' 
                            WHEN TRIM(summary_raw) = '' THEN 'EMPTY'
                            ELSE 'HAS_DATA' END as local_status
                FROM bills
                WHERE proposal_date >= '2025-01-01'
                AND summary_raw IS NOT NULL AND TRIM(summary_raw) != ''
            """)
            local_with_data = {row['bill_id']: row for row in local_cur.fetchall()}
            
            vm_cur.execute("""
                SELECT bill_id,
                       CASE WHEN summary_raw IS NULL THEN 'NULL' 
                            WHEN TRIM(summary_raw) = '' THEN 'EMPTY'
                            ELSE 'HAS_DATA' END as vm_status
                FROM bills
                WHERE proposal_date >= '2025-01-01'
            """)
            vm_statuses = {row['bill_id']: row['vm_status'] for row in vm_cur.fetchall()}
            
            different = []
            for bill_id, local_row in local_with_data.items():
                if bill_id not in vm_statuses:
                    different.append({'bill_id': bill_id, 'issue': 'VM에 없음', 'local': local_row})
                elif vm_statuses[bill_id] != 'HAS_DATA':
                    different.append({
                        'bill_id': bill_id, 
                        'issue': f'VM은 {vm_statuses[bill_id]}',
                        'local': local_row
                    })
            
            if different:
                print(f"\n  차이가 있는 의안: {len(different)}건")
                for i, diff in enumerate(different[:20], 1):
                    print(f"    {i}. [{diff['bill_id']}] {diff['local']['title'][:50]}...")
                    print(f"       local: HAS_DATA, VM: {diff['issue']}")
                if len(different) > 20:
                    print(f"    ... 외 {len(different) - 20}건")
        else:
            print("  ✅ 빈 문자열이 아닌 것 개수 일치")
        
        # VM에만 있는 것 (빈 문자열이 아닌데 localhost는 NULL이거나 빈 문자열)
        vm_cur.execute("""
            SELECT bill_id, bill_no, title,
                   CASE WHEN summary_raw IS NULL THEN 'NULL' 
                        WHEN TRIM(summary_raw) = '' THEN 'EMPTY'
                        ELSE 'HAS_DATA' END as vm_status
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            AND summary_raw IS NOT NULL AND TRIM(summary_raw) != ''
        """)
        vm_with_data = {row['bill_id']: row for row in vm_cur.fetchall()}
        
        local_cur.execute("""
            SELECT bill_id,
                   CASE WHEN summary_raw IS NULL THEN 'NULL' 
                        WHEN TRIM(summary_raw) = '' THEN 'EMPTY'
                        ELSE 'HAS_DATA' END as local_status
            FROM bills
            WHERE proposal_date >= '2025-01-01'
        """)
        local_statuses = {row['bill_id']: row['local_status'] for row in local_cur.fetchall()}
        
        vm_only = []
        for bill_id, vm_row in vm_with_data.items():
            if bill_id not in local_statuses:
                vm_only.append({'bill_id': bill_id, 'issue': 'localhost에 없음', 'vm': vm_row})
            elif local_statuses[bill_id] != 'HAS_DATA':
                vm_only.append({
                    'bill_id': bill_id,
                    'issue': f'localhost는 {local_statuses[bill_id]}',
                    'vm': vm_row
                })
        
        if vm_only:
            print(f"\n  VM에만 있는 것: {len(vm_only)}건")
            for i, diff in enumerate(vm_only[:20], 1):
                print(f"    {i}. [{diff['bill_id']}] {diff['vm']['title'][:50]}...")
                print(f"       VM: HAS_DATA, localhost: {diff['issue']}")
            if len(vm_only) > 20:
                print(f"    ... 외 {len(vm_only) - 20}건")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        local_cur.close()
        local_conn.close()
        vm_cur.close()
        vm_conn.close()
    
    print("\n" + "=" * 80)
    print("✅ 확인 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

