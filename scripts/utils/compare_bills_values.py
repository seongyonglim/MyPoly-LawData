#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
bills 테이블의 실제 값들을 비교
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
    print("bills 테이블 실제 값 비교")
    print("=" * 80)
    
    local_config = get_local_db_config()
    vm_config = get_vm_db_config()
    
    local_conn = psycopg2.connect(**local_config)
    local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
    
    vm_conn = psycopg2.connect(**vm_config)
    vm_cur = vm_conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 모든 bills의 주요 필드 비교
        print("\n[1] 모든 bills의 주요 필드 비교 중...")
        
        local_cur.execute("""
            SELECT bill_id, bill_no, title, proposer_name, link_url, 
                   headline IS NOT NULL AND TRIM(headline) != '' as has_headline,
                   summary IS NOT NULL AND TRIM(summary) != '' as has_summary
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            ORDER BY bill_id
        """)
        local_bills = {row['bill_id']: row for row in local_cur.fetchall()}
        
        vm_cur.execute("""
            SELECT bill_id, bill_no, title, proposer_name, link_url,
                   headline IS NOT NULL AND TRIM(headline) != '' as has_headline,
                   summary IS NOT NULL AND TRIM(summary) != '' as has_summary
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            ORDER BY bill_id
        """)
        vm_bills = {row['bill_id']: row for row in vm_cur.fetchall()}
        
        differences = []
        
        for bill_id in local_bills.keys():
            if bill_id not in vm_bills:
                differences.append({
                    'bill_id': bill_id,
                    'issue': 'VM에 없음',
                    'local': local_bills[bill_id],
                    'vm': None
                })
                continue
            
            local = local_bills[bill_id]
            vm = vm_bills[bill_id]
            
            if local['proposer_name'] != vm['proposer_name']:
                differences.append({
                    'bill_id': bill_id,
                    'issue': 'proposer_name 다름',
                    'local': local['proposer_name'],
                    'vm': vm['proposer_name']
                })
            
            if local['link_url'] != vm['link_url']:
                differences.append({
                    'bill_id': bill_id,
                    'issue': 'link_url 다름',
                    'local': local['link_url'][:50] if local['link_url'] else None,
                    'vm': vm['link_url'][:50] if vm['link_url'] else None
                })
            
            if local['has_headline'] != vm['has_headline']:
                differences.append({
                    'bill_id': bill_id,
                    'issue': 'headline 존재 여부 다름',
                    'local': local['has_headline'],
                    'vm': vm['has_headline']
                })
        
        if differences:
            print(f"\n❌ 차이점 발견: {len(differences)}건")
            for i, diff in enumerate(differences[:20], 1):
                print(f"\n  {i}. {diff['bill_id']}: {diff['issue']}")
                print(f"     local: {diff['local']}")
                print(f"     VM:   {diff['vm']}")
            if len(differences) > 20:
                print(f"\n  ... 외 {len(differences) - 20}건")
        else:
            print("✅ 모든 bills 데이터가 일치합니다!")
        
        # 2. votes 테이블에서 다른 데이터 찾기
        print("\n[2] votes 테이블에서 다른 데이터 찾기...")
        
        local_cur.execute("""
            SELECT bill_id, member_no, vote_date, vote_result, COUNT(*) as cnt
            FROM votes
            GROUP BY bill_id, member_no, vote_date, vote_result
        """)
        local_votes = {(row['bill_id'], row['member_no'], row['vote_date'], row['vote_result']): row['cnt'] 
                       for row in local_cur.fetchall()}
        
        vm_cur.execute("""
            SELECT bill_id, member_no, vote_date, vote_result, COUNT(*) as cnt
            FROM votes
            GROUP BY bill_id, member_no, vote_date, vote_result
        """)
        vm_votes = {(row['bill_id'], row['member_no'], row['vote_date'], row['vote_result']): row['cnt'] 
                    for row in vm_cur.fetchall()}
        
        only_local = set(local_votes.keys()) - set(vm_votes.keys())
        only_vm = set(vm_votes.keys()) - set(local_votes.keys())
        different_counts = []
        
        for key in set(local_votes.keys()) & set(vm_votes.keys()):
            if local_votes[key] != vm_votes[key]:
                different_counts.append({
                    'key': key,
                    'local': local_votes[key],
                    'vm': vm_votes[key]
                })
        
        if only_local:
            print(f"  ❌ localhost에만 있는 votes: {len(only_local)}건")
            for key in list(only_local)[:5]:
                print(f"    {key}")
        
        if only_vm:
            print(f"  ❌ VM에만 있는 votes: {len(only_vm)}건")
            for key in list(only_vm)[:5]:
                print(f"    {key}")
        
        if different_counts:
            print(f"  ❌ 개수가 다른 votes: {len(different_counts)}건")
            for diff in different_counts[:5]:
                print(f"    {diff['key']}: local={diff['local']}, vm={diff['vm']}")
        
        if not only_local and not only_vm and not different_counts:
            print("  ✅ votes 데이터가 일치합니다!")
        
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
    print("✅ 비교 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

