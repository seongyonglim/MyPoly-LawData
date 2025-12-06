#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
전체 데이터 품질 점검 및 수정 스크립트
- 링크 URL 생성 및 업데이트
- 의원 정보 매핑 수정
- 데이터 무결성 검증
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()

def get_db_connection():
    """데이터베이스 연결 생성"""
    try:
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_name = os.environ.get('DB_NAME', 'mypoly_lawdata')
        db_user = os.environ.get('DB_USER', 'postgres')
        db_password = os.environ.get('DB_PASSWORD')
        if not db_password:
            raise ValueError("DB_PASSWORD environment variable is required")
        db_port = int(os.environ.get('DB_PORT', '5432'))
        
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        return conn
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        raise

def generate_bill_link(bill_id):
    """의안 링크 생성"""
    if bill_id:
        return f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
    return None

def fix_link_urls(conn):
    """링크 URL 생성 및 업데이트"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n" + "=" * 80)
    print("1. 링크 URL 생성 및 업데이트")
    print("=" * 80)
    
    # link_url이 없는 의안들 조회
    cur.execute("""
        SELECT bill_id, bill_no
        FROM bills
        WHERE proposal_date >= '2025-01-01'
        AND (link_url IS NULL OR link_url = '')
    """)
    
    bills = cur.fetchall()
    print(f"\n처리할 의안 수: {len(bills):,}건")
    
    updated_count = 0
    for bill in bills:
        bill_id = bill['bill_id']
        link_url = generate_bill_link(bill_id)
        
        if link_url:
            try:
                cur.execute("""
                    UPDATE bills
                    SET link_url = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE bill_id = %s
                """, (link_url, bill_id))
                
                if cur.rowcount > 0:
                    updated_count += 1
            except Exception as e:
                print(f"  ⚠️ 오류 (bill_id: {bill_id[:20]}...): {e}")
                conn.rollback()
                continue
    
    conn.commit()
    print(f"✅ {updated_count:,}건 업데이트 완료")
    
    # 최종 통계
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN link_url IS NOT NULL AND link_url != '' THEN 1 END) as with_link
        FROM bills
        WHERE proposal_date >= '2025-01-01'
    """)
    
    result = cur.fetchone()
    total = result['total']
    with_link = result['with_link']
    print(f"\n최종 통계:")
    print(f"  전체 의안: {total:,}건")
    print(f"  link_url 있는 의안: {with_link:,}건 ({with_link/total*100:.1f}%)")
    
    cur.close()

