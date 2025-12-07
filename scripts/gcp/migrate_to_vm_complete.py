#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VM으로 데이터 완전 이관 스크립트
1. 최신 코드 pull 확인
2. 데이터 이관
3. link_url 및 proposer_name 업데이트
4. 최종 확인
"""

import sys
import os
import subprocess
import psycopg2
from psycopg2.extras import RealDictCursor
import re

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
    """VM DB 설정 (migrate_direct_public_ip.py와 동일한 환경 변수 사용)"""
    return {
        'host': os.environ.get('CLOUD_DB_HOST'),
        'database': os.environ.get('CLOUD_DB_NAME', 'mypoly_lawdata'),
        'user': os.environ.get('CLOUD_DB_USER', 'postgres'),
        'password': os.environ.get('CLOUD_DB_PASSWORD'),
        'port': int(os.environ.get('CLOUD_DB_PORT', '5432'))
    }

def extract_proposer_name_from_title(title):
    """의안 제목에서 제안자 이름 추출"""
    if not title:
        return ""
    
    match = re.search(r'\(([^)]+)\)', title)
    if not match:
        return ""
    
    proposer_text = match.group(1)
    proposer_match = re.search(r'([가-힣]+)의원', proposer_text)
    if proposer_match:
        return proposer_match.group(1)
    
    return proposer_text.strip()

def main():
    print("=" * 80)
    print("VM으로 데이터 완전 이관")
    print("=" * 80)
    
    # 1. Git pull 확인
    print("\n[1] Git 상태 확인 중...")
    try:
        result = subprocess.run(['git', 'status'], capture_output=True, text=True, encoding='utf-8')
        if 'Your branch is behind' in result.stdout:
            print("⚠️ 최신 코드가 아닙니다. 'git pull origin main'을 실행하세요.")
        else:
            print("✅ Git 상태 확인 완료")
    except Exception as e:
        print(f"⚠️ Git 확인 실패: {e}")
    
    # 2. DB 연결 확인
    print("\n[2] DB 연결 확인 중...")
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
        print("✅ VM DB 연결 성공")
    except Exception as e:
        print(f"❌ VM DB 연결 실패: {e}")
        local_cur.close()
        local_conn.close()
        return
    
    try:
        # 3. 데이터 이관 (migrate_direct_public_ip.py 실행)
        print("\n[3] 데이터 이관 시작...")
        print("   (migrate_direct_public_ip.py를 별도로 실행하세요)")
        print("   python scripts/gcp/migrate_direct_public_ip.py")
        
        # 4. link_url 업데이트
        print("\n[4] VM의 link_url 업데이트 중...")
        vm_cur.execute("""
            SELECT bill_id, link_url
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            AND (link_url IS NULL OR TRIM(link_url) = '')
        """)
        
        bills_to_update = vm_cur.fetchall()
        print(f"   업데이트 대상: {len(bills_to_update):,}건")
        
        if bills_to_update:
            updated = 0
            for bill in bills_to_update:
                bill_id = bill['bill_id']
                if bill_id:
                    link_url = f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
                    vm_cur.execute("""
                        UPDATE bills
                        SET link_url = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE bill_id = %s
                    """, (link_url, bill_id))
                    updated += 1
                    
                    if updated % 1000 == 0:
                        vm_conn.commit()
                        print(f"   진행 중... {updated:,}/{len(bills_to_update):,}건")
            
            vm_conn.commit()
            print(f"   ✅ link_url 업데이트 완료: {updated:,}건")
        else:
            print("   ✅ link_url 업데이트 불필요 (이미 완료)")
        
        # 5. proposer_name 업데이트
        print("\n[5] VM의 proposer_name 업데이트 중...")
        vm_cur.execute("""
            SELECT bill_id, title, proposer_name
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            AND (proposer_name IS NULL OR TRIM(proposer_name) = '' OR proposer_name = '의원')
        """)
        
        bills_to_update = vm_cur.fetchall()
        print(f"   업데이트 대상: {len(bills_to_update):,}건")
        
        if bills_to_update:
            updated = 0
            skipped = 0
            for bill in bills_to_update:
                bill_id = bill['bill_id']
                title = bill['title']
                
                if not title:
                    skipped += 1
                    continue
                
                proposer_name = extract_proposer_name_from_title(title)
                
                if proposer_name:
                    vm_cur.execute("""
                        UPDATE bills
                        SET proposer_name = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE bill_id = %s
                    """, (proposer_name, bill_id))
                    updated += 1
                else:
                    skipped += 1
                
                if (updated + skipped) % 1000 == 0:
                    vm_conn.commit()
                    print(f"   진행 중... {updated + skipped:,}/{len(bills_to_update):,}건 처리")
            
            vm_conn.commit()
            print(f"   ✅ proposer_name 업데이트 완료: {updated:,}건, 건너뜀: {skipped:,}건")
        else:
            print("   ✅ proposer_name 업데이트 불필요 (이미 완료)")
        
        # 6. 최종 확인
        print("\n[6] 최종 확인 중...")
        
        # localhost 데이터 개수
        local_cur.execute("SELECT COUNT(*) as cnt FROM bills WHERE proposal_date >= '2025-01-01'")
        local_bills = local_cur.fetchone()['cnt']
        
        local_cur.execute("SELECT COUNT(*) as cnt FROM votes")
        local_votes = local_cur.fetchone()['cnt']
        
        # VM 데이터 개수
        vm_cur.execute("SELECT COUNT(*) as cnt FROM bills WHERE proposal_date >= '2025-01-01'")
        vm_bills = vm_cur.fetchone()['cnt']
        
        vm_cur.execute("SELECT COUNT(*) as cnt FROM votes")
        vm_votes = vm_cur.fetchone()['cnt']
        
        print(f"\n   localhost:")
        print(f"     bills: {local_bills:,}건")
        print(f"     votes: {local_votes:,}건")
        
        print(f"\n   VM:")
        print(f"     bills: {vm_bills:,}건")
        print(f"     votes: {vm_votes:,}건")
        
        if local_bills == vm_bills and local_votes == vm_votes:
            print("\n   ✅ 데이터가 일치합니다!")
        else:
            print("\n   ⚠️ 데이터가 일치하지 않습니다.")
            if local_bills != vm_bills:
                print(f"     bills 차이: {abs(local_bills - vm_bills):,}건")
            if local_votes != vm_votes:
                print(f"     votes 차이: {abs(local_votes - vm_votes):,}건")
        
        # link_url 및 proposer_name 확인
        vm_cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE link_url IS NOT NULL AND TRIM(link_url) != '') as has_url,
                COUNT(*) FILTER (WHERE proposer_name IS NOT NULL AND TRIM(proposer_name) != '' AND proposer_name != '의원') as has_name
            FROM bills
            WHERE proposal_date >= '2025-01-01'
        """)
        
        result = vm_cur.fetchone()
        print(f"\n   VM 데이터 품질:")
        print(f"     link_url: {result['has_url']:,}/{result['total']:,} ({result['has_url']/result['total']*100:.1f}%)")
        print(f"     proposer_name: {result['has_name']:,}/{result['total']:,} ({result['has_name']/result['total']*100:.1f}%)")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        vm_conn.rollback()
    
    finally:
        local_cur.close()
        local_conn.close()
        vm_cur.close()
        vm_conn.close()
    
    print("\n" + "=" * 80)
    print("✅ 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

