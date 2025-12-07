#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
원문내용과 AI 헤드라인/요약 개수 비교
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

def get_db_config():
    """DB 설정 가져오기"""
    return {
        'host': os.environ.get('LOCAL_DB_HOST', 'localhost'),
        'database': os.environ.get('LOCAL_DB_NAME', 'mypoly_lawdata'),
        'user': os.environ.get('LOCAL_DB_USER', 'postgres'),
        'password': os.environ.get('LOCAL_DB_PASSWORD'),
        'port': int(os.environ.get('LOCAL_DB_PORT', '5432'))
    }

def main():
    print("=" * 80)
    print("원문내용 vs AI 헤드라인/요약 개수 비교")
    print("=" * 80)
    
    db_config = get_db_config()
    
    if not db_config['password']:
        print("❌ LOCAL_DB_PASSWORD 환경 변수가 필요합니다.")
        return
    
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        print("✅ DB 연결 성공\n")
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        return
    
    try:
        # 원문내용이 실제로 있는 개수 (NULL과 빈 문자열 제외)
        # headline과 summary는 TEXT 타입, categories/vote_for/vote_against는 JSONB 타입
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE summary_raw IS NOT NULL AND TRIM(summary_raw) != '') as has_summary,
                COUNT(*) FILTER (WHERE link_url IS NOT NULL AND TRIM(link_url) != '') as has_url,
                COUNT(*) FILTER (WHERE headline IS NOT NULL AND TRIM(headline) != '') as has_headline,
                COUNT(*) FILTER (WHERE summary IS NOT NULL AND TRIM(summary) != '') as has_ai_summary,
                COUNT(*) FILTER (WHERE categories IS NOT NULL AND categories != 'null'::jsonb AND categories != '{}'::jsonb) as has_categories
            FROM bills
            WHERE proposal_date >= '2025-01-01'
        """)
        
        result = cur.fetchone()
        
        print(f"[1] 전체 의안: {result['total']:,}건")
        print(f"[2] 원문내용 있음: {result['has_summary']:,}건 ({result['has_summary']/result['total']*100:.1f}%)")
        print(f"[3] 링크 URL 있음: {result['has_url']:,}건 ({result['has_url']/result['total']*100:.1f}%)")
        print(f"[4] AI 헤드라인 있음: {result['has_headline']:,}건 ({result['has_headline']/result['total']*100:.1f}%)")
        print(f"[5] AI 요약 있음: {result['has_ai_summary']:,}건 ({result['has_ai_summary']/result['total']*100:.1f}%)")
        print(f"[6] 카테고리 있음: {result['has_categories']:,}건 ({result['has_categories']/result['total']*100:.1f}%)")
        
        print("\n" + "=" * 80)
        print("비교 분석:")
        print("=" * 80)
        
        if result['has_summary'] == result['has_headline']:
            print("✅ 원문내용 개수와 AI 헤드라인 개수가 일치합니다!")
        else:
            diff = abs(result['has_summary'] - result['has_headline'])
            print(f"⚠️ 원문내용({result['has_summary']:,}건)과 AI 헤드라인({result['has_headline']:,}건) 개수가 다릅니다. (차이: {diff:,}건)")
        
        if result['has_summary'] == result['has_ai_summary']:
            print("✅ 원문내용 개수와 AI 요약 개수가 일치합니다!")
        else:
            diff = abs(result['has_summary'] - result['has_ai_summary'])
            print(f"⚠️ 원문내용({result['has_summary']:,}건)과 AI 요약({result['has_ai_summary']:,}건) 개수가 다릅니다. (차이: {diff:,}건)")
        
        # 원문내용은 있는데 AI 헤드라인이 없는 경우
        cur.execute("""
            SELECT COUNT(*) as cnt
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            AND summary_raw IS NOT NULL AND TRIM(summary_raw) != ''
            AND (headline IS NULL OR TRIM(headline) = '')
        """)
        missing_ai = cur.fetchone()['cnt']
        if missing_ai > 0:
            print(f"\n⚠️ 원문내용은 있지만 AI 헤드라인이 없는 의안: {missing_ai:,}건")
        
        # 원문내용이 없는데 AI 헤드라인이 있는 경우 (이상한 경우)
        cur.execute("""
            SELECT COUNT(*) as cnt
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            AND (summary_raw IS NULL OR TRIM(summary_raw) = '')
            AND headline IS NOT NULL AND TRIM(headline) != ''
        """)
        weird_case = cur.fetchone()['cnt']
        if weird_case > 0:
            print(f"⚠️ 원문내용은 없지만 AI 헤드라인이 있는 의안: {weird_case:,}건 (이상한 경우)")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cur.close()
        conn.close()
    
    print("\n" + "=" * 80)
    print("✅ 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

