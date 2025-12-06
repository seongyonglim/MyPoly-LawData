#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
전체 필드 수집 상태 점검 및 누락 필드 수정
"""

import sys
import os
import re
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

def extract_proposer_count(title):
    """제목에서 제안자 수 추출"""
    if not title:
        return None
    
    # 패턴: "등 10인", "등 11인" 등
    match = re.search(r'등\s*(\d+)인', title)
    if match:
        try:
            return int(match.group(1))
        except:
            pass
    return 1  # 기본값

def fix_all_missing_fields():
    """모든 누락 필드 수정"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("전체 필드 수집 상태 점검 및 수정")
    print("=" * 80)
    
    # 1. proposer_count 업데이트 (제목에서 추출)
    print("\n[1] proposer_count 업데이트 (제목에서 추출)")
    
    cur.execute("""
        SELECT bill_id, title
        FROM bills
        WHERE proposal_date >= '2025-01-01'
        AND (proposer_count IS NULL OR proposer_count = 1)
        AND proposer_kind = '의원'
    """)
    
    bills = cur.fetchall()
    print(f"  처리할 의안: {len(bills):,}건")
    
    updated_count = 0
    for bill in bills:
        bill_id = bill['bill_id']
        title = bill['title']
        proposer_count = extract_proposer_count(title)
        
        if proposer_count and proposer_count > 1:
            try:
                cur.execute("""
                    UPDATE bills
                    SET proposer_count = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE bill_id = %s
                """, (proposer_count, bill_id))
                
                if cur.rowcount > 0:
                    updated_count += 1
            except Exception as e:
                print(f"  ⚠️ 오류 (bill_id: {bill_id[:20]}...): {e}")
                conn.rollback()
                continue
    
    conn.commit()
    print(f"  ✅ {updated_count:,}건 업데이트 완료")
    
    # 2. 전체 필드 완성도 확인
    print("\n[2] 전체 필드 완성도 확인")
    
    fields_to_check = [
        ('bill_id', '의안ID'),
        ('bill_no', '의안번호'),
        ('title', '의안명'),
        ('proposal_date', '제안일'),
        ('proposer_kind', '제안자구분'),
        ('proposer_name', '제안자명'),
        ('proposer_count', '제안자 수'),
        ('proc_stage_cd', '진행단계'),
        ('pass_gubn', '처리구분'),
        ('proc_date', '처리일'),
        ('general_result', '일반결과'),
        ('summary_raw', '원문내용'),
        ('link_url', '링크 URL'),
    ]
    
    cur.execute("SELECT COUNT(*) as total FROM bills WHERE proposal_date >= '2025-01-01'")
    total = cur.fetchone()['total']
    
    print(f"\n전체 의안: {total:,}건\n")
    print(f"{'필드명':<25} {'한글명':<20} {'있음':<10} {'없음':<10} {'완성도':<10}")
    print("-" * 80)
    
    for field, label in fields_to_check:
        cur.execute(f"""
            SELECT 
                COUNT(CASE WHEN {field} IS NOT NULL AND {field}::text != '' THEN 1 END) as has_value
            FROM bills
            WHERE proposal_date >= '2025-01-01'
        """)
        has_value = cur.fetchone()['has_value']
        missing = total - has_value
        completion = (has_value / total * 100) if total > 0 else 0
        
        status = "✅" if completion >= 95 else "⚠️" if completion >= 50 else "❌"
        print(f"{field:<25} {label:<20} {has_value:<10,} {missing:<10,} {completion:>6.1f}% {status}")
    
    # 3. 제안자 정보 상세 확인
    print("\n[3] 제안자 정보 상세 확인")
    
    cur.execute("""
        SELECT 
            proposer_kind,
            COUNT(*) as total,
            COUNT(CASE WHEN proposer_name IS NOT NULL AND proposer_name != '' THEN 1 END) as has_name,
            COUNT(CASE WHEN proposer_count > 1 THEN 1 END) as has_count
        FROM bills
        WHERE proposal_date >= '2025-01-01'
        GROUP BY proposer_kind
        ORDER BY total DESC
    """)
    
    print(f"\n{'제안자구분':<15} {'전체':<10} {'이름있음':<10} {'수있음':<10} {'이름완성도':<12} {'수완성도':<12}")
    print("-" * 80)
    
    for row in cur.fetchall():
        kind = row['proposer_kind'] or '(NULL)'
        total = row['total']
        has_name = row['has_name']
        has_count = row['has_count']
        name_rate = (has_name / total * 100) if total > 0 else 0
        count_rate = (has_count / total * 100) if total > 0 else 0
        
        print(f"{kind:<15} {total:<10,} {has_name:<10,} {has_count:<10,} {name_rate:>10.1f}% {count_rate:>10.1f}%")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("점검 완료")
    print("=" * 80)

if __name__ == '__main__':
    fix_all_missing_fields()

