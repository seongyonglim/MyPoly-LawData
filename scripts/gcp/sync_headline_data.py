#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
localhost의 headline 데이터를 VM으로 동기화하는 스크립트
"""

import sys
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor, Json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# .env 파일 로드
if sys.platform == 'win32':
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_file):
        encodings = ['utf-8', 'utf-8-sig', 'cp949', 'latin-1']
        for encoding in encodings:
            try:
                with open(env_file, 'r', encoding=encoding) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key and value:
                                os.environ[key] = value
                break
            except (UnicodeDecodeError, Exception):
                continue
else:
    from dotenv import load_dotenv
    load_dotenv()

# 로컬 DB 설정
LOCAL_DB = {
    'host': os.environ.get('LOCAL_DB_HOST', 'localhost'),
    'database': os.environ.get('LOCAL_DB_NAME', 'mypoly_lawdata'),
    'user': os.environ.get('LOCAL_DB_USER', 'postgres'),
    'password': os.environ.get('LOCAL_DB_PASSWORD'),
    'port': int(os.environ.get('LOCAL_DB_PORT', '5432'))
}

# Cloud SQL 설정
CLOUD_DB = {
    'host': os.environ.get('CLOUD_DB_HOST'),
    'database': os.environ.get('CLOUD_DB_NAME', 'mypoly_lawdata'),
    'user': os.environ.get('CLOUD_DB_USER', 'postgres'),
    'password': os.environ.get('CLOUD_DB_PASSWORD'),
    'port': int(os.environ.get('CLOUD_DB_PORT', '5432'))
}

def main():
    print("=" * 80)
    print("headline 데이터 동기화 (localhost → VM)")
    print("=" * 80)
    
    # 로컬 DB 연결
    print("\n[1] localhost DB 연결 중...")
    try:
        local_conn = psycopg2.connect(**LOCAL_DB)
        local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ localhost DB 연결 성공")
    except Exception as e:
        print(f"❌ localhost DB 연결 실패: {e}")
        return
    
    # Cloud SQL 연결
    print("\n[2] VM (Cloud SQL) DB 연결 중...")
    if not CLOUD_DB['host'] or not CLOUD_DB['password']:
        print("❌ CLOUD_DB_HOST와 CLOUD_DB_PASSWORD 환경 변수가 필요합니다.")
        local_conn.close()
        return
    
    try:
        cloud_conn = psycopg2.connect(**CLOUD_DB)
        cloud_cur = cloud_conn.cursor(cursor_factory=RealDictCursor)
        print("✅ VM DB 연결 성공")
    except Exception as e:
        print(f"❌ VM DB 연결 실패: {e}")
        local_conn.close()
        return
    
    try:
        # headline 데이터가 있는 의안 조회
        print("\n[3] localhost에서 headline 데이터 조회 중...")
        local_cur.execute("""
            SELECT bill_id, headline, summary, categories, vote_for, vote_against, proc_stage_order
            FROM bills
            WHERE headline IS NOT NULL AND headline != ''
            ORDER BY bill_id
        """)
        bills_with_headline = local_cur.fetchall()
        print(f"✅ {len(bills_with_headline):,}건의 headline 데이터 발견")
        
        if len(bills_with_headline) == 0:
            print("⚠️ headline 데이터가 없습니다.")
            return
        
        # VM에 업데이트
        print("\n[4] VM에 headline 데이터 업데이트 중...")
        updated = 0
        error_count = 0
        
        for bill in bills_with_headline:
            try:
                # JSONB 필드 처리 (dict를 Json 객체로 변환)
                categories = Json(bill['categories']) if bill['categories'] else None
                vote_for = Json(bill['vote_for']) if bill['vote_for'] else None
                vote_against = Json(bill['vote_against']) if bill['vote_against'] else None
                
                cloud_cur.execute("""
                    UPDATE bills
                    SET headline = %s,
                        summary = %s,
                        categories = %s,
                        vote_for = %s,
                        vote_against = %s,
                        proc_stage_order = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE bill_id = %s
                """, (
                    bill['headline'],
                    bill['summary'],
                    categories,
                    vote_for,
                    vote_against,
                    bill['proc_stage_order'],
                    bill['bill_id']
                ))
                updated += 1
                
                if updated % 100 == 0:
                    cloud_conn.commit()
                    print(f"  진행 중... {updated:,}/{len(bills_with_headline):,}건 업데이트")
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # 처음 5개 오류만 출력
                    print(f"  ⚠️ {bill['bill_id']} 업데이트 실패: {e}")
                cloud_conn.rollback()
        
        cloud_conn.commit()
        
        print(f"\n✅ 완료: {updated:,}건 업데이트, {error_count}건 오류")
        
        # 확인
        print("\n[5] 업데이트 확인 중...")
        cloud_cur.execute("SELECT COUNT(*) as cnt FROM bills WHERE headline IS NOT NULL AND headline != ''")
        result = cloud_cur.fetchone()
        vm_count = result['cnt'] if isinstance(result, dict) else result[0]
        print(f"✅ VM headline 데이터: {vm_count:,}건")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        cloud_conn.rollback()
    
    finally:
        local_cur.close()
        local_conn.close()
        cloud_cur.close()
        cloud_conn.close()
    
    print("\n" + "=" * 80)
    print("✅ headline 데이터 동기화 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