def fix_member_mapping(conn):
    """의원 정보 매핑 수정"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n" + "=" * 80)
    print("2. 의원 정보 매핑 수정")
    print("=" * 80)
    
    # 2-1. votes 테이블에서 member_no/mona_cd로 assembly_members 매핑
    print("\n[2-1] votes → assembly_members 매핑")
    
    # votes에 있는 member_no/mona_cd로 assembly_members의 member_id 찾기
    cur.execute("""
        SELECT DISTINCT
            v.member_no,
            v.mona_cd,
            v.member_name,
            am.member_id
        FROM votes v
        LEFT JOIN assembly_members am ON (
            (v.member_no IS NOT NULL AND am.member_no = v.member_no) OR
            (v.mona_cd IS NOT NULL AND am.mona_cd = v.mona_cd)
        )
        WHERE v.member_id IS NULL
        AND (v.member_no IS NOT NULL OR v.mona_cd IS NOT NULL)
        LIMIT 1000
    """)
    
    unmapped_votes = cur.fetchall()
    print(f"  매핑되지 않은 표결: {len(unmapped_votes):,}건")
    
    updated_votes = 0
    for vote in unmapped_votes:
        member_id = vote['member_id']
        member_no = vote['member_no']
        mona_cd = vote['mona_cd']
        
        if member_id:
            # member_id가 있으면 votes 테이블 업데이트
            try:
                cur.execute("""
                    UPDATE votes
                    SET member_id = %s
                    WHERE member_no = %s
                    AND member_id IS NULL
                """, (member_id, member_no))
                
                if cur.rowcount > 0:
                    updated_votes += cur.rowcount
            except Exception as e:
                print(f"  ⚠️ 오류 (member_no: {member_no}): {e}")
                conn.rollback()
                continue
    
    conn.commit()
    print(f"  ✅ {updated_votes:,}건의 표결에 member_id 매핑 완료")
    
    # 2-2. assembly_members에 mona_cd, member_no 업데이트
    print("\n[2-2] assembly_members에 mona_cd, member_no 업데이트")
    
    cur.execute("""
        SELECT DISTINCT ON (v.member_name, v.party_name)
            v.member_name,
            v.party_name,
            v.member_no,
            v.mona_cd,
            am.member_id
        FROM votes v
        LEFT JOIN assembly_members am ON am.name = v.member_name
        WHERE (v.member_no IS NOT NULL OR v.mona_cd IS NOT NULL)
        AND am.member_id IS NOT NULL
        ORDER BY v.member_name, v.party_name, v.vote_date DESC
    """)
    
    member_mappings = cur.fetchall()
    print(f"  처리할 의원 매핑: {len(member_mappings):,}건")
    
    updated_members = 0
    for mapping in member_mappings:
        member_id = mapping['member_id']
        member_no = mapping['member_no']
        mona_cd = mapping['mona_cd']
        
        if not member_id:
            continue
        
        update_fields = []
        update_values = []
        
        if member_no:
            update_fields.append("member_no = %s")
            update_values.append(member_no)
        
        if mona_cd:
            update_fields.append("mona_cd = %s")
            update_values.append(mona_cd)
        
        if update_fields:
            update_values.append(member_id)
            try:
                cur.execute(f"""
                    UPDATE assembly_members
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE member_id = %s
                    AND (member_no IS NULL OR mona_cd IS NULL)
                """, update_values)
                
                if cur.rowcount > 0:
                    updated_members += 1
            except Exception as e:
                print(f"  ⚠️ 오류 (member_id: {member_id}): {e}")
                conn.rollback()
                continue
    
    conn.commit()
    print(f"  ✅ {updated_members:,}건의 의원 정보 업데이트 완료")
    
    # 2-3. 최종 매핑 통계
    print("\n[2-3] 최종 매핑 통계")
    
    cur.execute("""
        SELECT 
            COUNT(*) as total_votes,
            COUNT(member_id) as mapped_votes,
            COUNT(*) - COUNT(member_id) as unmapped_votes
        FROM votes
    """)
    
    vote_stats = cur.fetchone()
    total_votes = vote_stats['total_votes']
    mapped_votes = vote_stats['mapped_votes']
    unmapped_votes = vote_stats['unmapped_votes']
    
    print(f"  전체 표결: {total_votes:,}건")
    if total_votes > 0:
        print(f"  매핑된 표결: {mapped_votes:,}건 ({mapped_votes/total_votes*100:.1f}%)")
        print(f"  미매핑 표결: {unmapped_votes:,}건 ({unmapped_votes/total_votes*100:.1f}%)")
    else:
        print("  매핑된 표결: 0건")
        print("  미매핑 표결: 0건")
    
    cur.execute("""
        SELECT 
            COUNT(*) as total_members,
            COUNT(member_no) as has_member_no,
            COUNT(mona_cd) as has_mona_cd
        FROM assembly_members
    """)
    
    member_stats = cur.fetchone()
    total_members = member_stats['total_members']
    has_member_no = member_stats['has_member_no']
    has_mona_cd = member_stats['has_mona_cd']
    
    print(f"\n  전체 의원: {total_members:,}명")
    if total_members > 0:
        print(f"  member_no 있음: {has_member_no:,}명 ({has_member_no/total_members*100:.1f}%)")
        print(f"  mona_cd 있음: {has_mona_cd:,}명 ({has_mona_cd/total_members*100:.1f}%)")
    else:
        print("  member_no 있음: 0명")
        print("  mona_cd 있음: 0명")
    
    cur.close()

def validate_data_integrity(conn):
    """데이터 무결성 검증"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n" + "=" * 80)
    print("3. 데이터 무결성 검증")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # 3-1. bills 테이블 검증
    print("\n[3-1] bills 테이블 검증")
    
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN bill_id IS NULL THEN 1 END) as null_bill_id,
            COUNT(CASE WHEN bill_no IS NULL THEN 1 END) as null_bill_no,
            COUNT(CASE WHEN title IS NULL OR title = '' THEN 1 END) as null_title,
            COUNT(CASE WHEN proposal_date IS NULL THEN 1 END) as null_proposal_date
        FROM bills
        WHERE proposal_date >= '2025-01-01'
    """)
    
    bill_stats = cur.fetchone()
    print(f"  전체 의안: {bill_stats['total']:,}건")
    
    if bill_stats['null_bill_id'] > 0:
        errors.append(f"bills 테이블에 bill_id가 NULL인 행이 {bill_stats['null_bill_id']:,}건 있습니다")
    else:
        print("  ✅ bill_id: 모두 존재")
    
    if bill_stats['null_bill_no'] > 0:
        warnings.append(f"bills 테이블에 bill_no가 NULL인 행이 {bill_stats['null_bill_no']:,}건 있습니다")
    else:
        print("  ✅ bill_no: 모두 존재")
    
    if bill_stats['null_title'] > 0:
        warnings.append(f"bills 테이블에 title이 NULL인 행이 {bill_stats['null_title']:,}건 있습니다")
    else:
        print("  ✅ title: 모두 존재")
    
    # 3-2. votes 테이블 검증
    print("\n[3-2] votes 테이블 검증")
    
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN bill_id IS NULL THEN 1 END) as null_bill_id,
            COUNT(CASE WHEN member_no IS NULL AND mona_cd IS NULL THEN 1 END) as null_member_info
        FROM votes
        WHERE vote_date >= '2025-01-01'
    """)
    
    vote_stats = cur.fetchone()
    print(f"  전체 표결: {vote_stats['total']:,}건")
    
    if vote_stats['null_bill_id'] > 0:
        errors.append(f"votes 테이블에 bill_id가 NULL인 행이 {vote_stats['null_bill_id']:,}건 있습니다")
    else:
        print("  ✅ bill_id: 모두 존재")
    
    if vote_stats['null_member_info'] > 0:
        warnings.append(f"votes 테이블에 member_no와 mona_cd가 모두 NULL인 행이 {vote_stats['null_member_info']:,}건 있습니다")
    else:
        print("  ✅ member_no 또는 mona_cd: 모두 존재")
    
    # 3-3. 외래키 무결성 검증
    print("\n[3-3] 외래키 무결성 검증")
    
    cur.execute("""
        SELECT COUNT(*) as count
        FROM votes v
        WHERE v.bill_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM bills b WHERE b.bill_id = v.bill_id
        )
    """)
    
    orphan_votes = cur.fetchone()['count']
    if orphan_votes > 0:
        errors.append(f"votes 테이블에 bills 테이블에 없는 bill_id를 참조하는 행이 {orphan_votes:,}건 있습니다")
    else:
        print("  ✅ votes.bill_id → bills.bill_id: 모든 참조가 유효함")
    
    cur.execute("""
        SELECT COUNT(*) as count
        FROM votes v
        WHERE v.member_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM assembly_members am WHERE am.member_id = v.member_id
        )
    """)
    
    orphan_member_votes = cur.fetchone()['count']
    if orphan_member_votes > 0:
        warnings.append(f"votes 테이블에 assembly_members 테이블에 없는 member_id를 참조하는 행이 {orphan_member_votes:,}건 있습니다")
    else:
        print("  ✅ votes.member_id → assembly_members.member_id: 모든 참조가 유효함")
    
    # 결과 출력
    print("\n" + "=" * 80)
    print("검증 결과")
    print("=" * 80)
    
    if errors:
        print("\n❌ 오류:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ 오류 없음")
    
    if warnings:
        print("\n⚠️ 경고:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("\n✅ 경고 없음")
    
    cur.close()
    
    return len(errors) == 0

def main():
    """메인 함수"""
    print("=" * 80)
    print("전체 데이터 품질 점검 및 수정")
    print("=" * 80)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn = get_db_connection()
    
    try:
        # 1. 링크 URL 수정
        fix_link_urls(conn)
        
        # 2. 의원 매핑 수정
        fix_member_mapping(conn)
        
        # 3. 데이터 무결성 검증
        is_valid = validate_data_integrity(conn)
        
        print("\n" + "=" * 80)
        print("작업 완료")
        print("=" * 80)
        print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if is_valid:
            print("\n✅ 모든 데이터가 정상적으로 검증되었습니다!")
        else:
            print("\n⚠️ 일부 데이터에 문제가 있습니다. 위의 오류 메시지를 확인하세요.")
    
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    main()

