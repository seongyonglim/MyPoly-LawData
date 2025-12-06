#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
데이터 품질 종합 리포트 생성
디자이너/기획자용 데이터 상태 보고서
"""

import sys
import psycopg2
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
from dotenv import load_dotenv

load_dotenv()

def get_db_config():
    """환경 변수에서 데이터베이스 설정 가져오기"""
    config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD'),
        'port': int(os.environ.get('DB_PORT', '5432'))
    }
    
    if not config['password']:
        raise ValueError("DB_PASSWORD environment variable is required")
    
    return config

def generate_comprehensive_report():
    """종합 데이터 품질 리포트 생성"""
    config = get_db_config()
    conn = psycopg2.connect(**config)
    cur = conn.cursor()
    
    print("=" * 80)
    print("📊 데이터 품질 종합 리포트")
    print(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 1. 기본 통계
    print("\n## 1. 기본 데이터 통계")
    print("-" * 80)
    
    cur.execute("SELECT COUNT(*) FROM bills WHERE proposal_date >= '2025-01-01'")
    total_bills = cur.fetchone()[0]
    print(f"✅ 총 의안 수: {total_bills:,}건")
    
    cur.execute("SELECT COUNT(*) FROM assembly_members WHERE era LIKE '%22대%'")
    total_members = cur.fetchone()[0]
    print(f"✅ 22대 국회의원 수: {total_members:,}명")
    
    cur.execute("SELECT COUNT(*) FROM votes")
    total_votes = cur.fetchone()[0]
    print(f"✅ 총 표결 결과: {total_votes:,}건")
    
    cur.execute("""
        SELECT COUNT(DISTINCT bill_id) 
        FROM votes 
        WHERE bill_id IN (SELECT bill_id FROM bills WHERE proposal_date >= '2025-01-01')
    """)
    bills_with_votes = cur.fetchone()[0]
    print(f"✅ 표결 진행된 의안: {bills_with_votes:,}건 ({bills_with_votes*100/total_bills:.1f}%)")
    
    # 2. 데이터 완성도
    print("\n## 2. 데이터 완성도")
    print("-" * 80)
    
    # 제안자 정보
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN proposer_name IS NOT NULL AND proposer_name != '' THEN 1 END) as has_proposer_name,
            COUNT(CASE WHEN proposer_kind IS NOT NULL AND proposer_kind != '' THEN 1 END) as has_proposer_kind
        FROM bills
        WHERE proposal_date >= '2025-01-01'
    """)
    total, has_name, has_kind = cur.fetchone()
    print(f"📋 제안자 정보:")
    print(f"   - 제안자 이름 있음: {has_name:,}건 ({has_name*100/total:.1f}%)")
    print(f"   - 제안자 구분 있음: {has_kind:,}건 ({has_kind*100/total:.1f}%)")
    
    # 링크 URL
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN link_url IS NOT NULL AND link_url != '' THEN 1 END) as has_link
        FROM bills
        WHERE proposal_date >= '2025-01-01'
    """)
    total, has_link = cur.fetchone()
    print(f"🔗 의안 원문 링크:")
    print(f"   - 링크 있음: {has_link:,}건 ({has_link*100/total:.1f}%)")
    
    # 진행단계
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN proc_stage_cd IS NOT NULL AND proc_stage_cd != '' THEN 1 END) as has_stage
        FROM bills
        WHERE proposal_date >= '2025-01-01'
    """)
    total, has_stage = cur.fetchone()
    print(f"📊 진행단계 정보:")
    print(f"   - 진행단계 있음: {has_stage:,}건 ({has_stage*100/total:.1f}%)")
    
    # 처리일
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN proc_date IS NOT NULL THEN 1 END) as has_proc_date
        FROM bills
        WHERE proposal_date >= '2025-01-01' AND pass_gubn = '처리의안'
    """)
    result = cur.fetchone()
    if result and result[0] > 0:
        total, has_proc_date = result
        print(f"📅 처리일 정보 (처리의안만):")
        print(f"   - 처리일 있음: {has_proc_date:,}건 ({has_proc_date*100/total:.1f}%)")
    
    # 3. 매핑 품질
    print("\n## 3. 데이터 매핑 품질")
    print("-" * 80)
    
    # votes -> assembly_members 매핑
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN member_id IS NOT NULL AND member_id != '' THEN 1 END) as mapped
        FROM votes
    """)
    total, mapped = cur.fetchone()
    mapping_rate = (mapped / total * 100) if total > 0 else 0
    print(f"👥 의원 ID 매핑:")
    print(f"   - 매핑 완료: {mapped:,}건 ({mapping_rate:.1f}%)")
    print(f"   - 매핑 미완료: {total - mapped:,}건 ({100 - mapping_rate:.1f}%)")
    
    # votes -> bills 매핑
    cur.execute("""
        SELECT COUNT(*) 
        FROM votes v
        LEFT JOIN bills b ON v.bill_id = b.bill_id
        WHERE b.bill_id IS NULL
    """)
    orphan_votes = cur.fetchone()[0]
    print(f"📋 표결-의안 매핑:")
    print(f"   - 매핑 안 된 표결: {orphan_votes:,}건")
    
    # 4. 데이터 중복
    print("\n## 4. 데이터 중복 검사")
    print("-" * 80)
    
    cur.execute("""
        SELECT bill_id, COUNT(*) as cnt
        FROM bills
        GROUP BY bill_id
        HAVING COUNT(*) > 1
    """)
    duplicate_bills = cur.fetchall()
    print(f"📋 중복 의안: {len(duplicate_bills)}건")
    
    cur.execute("""
        SELECT bill_id, member_no, vote_date, COUNT(*) as cnt
        FROM votes
        GROUP BY bill_id, member_no, vote_date
        HAVING COUNT(*) > 1
    """)
    duplicate_votes = cur.fetchall()
    print(f"👥 중복 표결: {len(duplicate_votes):,}건")
    if len(duplicate_votes) > 0:
        print(f"   ⚠️ 중복 표결 데이터 정리 필요")
    
    # 5. 데이터 일관성
    print("\n## 5. 데이터 일관성")
    print("-" * 80)
    
    # 처리구분과 진행단계 일관성
    cur.execute("""
        SELECT 
            pass_gubn,
            proc_stage_cd,
            COUNT(*) as cnt
        FROM bills
        WHERE proposal_date >= '2025-01-01'
        GROUP BY pass_gubn, proc_stage_cd
        ORDER BY cnt DESC
        LIMIT 10
    """)
    consistency = cur.fetchall()
    print(f"📊 처리구분-진행단계 조합 (상위 10개):")
    for pass_gubn, stage, cnt in consistency:
        print(f"   - {pass_gubn} / {stage or 'NULL'}: {cnt:,}건")
    
    # 6. 개선 필요 사항
    print("\n## 6. 개선 필요 사항")
    print("-" * 80)
    
    issues = []
    
    # 제안자 정보 누락
    cur.execute("""
        SELECT COUNT(*) 
        FROM bills 
        WHERE proposal_date >= '2025-01-01' 
        AND (proposer_name IS NULL OR proposer_name = '')
    """)
    missing_proposer = cur.fetchone()[0]
    if missing_proposer > 0:
        issues.append(f"⚠️ 제안자 이름 누락: {missing_proposer:,}건")
    
    # 링크 누락
    cur.execute("""
        SELECT COUNT(*) 
        FROM bills 
        WHERE proposal_date >= '2025-01-01' 
        AND (link_url IS NULL OR link_url = '')
    """)
    missing_link = cur.fetchone()[0]
    if missing_link > 0:
        issues.append(f"⚠️ 의안 원문 링크 누락: {missing_link:,}건")
    
    # 진행단계 누락
    cur.execute("""
        SELECT COUNT(*) 
        FROM bills 
        WHERE proposal_date >= '2025-01-01' 
        AND (proc_stage_cd IS NULL OR proc_stage_cd = '')
    """)
    missing_stage = cur.fetchone()[0]
    if missing_stage > 0:
        issues.append(f"⚠️ 진행단계 정보 누락: {missing_stage:,}건")
    
    # 중복 표결
    if len(duplicate_votes) > 0:
        issues.append(f"⚠️ 중복 표결 데이터: {len(duplicate_votes):,}건 (정리 필요)")
    
    # 매핑 미완료
    if mapping_rate < 100:
        issues.append(f"⚠️ 의원 ID 매핑 미완료: {total - mapped:,}건 ({100 - mapping_rate:.1f}%)")
    
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("✅ 모든 데이터가 완벽합니다!")
    
    # 7. 데이터 품질 점수
    print("\n## 7. 데이터 품질 점수")
    print("-" * 80)
    
    score = 100
    deductions = []
    
    if missing_proposer > 0:
        deduction = min(10, (missing_proposer / total_bills) * 100)
        score -= deduction
        deductions.append(f"제안자 정보 누락: -{deduction:.1f}점")
    
    if missing_link > 0:
        deduction = min(5, (missing_link / total_bills) * 100)
        score -= deduction
        deductions.append(f"링크 누락: -{deduction:.1f}점")
    
    if missing_stage > 0:
        deduction = min(5, (missing_stage / total_bills) * 100)
        score -= deduction
        deductions.append(f"진행단계 누락: -{deduction:.1f}점")
    
    if len(duplicate_votes) > 0:
        deduction = min(10, (len(duplicate_votes) / total_votes) * 100)
        score -= deduction
        deductions.append(f"중복 데이터: -{deduction:.1f}점")
    
    if mapping_rate < 100:
        deduction = (100 - mapping_rate) * 0.1
        score -= deduction
        deductions.append(f"매핑 미완료: -{deduction:.1f}점")
    
    score = max(0, score)
    
    print(f"📊 종합 점수: {score:.1f}/100점")
    if deductions:
        print("\n감점 사항:")
        for deduction in deductions:
            print(f"   - {deduction}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("리포트 생성 완료!")
    print("=" * 80)

if __name__ == '__main__':
    generate_comprehensive_report()

