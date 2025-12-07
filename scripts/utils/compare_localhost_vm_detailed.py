#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
localhost와 VM의 데이터를 상세하게 비교
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
    """localhost DB 설정"""
    return {
        'host': os.environ.get('LOCAL_DB_HOST', 'localhost'),
        'database': os.environ.get('LOCAL_DB_NAME', 'mypoly_lawdata'),
        'user': os.environ.get('LOCAL_DB_USER', 'postgres'),
        'password': os.environ.get('LOCAL_DB_PASSWORD'),
        'port': int(os.environ.get('LOCAL_DB_PORT', '5432'))
    }

def get_vm_db_config():
    """VM DB 설정"""
    return {
        'host': os.environ.get('CLOUD_DB_HOST'),
        'database': os.environ.get('CLOUD_DB_NAME', 'mypoly_lawdata'),
        'user': os.environ.get('CLOUD_DB_USER', 'postgres'),
        'password': os.environ.get('CLOUD_DB_PASSWORD'),
        'port': int(os.environ.get('CLOUD_DB_PORT', '5432'))
    }

def main():
    print("=" * 80)
    print("localhost vs VM 상세 데이터 비교")
    print("=" * 80)
    
    local_config = get_local_db_config()
    vm_config = get_vm_db_config()
    
    if not local_config['password']:
        print("❌ LOCAL_DB_PASSWORD 환경 변수가 필요합니다.")
        return
    
    if not vm_config['host'] or not vm_config['password']:
        print("❌ CLOUD_DB_HOST와 CLOUD_DB_PASSWORD 환경 변수가 필요합니다.")
        return
    
    try:
        local_conn = psycopg2.connect(**local_config)
        local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ localhost DB 연결 성공")
    except Exception as e:
        print(f"❌ localhost DB 연결 실패: {e}")
        return
    
    try:
        vm_conn = psycopg2.connect(**vm_config)
        vm_cur = vm_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ VM DB 연결 성공\n")
    except Exception as e:
        print(f"❌ VM DB 연결 실패: {e}")
        local_cur.close()
        local_conn.close()
        return
    
    try:
        # 1. 테이블별 데이터 개수 비교
        print("[1] 테이블별 데이터 개수 비교:")
        print("=" * 80)
        
        tables = ['bills', 'votes', 'assembly_members', 'proc_stage_mapping']
        
        for table in tables:
            local_cur.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            local_count = local_cur.fetchone()['cnt']
            
            vm_cur.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            vm_count = vm_cur.fetchone()['cnt']
            
            status = "✅" if local_count == vm_count else "❌"
            diff = abs(local_count - vm_count)
            print(f"  {status} {table:25s} localhost: {local_count:>8,}건  VM: {vm_count:>8,}건  차이: {diff:>6,}건")
        
        # 2. bills 테이블 상세 비교
        print("\n[2] bills 테이블 상세 비교:")
        print("=" * 80)
        
        # 2025년 데이터만
        local_cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE proposal_date >= '2025-01-01') as after_2025,
                COUNT(*) FILTER (WHERE link_url IS NOT NULL AND TRIM(link_url) != '') as has_url,
                COUNT(*) FILTER (WHERE proposer_name IS NOT NULL AND TRIM(proposer_name) != '' AND proposer_name != '의원') as has_name,
                COUNT(*) FILTER (WHERE headline IS NOT NULL AND TRIM(headline) != '') as has_headline
            FROM bills
        """)
        local_bills = local_cur.fetchone()
        
        vm_cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE proposal_date >= '2025-01-01') as after_2025,
                COUNT(*) FILTER (WHERE link_url IS NOT NULL AND TRIM(link_url) != '') as has_url,
                COUNT(*) FILTER (WHERE proposer_name IS NOT NULL AND TRIM(proposer_name) != '' AND proposer_name != '의원') as has_name,
                COUNT(*) FILTER (WHERE headline IS NOT NULL AND TRIM(headline) != '') as has_headline
            FROM bills
        """)
        vm_bills = vm_cur.fetchone()
        
        print(f"  전체 의안:")
        print(f"    localhost: {local_bills['total']:,}건")
        print(f"    VM:        {vm_bills['total']:,}건")
        print(f"    차이:      {abs(local_bills['total'] - vm_bills['total']):,}건")
        
        print(f"\n  2025년 이후 의안:")
        print(f"    localhost: {local_bills['after_2025']:,}건")
        print(f"    VM:        {vm_bills['after_2025']:,}건")
        print(f"    차이:      {abs(local_bills['after_2025'] - vm_bills['after_2025']):,}건")
        
        print(f"\n  link_url:")
        print(f"    localhost: {local_bills['has_url']:,}건 ({local_bills['has_url']/local_bills['after_2025']*100:.1f}%)")
        print(f"    VM:        {vm_bills['has_url']:,}건 ({vm_bills['has_url']/vm_bills['after_2025']*100:.1f}%)")
        
        print(f"\n  proposer_name:")
        print(f"    localhost: {local_bills['has_name']:,}건 ({local_bills['has_name']/local_bills['after_2025']*100:.1f}%)")
        print(f"    VM:        {vm_bills['has_name']:,}건 ({vm_bills['has_name']/vm_bills['after_2025']*100:.1f}%)")
        
        print(f"\n  headline:")
        print(f"    localhost: {local_bills['has_headline']:,}건 ({local_bills['has_headline']/local_bills['after_2025']*100:.1f}%)")
        print(f"    VM:        {vm_bills['has_headline']:,}건 ({vm_bills['has_headline']/vm_bills['after_2025']*100:.1f}%)")
        
        # 3. votes 테이블 상세 비교
        print("\n[3] votes 테이블 상세 비교:")
        print("=" * 80)
        
        local_cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT bill_id) as distinct_bills,
                COUNT(DISTINCT member_no) as distinct_members,
                MIN(vote_date) as min_date,
                MAX(vote_date) as max_date
            FROM votes
        """)
        local_votes = local_cur.fetchone()
        
        vm_cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT bill_id) as distinct_bills,
                COUNT(DISTINCT member_no) as distinct_members,
                MIN(vote_date) as min_date,
                MAX(vote_date) as max_date
            FROM votes
        """)
        vm_votes = vm_cur.fetchone()
        
        print(f"  전체 표결:")
        print(f"    localhost: {local_votes['total']:,}건")
        print(f"    VM:        {vm_votes['total']:,}건")
        
        print(f"\n  고유 의안 수:")
        print(f"    localhost: {local_votes['distinct_bills']:,}건")
        print(f"    VM:        {vm_votes['distinct_bills']:,}건")
        
        print(f"\n  고유 의원 수:")
        print(f"    localhost: {local_votes['distinct_members']:,}건")
        print(f"    VM:        {vm_votes['distinct_members']:,}건")
        
        print(f"\n  표결일 범위:")
        print(f"    localhost: {local_votes['min_date']} ~ {local_votes['max_date']}")
        print(f"    VM:        {vm_votes['min_date']} ~ {vm_votes['max_date']}")
        
        # 4. bills 테이블에서 다른 데이터 찾기
        print("\n[4] bills 테이블에서 다른 데이터 찾기:")
        print("=" * 80)
        
        # localhost에만 있는 bill_id
        local_cur.execute("""
            SELECT bill_id FROM bills 
            WHERE proposal_date >= '2025-01-01'
            EXCEPT
            SELECT bill_id FROM bills WHERE proposal_date >= '2025-01-01'
        """)
        # 이건 의미없으니 다른 방법 사용
        
        # 샘플 데이터 비교
        local_cur.execute("""
            SELECT bill_id, bill_no, title, proposer_name, link_url, headline IS NOT NULL AND TRIM(headline) != '' as has_headline
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            ORDER BY bill_id
            LIMIT 10
        """)
        local_samples = local_cur.fetchall()
        
        vm_cur.execute("""
            SELECT bill_id, bill_no, title, proposer_name, link_url, headline IS NOT NULL AND TRIM(headline) != '' as has_headline
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            ORDER BY bill_id
            LIMIT 10
        """)
        vm_samples = vm_cur.fetchall()
        
        print("  샘플 비교 (처음 10개):")
        for i, (local, vm) in enumerate(zip(local_samples, vm_samples), 1):
            if local['bill_id'] != vm['bill_id']:
                print(f"    {i}. ❌ bill_id가 다름: local={local['bill_id']}, vm={vm['bill_id']}")
            elif local['proposer_name'] != vm['proposer_name']:
                print(f"    {i}. ❌ proposer_name이 다름: {local['bill_id']}")
                print(f"         local: {local['proposer_name']}")
                print(f"         VM:   {vm['proposer_name']}")
            elif local['link_url'] != vm['link_url']:
                print(f"    {i}. ❌ link_url이 다름: {local['bill_id']}")
            elif local['has_headline'] != vm['has_headline']:
                print(f"    {i}. ❌ headline이 다름: {local['bill_id']}")
            else:
                print(f"    {i}. ✅ {local['bill_id']}: {local['title'][:50]}...")
        
        # 5. localhost에만 있는 bill_id 찾기
        print("\n[5] localhost에만 있는 bill_id 찾기:")
        print("=" * 80)
        
        local_cur.execute("SELECT bill_id FROM bills WHERE proposal_date >= '2025-01-01'")
        local_bill_ids = set(row['bill_id'] for row in local_cur.fetchall())
        
        vm_cur.execute("SELECT bill_id FROM bills WHERE proposal_date >= '2025-01-01'")
        vm_bill_ids = set(row['bill_id'] for row in vm_cur.fetchall())
        
        only_local = local_bill_ids - vm_bill_ids
        only_vm = vm_bill_ids - local_bill_ids
        
        if only_local:
            print(f"  localhost에만 있는 bill_id: {len(only_local)}건")
            for bill_id in list(only_local)[:10]:
                print(f"    - {bill_id}")
            if len(only_local) > 10:
                print(f"    ... 외 {len(only_local) - 10}건")
        else:
            print("  ✅ localhost에만 있는 bill_id 없음")
        
        if only_vm:
            print(f"\n  VM에만 있는 bill_id: {len(only_vm)}건")
            for bill_id in list(only_vm)[:10]:
                print(f"    - {bill_id}")
            if len(only_vm) > 10:
                print(f"    ... 외 {len(only_vm) - 10}건")
        else:
            print("  ✅ VM에만 있는 bill_id 없음")
        
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

