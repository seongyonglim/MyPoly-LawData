#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2025년 의안 표결 결과 웹 대시보드
Flask 기반 웹 애플리케이션
"""

import sys
import os
from datetime import datetime, date, timedelta
from flask import Flask, render_template, jsonify, request
from flask_caching import Cache
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# .env 파일 자동 로드
load_dotenv()

# Windows 환경에서 한글 출력을 위한 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = Flask(__name__)

# 캐시 설정
cache_config = {
    'CACHE_TYPE': 'simple',  # 메모리 기반 캐시 (프로덕션에서는 Redis 사용 권장)
    'CACHE_DEFAULT_TIMEOUT': 300  # 5분 캐시
}
app.config.from_mapping(cache_config)
cache = Cache(app)


# 데이터베이스 설정 (로컬/GCP 모두 지원)
def get_db_config():
    """데이터베이스 설정 (환경 변수 우선, 없으면 로컬 기본값)"""
    # GCP 환경 변수 확인
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_name = os.environ.get('DB_NAME', 'mypoly_lawdata')
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', 'maza_970816')
    db_port = int(os.environ.get('DB_PORT', '5432'))
    
    return {
        'host': db_host,
        'database': db_name,
        'user': db_user,
        'password': db_password,
        'port': db_port
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
@cache.cached(timeout=300)  # 5분 캐시
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
@cache.cached(timeout=60, query_string=True)  # 1분 캐시, 쿼리 파라미터별로 캐시
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
@cache.cached(timeout=600)  # 10분 캐시 (월별 데이터는 자주 변경되지 않음)
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
@cache.cached(timeout=600)  # 10분 캐시
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
@cache.cached(timeout=600)  # 10분 캐시
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

def get_table_korean_info(table_name):
    """테이블명에 대한 한글명과 설명 반환"""
    table_info = {
        'bills': {
            'name': '의안 정보',
            'description': '국회에서 제안된 의안의 기본 정보와 진행 상황을 저장하는 테이블입니다.'
        },
        'assembly_members': {
            'name': '국회의원 정보',
            'description': '국회의원의 기본 정보, 정당, 선거구, 위원회 등 상세 정보를 저장하는 테이블입니다.'
        },
        'votes': {
            'name': '표결 정보',
            'description': '국회의원들이 의안에 대해 표결한 결과(찬성/반대/기권/불참)를 저장하는 테이블입니다.'
        },
        'user_votes': {
            'name': '사용자 투표',
            'description': '일반 사용자가 의안에 대해 투표한 결과를 저장하는 테이블입니다. (추후 기능)'
        },
        'user_political_profile': {
            'name': '사용자 정치성향 프로필',
            'description': '사용자가 정치성향 테스트를 통해 얻은 8개 축의 점수를 저장하는 테이블입니다. (추후 기능)'
        },
        'member_political_profile': {
            'name': '의원 정치성향 프로필',
            'description': '국회의원의 표결 이력을 기반으로 계산된 정치성향 점수를 저장하는 테이블입니다. (추후 기능)'
        },
        'proc_stage_mapping': {
            'name': '진행 단계 매핑',
            'description': '의안의 진행 단계 코드(접수, 심사, 본회의, 처리완료 등)를 읽기 쉬운 이름으로 매핑하는 설정 테이블입니다.'
        },
        'bill_similarity': {
            'name': '의안 유사도',
            'description': '의안 간의 유사도를 계산한 결과를 저장하는 테이블입니다. 유사도 점수(0.0~1.0)로 저장되며, 하나의 계산 방법을 사용합니다. (추후 기능)'
        },
    }
    return table_info.get(table_name, {'name': table_name, 'description': ''})

def get_column_korean_name(table_name, column_name):
    """컬럼명에 대한 한글 설명 반환"""
    column_descriptions = {
        'bills': {
            'bill_id': '의안ID',
            'bill_no': '의안번호',
            'title': '의안명',
            'proposal_date': '제안일',
            'proposer_kind': '제안자구분',
            'proposer_name': '제안자 이름',
            'proc_stage_cd': '진행단계 코드',
            'pass_gubn': '처리구분',
            'proc_date': '처리일',
            'general_result': '일반 결과',
            'summary_raw': '제안이유 및 주요내용 원문',
            'summary': 'AI 요약 결과',
            'categories': '카테고리 분류 결과',
            'vote_for': '찬성 시 정치성향 가중치',
            'vote_against': '반대 시 정치성향 가중치',
            'proc_stage_order': '진행 단계 순서',
            'proposer_count': '제안자 수',
            'link_url': '의안 원문 링크',
            'created_at': '생성일시',
            'updated_at': '수정일시',
        },
        'assembly_members': {
            'member_id': '의원코드',
            'name': '의원명',
            'name_chinese': '한자명',
            'name_english': '영문명',
            'party': '정당명',
            'district': '선거구',
            'district_type': '선거구 구분명',
            'committee': '소속위원회명',
            'current_committee': '현재 위원회명',
            'era': '당선 대수',
            'election_type': '선거 구분명',
            'gender': '성별',
            'birth_date': '생년월일',
            'birth_type': '생년 구분 코드',
            'duty_name': '직책명',
            'phone': '전화번호',
            'email': '이메일',
            'homepage_url': '홈페이지 URL',
            'office_room': '사무실 호수',
            'aide_name': '보좌관 이름',
            'secretary_name': '비서 이름',
            'assistant_name': '조수 이름',
            'photo_url': '사진 URL',
            'brief_history': '약력',
            'mona_cd': '표결정보 API의 MONA_CD',
            'member_no': '표결정보 API의 MEMBER_NO',
            'created_at': '생성일시',
            'updated_at': '수정일시',
        },
        'votes': {
            'vote_id': '표결ID',
            'bill_id': '의안ID',
            'bill_no': '의안번호',
            'bill_name': '의안명',
            'member_no': '의원번호',
            'mona_cd': 'MONA 코드',
            'member_id': '의원코드',
            'member_name': '의원명',
            'member_name_chinese': '의원 한자명',
            'party_name': '정당명',
            'party_code': '정당 코드',
            'district_name': '선거구명',
            'district_code': '선거구 코드',
            'vote_result': '표결결과',
            'vote_date': '표결일시',
            'era': '국회 대수',
            'session_code': '회기 코드',
            'current_committee': '현재 위원회',
            'current_committee_id': '현재 위원회 ID',
            'currents_code': '회기 코드 (미사용)',
            'dept_code': '부서 코드 (미사용)',
            'display_order': '표시 순서 (미사용)',
            'law_title': '법률 제목 (미사용)',
            'bill_url': '의안 URL (미사용)',
            'bill_name_url': '의안명 URL (미사용)',
            'created_at': '생성일시',
            'updated_at': '수정일시',
        },
        'user_votes': {
            'user_vote_id': '사용자 투표ID',
            'bill_id': '의안ID',
            'user_id': '사용자ID',
            'vote_result': '투표 결과',
            'vote_date': '투표일시',
        },
        'user_political_profile': {
            'user_id': '사용자ID',
            'p_score': '공공 중심 점수',
            'm_score': '시장 중심 점수',
            'u_score': '보편 적용 점수',
            't_score': '대상 맞춤 점수',
            'n_score': '필요 기반 점수',
            's_score': '성과 기반 점수',
            'o_score': '개방 실험 점수',
            'r_score': '절차 안정 점수',
            'test_completed': '테스트 완료 여부',
            'created_at': '생성일시',
            'updated_at': '수정일시',
        },
        'member_political_profile': {
            'member_id': '의원코드',
            'p_score': '공공 중심 점수',
            'm_score': '시장 중심 점수',
            'u_score': '보편 적용 점수',
            't_score': '대상 맞춤 점수',
            'n_score': '필요 기반 점수',
            's_score': '성과 기반 점수',
            'o_score': '개방 실험 점수',
            'r_score': '절차 안정 점수',
            'total_votes': '총 표결 수',
            'last_calculated_at': '마지막 계산일시',
            'created_at': '생성일시',
            'updated_at': '수정일시',
        },
        'proc_stage_mapping': {
            'stage_code': '진행 단계 코드',
            'stage_name': '진행 단계 이름',
            'stage_order': '진행 단계 순서',
            'description': '설명',
        },
        'bill_similarity': {
            'bill_id_1': '의안ID 1',
            'bill_id_2': '의안ID 2',
            'similarity_score': '유사도 점수',
            'created_at': '생성일시',
        },
    }
    
    return column_descriptions.get(table_name, {}).get(column_name, '')

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
            
            columns = []
            for row in cur.fetchall():
                col = dict(row)
                col['korean_name'] = get_column_korean_name(table_name, col['column_name'])
                columns.append(col)
            
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
            
            # 테이블 한글 정보 추가
            table_korean_info = get_table_korean_info(table_name)
            
            tables.append({
                'table_name': table_name,
                'korean_name': table_korean_info['name'],
                'description': table_korean_info['description'],
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

@app.route('/members/quality')
def members_quality_dashboard():
    """의원 정보 데이터 품질 대시보드"""
    return render_template('members_quality.html')

@app.route('/api/members/quality/stats')
@cache.cached(timeout=300)  # 5분 캐시
def get_members_quality_stats():
    """의원 정보 데이터 품질 통계"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 전체 의원 수
        cur.execute("SELECT COUNT(*) as total FROM assembly_members")
        total = cur.fetchone()['total']
        
        # 필드별 NULL 비율 계산
        fields = [
            ('name', '의원명'),
            ('name_chinese', '한자명'),
            ('name_english', '영문명'),
            ('party', '정당명'),
            ('district', '선거구'),
            ('district_type', '선거구 구분'),
            ('committee', '소속위원회'),
            ('current_committee', '현재위원회'),
            ('era', '당선 대수'),
            ('election_type', '선거 구분'),
            ('gender', '성별'),
            ('birth_date', '생년월일'),
            ('birth_type', '생년 구분'),
            ('duty_name', '직책명'),
            ('phone', '전화번호'),
            ('email', '이메일'),
            ('homepage_url', '홈페이지'),
            ('office_room', '사무실 호수'),
            ('aide_name', '보좌관'),
            ('secretary_name', '비서'),
            ('assistant_name', '조수'),
            ('photo_url', '사진 URL'),
            ('brief_history', '약력'),
            ('mona_cd', 'MONA 코드'),
            ('member_no', '의원번호'),
        ]
        
        field_stats = []
        for field, label in fields:
            cur.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT({field}) as filled,
                    COUNT(*) - COUNT({field}) as missing
                FROM assembly_members
            """)
            result = cur.fetchone()
            filled = result['filled']
            missing = result['missing']
            completion_rate = (filled / total * 100) if total > 0 else 0
            
            field_stats.append({
                'field': field,
                'label': label,
                'total': total,
                'filled': filled,
                'missing': missing,
                'completion_rate': round(completion_rate, 1)
            })
        
        # 의원별 데이터 완성도
        cur.execute("""
            SELECT 
                member_id,
                name,
                party,
                district,
                (
                    CASE WHEN name IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN name_chinese IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN name_english IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN party IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN district IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN district_type IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN committee IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN current_committee IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN era IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN election_type IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN gender IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN birth_date IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN birth_type IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN duty_name IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN phone IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN email IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN homepage_url IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN office_room IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN aide_name IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN secretary_name IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN assistant_name IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN photo_url IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN brief_history IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN mona_cd IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN member_no IS NOT NULL THEN 1 ELSE 0 END
                ) as filled_fields,
                25 as total_fields
            FROM assembly_members
            ORDER BY filled_fields ASC, name ASC
        """)
        
        members = []
        for row in cur.fetchall():
            completion_rate = (row['filled_fields'] / row['total_fields'] * 100) if row['total_fields'] > 0 else 0
            members.append({
                'member_id': row['member_id'],
                'name': row['name'],
                'party': row['party'],
                'district': row['district'],
                'filled_fields': row['filled_fields'],
                'total_fields': row['total_fields'],
                'completion_rate': round(completion_rate, 1)
            })
        
        return jsonify({
            'total_members': total,
            'field_stats': field_stats,
            'members': members
        })
    
    except Exception as e:
        print(f"의원 품질 통계 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        cur.close()
        conn.close()

@app.route('/bills/quality')
def bills_quality_dashboard():
    """의안 정보 데이터 품질 대시보드"""
    return render_template('bills_quality.html')

@app.route('/api/bills/quality/stats')
@cache.cached(timeout=300)  # 5분 캐시
def get_bills_quality_stats():
    """의안 정보 데이터 품질 통계"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 전체 의안 수
        cur.execute("SELECT COUNT(*) as total FROM bills WHERE proposal_date >= '2025-01-01'")
        total = cur.fetchone()['total']
        
        # 필드별 NULL 비율 계산
        fields = [
            ('bill_id', '의안ID'),
            ('bill_no', '의안번호'),
            ('title', '의안명'),
            ('proposal_date', '제안일'),
            ('proposer_kind', '제안자구분'),
            ('proposer_name', '제안자명'),
            ('proc_stage_cd', '진행단계'),
            ('pass_gubn', '처리구분'),
            ('proc_date', '처리일'),
            ('general_result', '일반결과'),
            ('summary_raw', '원문내용'),
            ('summary', 'AI 요약'),
            ('categories', '카테고리'),
            ('vote_for', '찬성 가중치'),
            ('vote_against', '반대 가중치'),
            ('proc_stage_order', '진행단계 순서'),
            ('proposer_count', '제안자 수'),
            ('link_url', '링크 URL'),
        ]
        
        field_stats = []
        for field, label in fields:
            cur.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT({field}) as filled,
                    COUNT(*) - COUNT({field}) as missing
                FROM bills
                WHERE proposal_date >= '2025-01-01'
            """)
            result = cur.fetchone()
            filled = result['filled']
            missing = result['missing']
            completion_rate = (filled / total * 100) if total > 0 else 0
            
            field_stats.append({
                'field': field,
                'label': label,
                'total': total,
                'filled': filled,
                'missing': missing,
                'completion_rate': round(completion_rate, 1)
            })
        
        # 의안별 데이터 완성도
        cur.execute("""
            SELECT 
                bill_id,
                bill_no,
                title,
                proposer_kind,
                pass_gubn,
                proc_stage_cd,
                (
                    CASE WHEN bill_id IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN bill_no IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN title IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN proposal_date IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN proposer_kind IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN proposer_name IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN proc_stage_cd IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN pass_gubn IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN proc_date IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN general_result IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN summary_raw IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN summary IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN categories IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN vote_for IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN vote_against IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN proc_stage_order IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN proposer_count IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN link_url IS NOT NULL THEN 1 ELSE 0 END
                ) as filled_fields,
                18 as total_fields
            FROM bills
            WHERE proposal_date >= '2025-01-01'
            ORDER BY filled_fields ASC, proposal_date DESC
        """)
        
        bills = []
        for row in cur.fetchall():
            completion_rate = (row['filled_fields'] / row['total_fields'] * 100) if row['total_fields'] > 0 else 0
            bills.append({
                'bill_id': row['bill_id'],
                'bill_no': row['bill_no'],
                'title': row['title'],
                'proposer_kind': row['proposer_kind'],
                'pass_gubn': row['pass_gubn'],
                'proc_stage_cd': row['proc_stage_cd'],
                'filled_fields': row['filled_fields'],
                'total_fields': row['total_fields'],
                'completion_rate': round(completion_rate, 1)
            })
        
        # 표결 결과 연결 통계
        cur.execute("""
            SELECT 
                COUNT(DISTINCT b.bill_id) as bills_with_votes,
                COUNT(DISTINCT b.bill_id) FILTER (WHERE v.bill_id IS NULL) as bills_without_votes
            FROM bills b
            LEFT JOIN votes v ON b.bill_id = v.bill_id
            WHERE b.proposal_date >= '2025-01-01'
        """)
        vote_stats = cur.fetchone()
        
        return jsonify({
            'total_bills': total,
            'field_stats': field_stats,
            'bills': bills,
            'vote_stats': {
                'bills_with_votes': vote_stats['bills_with_votes'],
                'bills_without_votes': vote_stats['bills_without_votes']
            }
        })
    
    except Exception as e:
        print(f"의안 품질 통계 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        cur.close()
        conn.close()

@app.route('/api/bills/quality/detail/<bill_id>')
def get_bill_quality_detail(bill_id):
    """특정 의안의 데이터 상세 정보"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                bill_id, bill_no, title, proposal_date,
                proposer_kind, proposer_name,
                proc_stage_cd, pass_gubn, proc_date,
                general_result, summary_raw, summary,
                categories, vote_for, vote_against,
                proc_stage_order, proposer_count, link_url
            FROM bills
            WHERE bill_id = %s
        """, (bill_id,))
        
        bill = cur.fetchone()
        if not bill:
            return jsonify({'error': 'Bill not found'}), 404
        
        # 필드별 상태 확인
        fields = {
            '기본 정보': [
                ('bill_id', '의안ID'),
                ('bill_no', '의안번호'),
                ('title', '의안명'),
                ('proposal_date', '제안일'),
            ],
            '제안자 정보': [
                ('proposer_kind', '제안자구분'),
                ('proposer_name', '제안자명'),
                ('proposer_count', '제안자 수'),
            ],
            '진행 정보': [
                ('proc_stage_cd', '진행단계'),
                ('proc_stage_order', '진행단계 순서'),
                ('pass_gubn', '처리구분'),
                ('proc_date', '처리일'),
                ('general_result', '일반결과'),
            ],
            '내용 정보': [
                ('summary_raw', '원문내용'),
                ('summary', 'AI 요약'),
                ('categories', '카테고리'),
            ],
            '정치성향 가중치': [
                ('vote_for', '찬성 가중치'),
                ('vote_against', '반대 가중치'),
            ],
            '기타': [
                ('link_url', '링크 URL'),
            ]
        }
        
        field_details = {}
        for category, field_list in fields.items():
            field_details[category] = []
            for field, label in field_list:
                value = bill[field]
                has_value = False
                if value is not None:
                    if isinstance(value, (dict, list)):
                        has_value = len(value) > 0
                    else:
                        has_value = str(value).strip() != ''
                
                field_details[category].append({
                    'field': field,
                    'label': label,
                    'value': value,
                    'has_value': has_value
                })
        
        return jsonify({
            'bill': dict(bill),
            'field_details': field_details
        })
    
    except Exception as e:
        print(f"의안 상세 정보 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        cur.close()
        conn.close()

@app.route('/api/members/quality/detail/<member_id>')
def get_member_quality_detail(member_id):
    """특정 의원의 데이터 상세 정보"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                member_id, name, name_chinese, name_english,
                party, district, district_type,
                committee, current_committee,
                era, election_type,
                gender, birth_date, birth_type,
                duty_name, phone, email, homepage_url, office_room,
                aide_name, secretary_name, assistant_name,
                photo_url, brief_history,
                mona_cd, member_no
            FROM assembly_members
            WHERE member_id = %s
        """, (member_id,))
        
        member = cur.fetchone()
        if not member:
            return jsonify({'error': 'Member not found'}), 404
        
        # 필드별 상태 확인
        fields = {
            '기본 정보': [
                ('name', '의원명'),
                ('name_chinese', '한자명'),
                ('name_english', '영문명'),
            ],
            '정당/선거 정보': [
                ('party', '정당명'),
                ('district', '선거구'),
                ('district_type', '선거구 구분'),
                ('era', '당선 대수'),
                ('election_type', '선거 구분'),
            ],
            '위원회 정보': [
                ('committee', '소속위원회'),
                ('current_committee', '현재위원회'),
            ],
            '개인 정보': [
                ('gender', '성별'),
                ('birth_date', '생년월일'),
                ('birth_type', '생년 구분'),
                ('duty_name', '직책명'),
            ],
            '연락처 정보': [
                ('phone', '전화번호'),
                ('email', '이메일'),
                ('homepage_url', '홈페이지'),
                ('office_room', '사무실 호수'),
            ],
            '보좌진 정보': [
                ('aide_name', '보좌관'),
                ('secretary_name', '비서'),
                ('assistant_name', '조수'),
            ],
            '기타 정보': [
                ('photo_url', '사진 URL'),
                ('brief_history', '약력'),
                ('mona_cd', 'MONA 코드'),
                ('member_no', '의원번호'),
            ]
        }
        
        field_details = {}
        for category, field_list in fields.items():
            field_details[category] = []
            for field, label in field_list:
                value = member[field]
                field_details[category].append({
                    'field': field,
                    'label': label,
                    'value': value,
                    'has_value': value is not None and str(value).strip() != ''
                })
        
        return jsonify({
            'member': dict(member),
            'field_details': field_details
        })
    
    except Exception as e:
        print(f"의원 상세 정보 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("2025년 의안 표결 결과 웹 대시보드 시작")
    print("=" * 60)
    print("서버 주소: http://0.0.0.0:5000")
    print("의안 대시보드: http://localhost:5000")
    print("DB 구조 페이지: http://localhost:5000/db-structure")
    print("의원 품질 대시보드: http://localhost:5000/members/quality")
    print("의안 품질 대시보드: http://localhost:5000/bills/quality")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)

