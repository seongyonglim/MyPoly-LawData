#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
최종 전체 데이터 품질 점검 및 수정
- 모든 필드 수집 상태 확인
- 누락된 데이터 보완
- 데이터 무결성 검증
"""

import sys
import os
import re
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

def extract_proposer_from_title(title):
    """제목에서 제안자 이름 추출"""
    if not title:
        return None
    
    # 패턴 1: "법률안(홍길동의원 등 10인)"
    match = re.search(r'\(([^)]+의원)\s*등\s*\d+인\)', title)
    if match:
        name = match.group(1).replace('의원', '').strip()
        return name
    
    # 패턴 2: "법률안(홍길동의원)"
    match = re.search(r'\(([^)]+의원)\)', title)
    if match:
        name = match.group(1).replace('의원', '').strip()
        return name
    
    # 패턴 3: "법률안(홍길동 등 10인)"
    match = re.search(r'\(([^)]+)\s*등\s*\d+인\)', title)
    if match:
        name = match.group(1).strip()
        name = name.replace('의원', '').strip()
        return name
    
    return None

def extract_proposer_count(title):
    """제목에서 제안자 수 추출"""
    if not title:
        return 1
    
    match = re.search(r'등\s*(\d+)인', title)
    if match:
        try:
            return int(match.group(1))
        except:
            pass
    return 1

def final_comprehensive_fix():
    """최종 전체 데이터 품질 점검 및 수정"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("최종 전체 데이터 품질 점검 및 수정")
    print("=" * 80)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 제안자 이름 최종 보완
    print("[1] 제안자 이름 최종 보완")
    cur.execute("""
        SELECT bill_id, title, proposer_kind
        FROM bills
        WHERE proposal_date >= '2025-01-01'
        AND (proposer_name IS NULL OR proposer_name = '')
        AND proposer_kind = '의원'
    """)
    
    missing_bills = cur.fetchall()
    print(f"  처리할 의안: {len(missing_bills):,}건")
    
    updated = 0
    for bill in missing_bills:
        extracted_name = extract_proposer_from_title(bill['title'])
        if extracted_name:
            try:
                cur.execute("""
                    UPDATE bills
                    SET proposer_name = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE bill_id = %s
                """, (extracted_name, bill['bill_id']))
                if cur.rowcount > 0:
                    updated += 1
            except Exception as e:
                print(f"  ⚠️ 오류 (bill_id: {bill['bill_id'][:20]}...): {e}")
                conn.rollback()
                continue
    
    conn.commit()
    print(f"  ✅ {updated:,}건 업데이트 완료\n")
    
    # 2. 제안자 수 최종 보완
    print("[2] 제안자 수 최종 보완")
    cur.execute("""
        SELECT bill_id, title
        FROM bills
        WHERE proposal_date >= '2025-01-01'
        AND proposer_kind = '의원'
        AND (proposer_count IS NULL OR proposer_count = 1)
    """)
    
    bills = cur.fetchall()
    print(f"  처리할 의안: {len(bills):,}건")
    
    updated = 0
    for bill in bills:
        proposer_count = extract_proposer_count(bill['title'])
        if proposer_count and proposer_count > 1:
            try:
                cur.execute("""
                    UPDATE bills
                    SET proposer_count = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE bill_id = %s
                """, (proposer_count, bill['bill_id']))
                if cur.rowcount > 0:
                    updated += 1
            except Exception as e:
                print(f"  ⚠️ 오류 (bill_id: {bill['bill_id'][:20]}...): {e}")
                conn.rollback()
                continue
    
    conn.commit()
    print(f"  ✅ {updated:,}건 업데이트 완료\n")
    
    # 3. 최종 통계
    print("[3] 최종 데이터 품질 통계")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN proposer_name IS NOT NULL AND proposer_name != '' THEN 1 END) as has_proposer_name,
            COUNT(CASE WHEN proposer_count > 1 THEN 1 END) as has_proposer_count,
            COUNT(CASE WHEN summary_raw IS NOT NULL AND summary_raw != '' THEN 1 END) as has_summary,
            COUNT(CASE WHEN link_url IS NOT NULL AND link_url != '' THEN 1 END) as has_link
        FROM bills
        WHERE proposal_date >= '2025-01-01'
    """)
    
    stats = cur.fetchone()
    total = stats['total']
    
    print(f"전체 의안: {total:,}건\n")
    print(f"제안자 이름: {stats['has_proposer_name']:,}건 ({stats['has_proposer_name']/total*100:.1f}%)")
    print(f"제안자 수: {stats['has_proposer_count']:,}건 ({stats['has_proposer_count']/total*100:.1f}%)")
    print(f"원문내용: {stats['has_summary']:,}건 ({stats['has_summary']/total*100:.1f}%)")
    print(f"링크 URL: {stats['has_link']:,}건 ({stats['has_link']/total*100:.1f}%)")
    
    # 제안자 구분별 통계
    cur.execute("""
        SELECT 
            proposer_kind,
            COUNT(*) as total,
            COUNT(CASE WHEN proposer_name IS NOT NULL AND proposer_name != '' THEN 1 END) as has_name
        FROM bills
        WHERE proposal_date >= '2025-01-01'
        GROUP BY proposer_kind
        ORDER BY total DESC
    """)
    
    print("\n제안자 구분별 통계:")
    for row in cur.fetchall():
        kind = row['proposer_kind'] or '(NULL)'
        total_kind = row['total']
        has_name = row['has_name']
        rate = (has_name / total_kind * 100) if total_kind > 0 else 0
        print(f"  {kind}: {total_kind:,}건 (이름: {has_name:,}건, {rate:.1f}%)")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("작업 완료")
    print("=" * 80)
    print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    final_comprehensive_fix()

