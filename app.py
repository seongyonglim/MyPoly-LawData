#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2025년 의안 표결 결과 웹 대시보드
Flask 기반 웹 애플리케이션
"""

import sys
import os
from datetime import datetime, date
from flask import Flask, render_template, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Windows 환경에서 한글 출력을 위한 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = Flask(__name__)

# 데이터베이스 설정 (환경 변수 지원)
def get_db_config():
    """환경 변수에서 데이터베이스 설정 가져오기"""
    # Railway는 DATABASE_URL 제공
    if 'DATABASE_URL' in os.environ:
        from urllib.parse import urlparse
        db_url = urlparse(os.environ['DATABASE_URL'])
        return {
            'host': db_url.hostname,
            'database': db_url.path[1:],  # / 제거
            'user': db_url.username,
            'password': db_url.password,
            'port': db_url.port or 5432
        }
    # Render는 개별 환경 변수 제공
    elif 'DB_HOST' in os.environ:
        return {
            'host': os.environ.get('DB_HOST'),
            'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': os.environ.get('DB_PASSWORD'),
            'port': int(os.environ.get('DB_PORT', 5432))
        }
    # 로컬 개발용 (기본값)
    else:
        return {
            'host': 'localhost',
            'database': 'mypoly_lawdata',
            'user': 'postgres',
            'password': 'maza_970816',
            'port': 5432
        }

def get_db_connection():
    """데이터베이스 연결 생성"""
    try:
        config = get_db_config()
        conn = psycopg2.connect(**config)
        return conn
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        raise

def format_date_for_json(dt):
    """날짜 객체를 JSON 직렬화 가능한 문자열로 변환"""
    if dt is None:
        return None
    if isinstance(dt, date):
        return dt.isoformat()
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    """전체 통계 정보"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 전체 의안 수
        cur.execute("""
            SELECT COUNT(*) as total_bills
            FROM bills
            WHERE proposal_date >= '2025-01-01'
        """)
        total_bills = cur.fetchone()['total_bills']
        
        # 표결 진행된 의안 수
        cur.execute("""
            SELECT COUNT(DISTINCT b.bill_id) as bills_with_votes
            FROM bills b
            INNER JOIN votes v ON b.bill_id = v.bill_id
            WHERE b.proposal_date >= '2025-01-01'
        """)
        bills_with_votes = cur.fetchone()['bills_with_votes']
        
        # 전체 표결 결과 수
        cur.execute("""
            SELECT COUNT(*) as total_votes
            FROM votes v
            INNER JOIN bills b ON v.bill_id = b.bill_id
            WHERE b.proposal_date >= '2025-01-01'
        """)
        total_votes = cur.fetchone()['total_votes']
        
        # 표결 결과가 없는 의안 수
        bills_without_votes = total_bills - bills_with_votes
        
        # 계류의안 수
        cur.execute("""
            SELECT COUNT(*) as count
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            AND pass_gubn = '계류의안'
        """)
        pending_bills = cur.fetchone()['count']
        
        # 처리의안 수
        cur.execute("""
            SELECT COUNT(*) as count
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            AND pass_gubn = '처리의안'
        """)
        processed_bills = cur.fetchone()['count']
        
        # 처리의안 중 표결 결과가 있는 의안 수
        cur.execute("""
            SELECT COUNT(DISTINCT b.bill_id) as count
            FROM bills b
            INNER JOIN votes v ON b.bill_id = v.bill_id
            WHERE b.proposal_date >= '2025-01-01'
            AND b.pass_gubn = '처리의안'
        """)
        processed_with_votes = cur.fetchone()['count']
        
        # 처리의안 중 표결 결과가 없는 의안 수
        processed_no_votes = processed_bills - processed_with_votes
        
        # 진행단계별 통계 (모든 단계)
        cur.execute("""
            SELECT 
                COALESCE(proc_stage_cd, '미분류') as proc_stage_cd,
                COUNT(*) as count
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            GROUP BY proc_stage_cd
        """)
        proc_stage_stats = {row['proc_stage_cd']: row['count'] for row in cur.fetchall()}
        
        # 처리/계류 통계
        cur.execute("""
            SELECT 
                COALESCE(pass_gubn, '미분류') as pass_gubn,
                COUNT(*) as count
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            GROUP BY pass_gubn
        """)
        pass_gubn_stats = {row['pass_gubn']: row['count'] for row in cur.fetchall()}
        
        # 월별 의안 수
        cur.execute("""
            SELECT 
                TO_CHAR(proposal_date, 'YYYY-MM') as month,
                COUNT(*) as count
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            GROUP BY TO_CHAR(proposal_date, 'YYYY-MM')
            ORDER BY month
        """)
        monthly_bills = {row['month']: row['count'] for row in cur.fetchall()}
        
        return jsonify({
            'total_bills': total_bills,
            'bills_with_votes': bills_with_votes,
            'bills_without_votes': bills_without_votes,
            'total_votes': total_votes,
            'pending_bills': pending_bills,
            'processed_bills': processed_bills,
            'processed_with_votes': processed_with_votes,
            'processed_no_votes': processed_no_votes,
            'proc_stage_stats': proc_stage_stats,
            'pass_gubn_stats': pass_gubn_stats,
            'monthly_bills': monthly_bills
        })
    
    except Exception as e:
        print(f"통계 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        cur.close()
        conn.close()

@app.route('/api/bills')
def get_bills():
    """의안 목록 조회 (월별 필터링, 제목 검색, 처리구분, 진행단계 필터 지원)"""
    month = request.args.get('month', None)  # YYYY-MM 형식
    search = request.args.get('search', None)  # 제목 검색어
    pass_gubn = request.args.get('pass_gubn', None)  # 처리구분 필터
    proc_stage = request.args.get('proc_stage', None)  # 진행단계 필터
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    sort_by = request.args.get('sort_by', 'proposal_date')  # proposal_date, vote_count
    order = request.args.get('order', 'desc')  # asc, desc
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # WHERE 조건 구성
        where_conditions = ["b.proposal_date >= '2025-01-01'"]
        params_list = []
        
        if month:
            where_conditions.append("TO_CHAR(b.proposal_date, 'YYYY-MM') = %s")
            params_list.append(month)
        
        if search:
            where_conditions.append("b.title ILIKE %s")
            params_list.append(f'%{search}%')
        
        if pass_gubn:
            where_conditions.append("b.pass_gubn = %s")
            params_list.append(pass_gubn)
        
        if proc_stage:
            where_conditions.append("b.proc_stage_cd = %s")
            params_list.append(proc_stage)
        
        where_clause = " AND ".join(where_conditions)
        
        # 정렬 조건 구성
        if sort_by == 'vote_count':
            order_by = f"vote_count {order.upper()}, b.proposal_date DESC"
        else:
            order_by = f"b.proposal_date {order.upper()}"
        
        # 전체 개수 조회
        count_query = f"""
            SELECT COUNT(DISTINCT b.bill_id) as total
            FROM bills b
            LEFT JOIN votes v ON b.bill_id = v.bill_id
            WHERE {where_clause}
        """
        cur.execute(count_query, tuple(params_list))
        total = cur.fetchone()['total']
        
        # 의안 목록 조회 (표결 결과 포함)
        query = f"""
            SELECT 
                b.bill_id,
                b.bill_no,
                b.title,
                b.proposal_date,
                b.proposer_kind,
                b.proposer_name,
                b.proc_stage_cd,
                b.pass_gubn,
                b.proc_date,
                b.general_result,
                b.link_url,
                COUNT(DISTINCT v.vote_id) as vote_count,
                COUNT(DISTINCT CASE WHEN v.vote_result = '찬성' THEN v.vote_id END) as vote_for,
                COUNT(DISTINCT CASE WHEN v.vote_result = '반대' THEN v.vote_id END) as vote_against,
                COUNT(DISTINCT CASE WHEN v.vote_result = '기권' THEN v.vote_id END) as vote_abstain,
                COUNT(DISTINCT CASE WHEN v.vote_result = '불참' THEN v.vote_id END) as vote_absent,
                COUNT(DISTINCT v.member_no) as member_count
            FROM bills b
            LEFT JOIN votes v ON b.bill_id = v.bill_id
            WHERE {where_clause}
            GROUP BY b.bill_id, b.bill_no, b.title, b.proposal_date, 
                     b.proposer_kind, b.proposer_name, b.proc_stage_cd, b.pass_gubn, 
                     b.proc_date, b.general_result, b.link_url
            ORDER BY {order_by}
            LIMIT %s OFFSET %s
        """
        
        offset = (page - 1) * per_page
        query_params = tuple(params_list) + (per_page, offset)
        cur.execute(query, query_params)
        
        bills = []
        for row in cur.fetchall():
            bill = dict(row)
            # 날짜 형식 변환
            bill['proposal_date'] = format_date_for_json(bill['proposal_date'])
            bill['proc_date'] = format_date_for_json(bill['proc_date'])
            bills.append(bill)
        
        return jsonify({
            'bills': bills,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
    
    except Exception as e:
        print(f"의안 목록 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
    finally:
        cur.close()
        conn.close()

@app.route('/api/bills/<bill_id>')
def get_bill_detail(bill_id):
    """의안 상세 정보 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 의안 기본 정보
        cur.execute("""
            SELECT 
                b.*,
                COUNT(DISTINCT v.vote_id) as vote_count,
                COUNT(DISTINCT CASE WHEN v.vote_result = '찬성' THEN v.vote_id END) as vote_for,
                COUNT(DISTINCT CASE WHEN v.vote_result = '반대' THEN v.vote_id END) as vote_against,
                COUNT(DISTINCT CASE WHEN v.vote_result = '기권' THEN v.vote_id END) as vote_abstain,
                COUNT(DISTINCT CASE WHEN v.vote_result = '불참' THEN v.vote_id END) as vote_absent,
                COUNT(DISTINCT v.member_no) as member_count
            FROM bills b
            LEFT JOIN votes v ON b.bill_id = v.bill_id
            WHERE b.bill_id = %s
            GROUP BY b.bill_id
        """, (bill_id,))
        
        bill = cur.fetchone()
        if not bill:
            return jsonify({'error': '의안을 찾을 수 없습니다.'}), 404
        
        bill_dict = dict(bill)
        bill_dict['proposal_date'] = format_date_for_json(bill_dict['proposal_date'])
        bill_dict['proc_date'] = format_date_for_json(bill_dict['proc_date'])
        bill_dict['created_at'] = format_date_for_json(bill_dict['created_at'])
        bill_dict['updated_at'] = format_date_for_json(bill_dict['updated_at'])
        
        # 정당별 표결 결과
        cur.execute("""
            SELECT 
                v.party_name,
                COUNT(*) as total,
                COUNT(CASE WHEN v.vote_result = '찬성' THEN 1 END) as vote_for,
                COUNT(CASE WHEN v.vote_result = '반대' THEN 1 END) as vote_against,
                COUNT(CASE WHEN v.vote_result = '기권' THEN 1 END) as vote_abstain,
                COUNT(CASE WHEN v.vote_result = '불참' THEN 1 END) as vote_absent
            FROM votes v
            WHERE v.bill_id = %s
            AND v.party_name IS NOT NULL
            GROUP BY v.party_name
            ORDER BY total DESC
        """, (bill_id,))
        
        party_votes = []
        for row in cur.fetchall():
            party_votes.append(dict(row))
        
        bill_dict['party_votes'] = party_votes
        
        # 의원별 표결 결과 (찬성/반대/기권/불참별로 분류)
        cur.execute("""
            SELECT 
                v.member_name,
                v.party_name,
                v.district_name,
                v.vote_result,
                am.member_id,
                am.photo_url
            FROM votes v
            LEFT JOIN assembly_members am ON v.member_id = am.member_id
            WHERE v.bill_id = %s
            AND v.member_name IS NOT NULL
            ORDER BY 
                CASE v.vote_result
                    WHEN '찬성' THEN 1
                    WHEN '반대' THEN 2
                    WHEN '기권' THEN 3
                    WHEN '불참' THEN 4
                    ELSE 5
                END,
                v.member_name
        """, (bill_id,))
        
        # 표결 결과별로 분류
        member_votes_by_result = {
            '찬성': [],
            '반대': [],
            '기권': [],
            '불참': []
        }
        
        for row in cur.fetchall():
            vote_data = dict(row)
            vote_result = vote_data.get('vote_result', '')
            if vote_result in member_votes_by_result:
                member_votes_by_result[vote_result].append(vote_data)
        
        bill_dict['member_votes_by_result'] = member_votes_by_result
        
        return jsonify(bill_dict)
    
    except Exception as e:
        print(f"의안 상세 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
    finally:
        cur.close()
        conn.close()

@app.route('/api/months')
def get_available_months():
    """사용 가능한 월 목록 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT DISTINCT
                TO_CHAR(proposal_date, 'YYYY-MM') as month,
                TO_CHAR(proposal_date, 'YYYY년 MM월') as month_label,
                COUNT(*) as bill_count
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            GROUP BY TO_CHAR(proposal_date, 'YYYY-MM'), TO_CHAR(proposal_date, 'YYYY년 MM월')
            ORDER BY month DESC
        """)
        
        months = [dict(row) for row in cur.fetchall()]
        return jsonify({'months': months})
    
    except Exception as e:
        print(f"월 목록 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        cur.close()
        conn.close()

@app.route('/api/pass_gubn_options')
def get_pass_gubn_options():
    """처리구분 옵션 목록 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT DISTINCT
                pass_gubn,
                COUNT(*) as bill_count
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            AND pass_gubn IS NOT NULL
            GROUP BY pass_gubn
            ORDER BY bill_count DESC
        """)
        
        options = [dict(row) for row in cur.fetchall()]
        return jsonify({'options': options})
    
    except Exception as e:
        print(f"처리구분 옵션 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        cur.close()
        conn.close()

@app.route('/api/proc_stage_options')
def get_proc_stage_options():
    """진행단계 옵션 목록 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT DISTINCT
                proc_stage_cd,
                COUNT(*) as bill_count
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            AND proc_stage_cd IS NOT NULL
            GROUP BY proc_stage_cd
            ORDER BY bill_count DESC
        """)
        
        options = [dict(row) for row in cur.fetchall()]
        return jsonify({'options': options})
    
    except Exception as e:
        print(f"진행단계 옵션 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        cur.close()
        conn.close()

@app.route('/erd')
def erd():
    """ERD (테이블 관계도) 페이지"""
    return render_template('erd.html')

@app.route('/api/erd')
def get_erd():
    """ERD 데이터 조회 (테이블 및 관계 정보)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 모든 테이블 목록 조회
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        table_names = [row['table_name'] for row in cur.fetchall()]
        
        tables = []
        relationships = []
        
        for table_name in table_names:
            # 데이터 개수
            cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = cur.fetchone()['count']
            
            # 컬럼 정보 (주요 컬럼만)
            cur.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length as max_length,
                    is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = [dict(row) for row in cur.fetchall()]
            
            # 외래키 정보
            cur.execute("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name as from_column,
                    ccu.table_name AS to_table,
                    ccu.column_name AS to_column,
                    rc.delete_rule as on_delete
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                LEFT JOIN information_schema.referential_constraints AS rc
                    ON rc.constraint_name = tc.constraint_name
                    AND rc.constraint_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
                AND tc.table_name = %s
            """, (table_name,))
            
            foreign_keys = cur.fetchall()
            
            tables.append({
                'table_name': table_name,
                'row_count': row_count,
                'columns': columns,
                'foreign_keys': [dict(fk) for fk in foreign_keys]
            })
            
            # 관계 정보 추가
            for fk in foreign_keys:
                relationships.append({
                    'from_table': table_name,
                    'from_column': fk['from_column'],
                    'to_table': fk['to_table'],
                    'to_column': fk['to_column'],
                    'on_delete': fk['on_delete'] or 'NO ACTION'
                })
        
        return jsonify({
            'tables': tables,
            'relationships': relationships
        })
    
    except Exception as e:
        print(f"ERD 데이터 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
    finally:
        cur.close()
        conn.close()

@app.route('/db-structure')
def db_structure():
    """데이터베이스 테이블 구조 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 모든 테이블 목록 조회
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        table_names = [row['table_name'] for row in cur.fetchall()]
        
        tables = []
        total_bills = 0
        total_members = 0
        total_votes = 0
        
        for table_name in table_names:
            # 데이터 개수
            cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = cur.fetchone()['count']
            
            if table_name == 'bills':
                total_bills = row_count
            elif table_name == 'assembly_members':
                total_members = row_count
            elif table_name == 'votes':
                total_votes = row_count
            
            # 컬럼 정보
            cur.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length as max_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = [dict(row) for row in cur.fetchall()]
            
            # 인덱스 정보
            cur.execute("""
                SELECT
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename = %s
                ORDER BY indexname
            """, (table_name,))
            
            indexes = [dict(row) for row in cur.fetchall()]
            
            # 외래키 정보
            cur.execute("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
                AND tc.table_name = %s
            """, (table_name,))
            
            foreign_keys = [dict(row) for row in cur.fetchall()]
            
            tables.append({
                'table_name': table_name,
                'row_count': row_count,
                'columns': columns,
                'indexes': indexes,
                'foreign_keys': foreign_keys
            })
        
        summary = {
            'total_tables': len(tables),
            'total_bills': total_bills,
            'total_members': total_members,
            'total_votes': total_votes
        }
        
        return render_template('db_structure.html', tables=tables, summary=summary)
    
    except Exception as e:
        print(f"테이블 구조 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return f"오류 발생: {str(e)}", 500
    
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    # 프로덕션 환경에서는 PORT 환경 변수 사용 (Render, Railway 등)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print("=" * 60)
    print("2025년 의안 표결 결과 웹 대시보드 시작")
    print("=" * 60)
    print(f"서버 주소: http://0.0.0.0:{port}")
    print(f"의안 대시보드: http://localhost:{port}")
    print(f"DB 구조 페이지: http://localhost:{port}/db-structure")
    print(f"ERD 페이지: http://localhost:{port}/erd")
    print("=" * 60)
    app.run(debug=debug, host='0.0.0.0', port=port)

