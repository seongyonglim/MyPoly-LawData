#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VM의 bills 테이블 proc_stage_order 업데이트
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

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

# VM DB 설정
VM_DB = {
    'host': os.environ.get('CLOUD_DB_HOST'),
    'database': os.environ.get('CLOUD_DB_NAME', 'mypoly_lawdata'),
    'user': os.environ.get('CLOUD_DB_USER', 'postgres'),
    'password': os.environ.get('CLOUD_DB_PASSWORD'),
    'port': int(os.environ.get('CLOUD_DB_PORT', '5432'))
}

def calculate_proc_stage_order(proc_stage_cd):
    """proc_stage_cd를 기반으로 proc_stage_order 계산"""
    if not proc_stage_cd:
        return None
    
    proc_stage_cd = proc_stage_cd.strip()
    
    # 접수 관련
    if '접수' in proc_stage_cd:
        return 1
    
    # 심사 관련
    if '심사' in proc_stage_cd:
        return 2
    
    # 본회의 관련
    if '본회의' in proc_stage_cd:
        return 3
    
    # 처리완료 관련 (공포, 정부이송 등)
    if any(keyword in proc_stage_cd for keyword in ['공포', '정부이송', '처리완료']):
        return 4
    
    # 기타 (철회, 폐기 등)
    return None

def main():
    print("=" * 80)
    print("VM bills 테이블 proc_stage_order 업데이트")
    print("=" * 80)
    
    if not VM_DB['host'] or not VM_DB['password']:
        print("❌ CLOUD_DB_HOST와 CLOUD_DB_PASSWORD 환경 변수가 필요합니다.")
        return
    
    try:
        conn = psycopg2.connect(**VM_DB)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        print("✅ VM DB 연결 성공\n")
    except Exception as e:
        print(f"❌ VM DB 연결 실패: {e}")
        return
    
    try:
        # proc_stage_order가 NULL인 것들 업데이트
        cur.execute("""
            SELECT bill_id, proc_stage_cd, proc_stage_order
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            AND proc_stage_order IS NULL
        """)
        
        bills_to_update = cur.fetchall()
        print(f"[1] 업데이트 대상: {len(bills_to_update):,}건")
        
        if not bills_to_update:
            print("✅ 업데이트할 데이터가 없습니다.")
            
            # 현재 상태 확인
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE proc_stage_order IS NOT NULL) as has_order
                FROM bills
                WHERE proposal_date >= '2025-01-01'
            """)
            result = cur.fetchone()
            print(f"\n   현재 상태: {result['has_order']:,}/{result['total']:,}건 ({result['has_order']/result['total']*100:.1f}%)")
            return
        
        updated = 0
        skipped = 0
        
        for bill in bills_to_update:
            bill_id = bill['bill_id']
            proc_stage_cd = bill['proc_stage_cd']
            
            proc_stage_order = calculate_proc_stage_order(proc_stage_cd)
            
            if proc_stage_order is not None:
                cur.execute("""
                    UPDATE bills
                    SET proc_stage_order = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE bill_id = %s
                """, (proc_stage_order, bill_id))
                updated += 1
            else:
                skipped += 1
            
            if (updated + skipped) % 1000 == 0:
                conn.commit()
                print(f"  진행 중... {updated + skipped:,}/{len(bills_to_update):,}건 처리 (업데이트: {updated:,}, 건너뜀: {skipped:,})")
        
        conn.commit()
        print(f"\n✅ 완료: {updated:,}건 업데이트, {skipped:,}건 건너뜀")
        
        # 확인
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE proc_stage_order IS NOT NULL) as has_order
            FROM bills
            WHERE proposal_date >= '2025-01-01'
        """)
        
        result = cur.fetchone()
        print(f"\n[2] 최종 확인:")
        print(f"    전체: {result['total']:,}건")
        print(f"    proc_stage_order 있음: {result['has_order']:,}건 ({result['has_order']/result['total']*100:.1f}%)")
        
        # proc_stage_order별 통계
        cur.execute("""
            SELECT proc_stage_order, COUNT(*) as cnt
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            AND proc_stage_order IS NOT NULL
            GROUP BY proc_stage_order
            ORDER BY proc_stage_order
        """)
        
        stats = cur.fetchall()
        print(f"\n[3] proc_stage_order별 통계:")
        for stat in stats:
            stage_name = {1: '접수', 2: '심사', 3: '본회의', 4: '처리완료'}.get(stat['proc_stage_order'], '기타')
            print(f"    {stat['proc_stage_order']} ({stage_name}): {stat['cnt']:,}건")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    
    finally:
        cur.close()
        conn.close()
    
    print("\n" + "=" * 80)
    print("✅ 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()

