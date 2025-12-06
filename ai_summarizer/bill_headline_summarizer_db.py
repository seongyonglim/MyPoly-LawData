# -*- coding: utf-8 -*-
"""
bill_headline_summarizer_db.py (Gemini 버전 - DB 연동)

DB에 저장된 의안들을 50개씩 배치로 처리하여 AI 요약 생성
- 가장 오래된 것부터 처리 (2025-01-01부터)
- 이미 처리된 의안은 건너뜀 (summary IS NOT NULL)
- 무료 API 제한을 고려하여 2.5초 sleep 유지
"""

import argparse
import json
import os
import re
import sys

# Windows 환경에서 한글 출력을 위한 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import time
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Google Generative AI는 선택적 import (필요할 때만)
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# SYSTEM_GUIDE는 원본 파일과 동일
SYSTEM_GUIDE = """
[역할]
당신은 한국어 뉴스 편집자다. 국회 의안(법률 제·개정안, 결의안, 보고안 등)의 제목과 요약을 받아, 일반 독자(특히 20대)가 바로 이해할 수 있는 간결한 뉴스성 산출물을 만든다. 편향 없이 중립·사실 중심으로, 입력에 포함된 정보만 사용한다.

[산출물]
- headline: 뉴스형 헤드라인 1줄
- summary: 쉬운말 요약 2~3문장
- categories: 아래 16개 카테고리 중 1개(정말 애매할 때만 2개)
- vote: 사용자가 이 의안에 대해 찬성/반대 투표를 했을 때 사전에 수행한 정치성향 테스트(P/M/U/T/N/S/O/R 축)에 가중치(+점수)를 어떻게 반영할지에 대한 안내.
  - 구조:
    {
      "for":     {"P":1, "U":1},
      "against": {"M":1, "T":1}
    }

[정치성향 축(배타쌍)]
- P(공공 중심) / M(시장 중심)
- U(보편 적용) / T(대상 맞춤)
- N(필요 기반) / S(성과·기여 기반)
- O(개방·실험) / R(절차·안정)

[투표 가중치 판정 규칙]
- 같은 축에서 양쪽(P·M, U·T, N·S, O·R)을 동시에 넣지 않는다.
- 1~3개 축을 선택하여 +1 가중치를 부여한다(기본 2개 권장). 가중치는 정수 1을 사용한다.
- 찬성("for")은 의안의 핵심 변화 방향과 부합하는 축 쪽으로 선택한다.
- 반대("against")는 기본적으로 거울 반대 축을 선택하되, 입력 내용상 반대가 특정 가치(예: 절차 안정, 특정대상 보호)를 더 강화하는 맥락이라면 해당 축을 추가할 수 있다.
- 매핑 가이드(예시, 상황에 맞춰 적용):
  - 공공 재정투입 확대/공공서비스 보편 공급 확대 → P, U
  - 민영화/규제완화/경쟁촉진/시장 메커니즘 강화 → M, S
  - 취약계층·특정대상 선별 지원/바우처/상한선 차등 → T, N
  - 규정·심사·면허·감사 강화/처벌 상향/표준절차 엄격화 → R
  - 규제샌드박스/파일럿/신기술 우선적용/유연 실험 → O
  - 요금 보편 인하/보편 급여 확대 → U (상황에 따라 P 동반)
  - 성과기준 인센티브/차등 지원 확대 → S (상황에 따라 M 동반)
    
[출력 형식(엄수)]
- 반드시 JSON 한 객체 **딱 하나**만 출력하고, 그 외 어떤 글자도 출력하지 않는다.
- 구조:
  {
    "headline":"...",
    "summary":"...",
    "categories":["..."],
    "vote":{"for":{"...":1}, "against":{"...":1}}
  }
- 추가 필드, 주석, 설명, 따옴표 밖 텍스트 금지.
- categories 배열에는 지정된 카테고리 이름 **그 자체**만 넣고, 괄호나 보충설명 금지.
- vote의 키는 반드시 P/M/U/T/N/S/O/R 중에서만 선택하고, 값은 양의 정수 1을 사용한다.

[입력 해석 원칙]
- 입력은 의안의 공식 제목(title)과 본문 요약(body)이다.
- 본문에 없는 사실, 추정, 해석 추가 금지.
- 사실관계가 불명확하면 모호한 표현("가능", "검토")로 완곡히 표기하되, 과장·단정 금지.
- 동일·반복 문구, 불필요한 기관명 나열, 과도한 수사는 제거한다.

[헤드라인 작성 규칙]
1) 길이/부호
   - 20~36자(완성형 한글 기준)로 맞춘다.
   - 마침표·물음표·느낌표 금지.
   - 따옴표(" " ' ' " '), 괄호(( ) [ ] { } 〈 〉 《 》 「 」 『 』) 전부 금지.
   - 콜론/세미콜론/슬래시 등 기호 사용 지양. 반드시 필요하면 한 번만.
2) 금지어/금지 패턴
   - '법률안', '개정법률안', '법안', '대안', '수정안' 금지.
   - 기관·위원회명, 발의자 수("○○의원 등 ○인") 등 형식 정보 금지.
   - 원제 그대로의 복붙 금지(핵심 의미는 살리되 표현은 재서술).
3) 내용/구조
   - "누가(대상/적용범위) → 무엇이 바뀌나(핵심 변화) → 왜/효과(의도·기대)" 흐름을 1줄에 응축.
   - 핵심 1~2개만 선택하고, 부차 내용은 과감히 버린다.
   - 수치·기간·대상 확대/축소 등 변경점이 있으면 가능한 한 드러낸다.
4) 톤/어휘
   - 중립·사실 중심, 간결한 평서체(–다).
   - '및/등' 대신 '그리고/같은' 권장.
   - 어려운 한자어·관료어는 쉽고 일상적인 어휘로 치환(필요 시 괄호로 간단 풀이: 예) 긴급응급조치(급히 막는 조치)).
5) 행동·효과 동사(권장)
   - 강화, 완화, 확대, 축소, 의무화, 금지, 허용, 명확화, 신설, 폐지, 인상, 인하, 조정, 설정, 도입, 차단, 보호, 지원, 정비, 개편, 통합, 분리, 개선, 간소화, 고도화
   - 위 동사들은 상황에 맞게 자연스럽게 사용하되, 과장·임의 해석 금지.

[요약 작성 규칙]
1) 분량/문장
   - 2~3문장, 전체 180자 이내.
   - 문장당 14~22자 권장. 너무 긴 문장은 둘로 나눈다.
2) 쉬운말 치환(예)
   - '및/등'→'그리고/같은', '규율/규정'→'정해', '개선/정비'→'고치', '부과'→'매기', '면제'→'빼주', '의무'→'꼭 하게', '완화'→'느슨하게', '강화'→'더 엄격하게', '효율화'→'더 효율 있게'
   - 모르면 그냥 더 쉬운 표현을 쓴다.
3) 정보 구성
   - 대상(누구에게) / 변화(무엇이 바뀌나) / 이유·효과(왜 하거나 기대 효과는 무엇인가)를 모두 포함.
   - 가능하면 수치·범위·시점을 간단히 반영. 단, 입력에 없으면 추정하지 않는다.
4) 금지/주의
   - 과장·감정·정치적 수사 금지. 예: '충격', '파격', '전면전'.
   - 출처 불명 수치·사실 추가 금지.
   - '법률안/개정법률안/법안/대안/수정안' 같은 형식 단어 남발 금지.

[카테고리 정의(16개)]
- 일자리, 재정, 금융, 교육, 보건, 복지, 주거, 교통, 환경, 에너지, 디지털, 안전, 청년, 여성, 국방, 문화
[카테고리 경계 규칙]
- 디지털 vs 안전: 개인정보·통신규제·플랫폼 질서는 디지털, 범죄·피해자보호는 안전.
- 복지 vs 교육/청년/여성: 대상이 학생이면 교육, 19~34세 일반 대상이면 청년, 여성 특정이면 여성, 그 외 보편적 소득·돌봄이면 복지.
- 에너지 vs 환경: 전력요금·공급·원전·효율은 에너지, 오염·보전은 환경.
- 모호하면 가장 핵심 영향 분야 1개를 선택. 정말 애매할 때만 2개를 고른다.

[품질 점검(내부 체크리스트)]
- 헤드라인 길이 20~36자 맞는가?
- 금지어(법률안/개정법률안/법안/대안/수정안) 없는가?
- 따옴표/괄호/마침표 등 금지 부호가 없는가?
- 원제 복붙이 아닌가(동일/유사 표현 반복 제거)?
- 대상/변화/이유가 모두 드러나는가?
- 요약 2~3문장, 180자 이내, 문장당 14~22자인가?
- 어려운 말이 남아있다면 더 쉬운 표현으로 바꿨는가?
- categories가 1개(또는 정말 애매한 경우 2개)이고, 목록 외 이름이 없는가?

[안전 장치]
- 입력이 불명확·부족해도 임의 추정 금지.
- 정치적·가치 판단 표현 삼가고, 입법 취지·효과를 과장하지 않는다.
- 날짜·수치·고유명사는 입력에 있을 때만 사용하고, 형식 통일(숫자는 아라비아, 필요 최소한만).

[최종 지시]
- 위 모든 규칙을 따르고, 오직 하나의 JSON 객체만 출력한다.
- 형식 오류, 여분 텍스트, 주석, 설명을 절대 출력하지 않는다.
"""

@dataclass
class RowResult:
    bill_id: str
    title: str
    body: str
    headline: str
    summary: str
    categories: List[str]
    vote_for: Dict[str, int]
    vote_against: Dict[str, int]
    success: bool = False
    error: Optional[str] = None

# ---------- DB 연결 ----------

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
        password = os.environ.get('DB_PASSWORD')
        if not password:
            raise ValueError("DB_PASSWORD environment variable is required")
        return {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': password,
            'port': int(os.environ.get('DB_PORT', '5432'))
        }

def get_db_connection():
    config = get_db_config()
    return psycopg2.connect(**config)

def fetch_unprocessed_bills(limit: int = 50, start_date: str = '2025-01-01') -> List[Dict]:
    """처리되지 않은 의안들을 가져옴 (의안번호 순서대로, 가장 오래된 것부터)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT bill_id, title, summary_raw as body
            FROM bills
            WHERE (summary IS NULL OR summary = '')
              AND proposal_date >= %s
              AND (summary_raw IS NOT NULL AND summary_raw != '')
              AND bill_no IS NOT NULL
            ORDER BY 
                CASE 
                    WHEN bill_no ~ '^ZZ[0-9]+$' THEN CAST(SUBSTRING(bill_no FROM '([0-9]+)') AS INTEGER) - 1000000000
                    WHEN bill_no ~ '^[0-9]+$' THEN CAST(bill_no AS INTEGER)
                    WHEN bill_no ~ '^제[0-9]+호$' THEN CAST(SUBSTRING(bill_no FROM '([0-9]+)') AS INTEGER)
                    ELSE 999999999
                END ASC,
                proposal_date ASC,
                bill_id ASC
            LIMIT %s
        """
        cur.execute(query, (start_date, limit))
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        cur.close()
        conn.close()

def update_bill_summary(bill_id: str, headline: str, summary: str, 
                       categories: List[str], vote_for: Dict[str, int], 
                       vote_against: Dict[str, int]):
    """의안의 AI 요약 결과를 DB에 업데이트"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # headline 컬럼이 있는지 확인
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bills' AND column_name = 'headline'
        """)
        has_headline = cur.fetchone() is not None
        
        if has_headline:
            # headline 컬럼이 있으면 별도 저장
            query = """
                UPDATE bills
                SET headline = %s,
                    summary = %s,
                    categories = %s::jsonb,
                    vote_for = %s::jsonb,
                    vote_against = %s::jsonb,
                    updated_at = CURRENT_TIMESTAMP
                WHERE bill_id = %s
            """
            categories_json = json.dumps(categories, ensure_ascii=False)
            vote_for_json = json.dumps(vote_for, ensure_ascii=False)
            vote_against_json = json.dumps(vote_against, ensure_ascii=False)
            
            cur.execute(query, (headline, summary, categories_json, vote_for_json, vote_against_json, bill_id))
        else:
            # headline 컬럼이 없으면 summary에 포함 (headline + "\n\n" + summary)
            full_summary = f"{headline}\n\n{summary}" if headline else summary
            query = """
                UPDATE bills
                SET summary = %s,
                    categories = %s::jsonb,
                    vote_for = %s::jsonb,
                    vote_against = %s::jsonb,
                    updated_at = CURRENT_TIMESTAMP
                WHERE bill_id = %s
            """
            categories_json = json.dumps(categories, ensure_ascii=False)
            vote_for_json = json.dumps(vote_for, ensure_ascii=False)
            vote_against_json = json.dumps(vote_against, ensure_ascii=False)
            
            cur.execute(query, (full_summary, categories_json, vote_for_json, vote_against_json, bill_id))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

# ---------- Gemini 호출부 ----------

def build_user_prompt(title: str, body: str) -> str:
    return (
        "[입력]\n"
        f"- 제목: {title}\n"
        f"- 본문: {body}\n"
        "\n오직 하나의 JSON 객체만 출력."
    )

def safe_json_parse(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    m = re.search(r"\{.*\}\s*$", text, flags=re.DOTALL)
    if m:
        text = m.group(0)
    try:
        return json.loads(text)
    except Exception:
        return {"headline": "", "summary": "", "categories": []}

def _ensure_dict_i(d: Any) -> Dict[str, int]:
    out: Dict[str, int] = {}
    if isinstance(d, dict):
        for k, v in d.items():
            try:
                iv = int(v)
            except Exception:
                continue
            if k in ("P", "M", "U", "T", "N", "S", "O", "R") and iv > 0:
                out[k] = iv
    return out

def call_model_gemini(model_name: str, title: str, body: str, timeout: int = 60, api_key: str = None) -> RowResult:
    if not HAS_GENAI:
        return RowResult(
            bill_id="",
            title=title,
            body=body,
            headline="",
            summary="",
            categories=[],
            vote_for={},
            vote_against={},
            success=False,
            error="google.generativeai 모듈이 설치되지 않았습니다. 'pip install google-generativeai' 실행 필요"
        )

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("환경변수 GEMINI_API_KEY가 필요합니다.")

    try:
        genai.configure(api_key=api_key)

        generation_config = {
            "temperature": 0.3,
            "response_mime_type": "application/json",
        }

        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            system_instruction=SYSTEM_GUIDE
        )

        user_prompt = build_user_prompt(title, body)
        resp = model.generate_content(user_prompt, request_options={"timeout": timeout})

        content_text = ""
        try:
            content_text = resp.text or ""
        except Exception:
            try:
                content_text = resp.candidates[0].content.parts[0].text
            except Exception:
                content_text = ""

        if not content_text:
            return RowResult(
                bill_id="",
                title=title,
                body=body,
                headline="",
                summary="",
                categories=[],
                vote_for={},
                vote_against={},
                success=False,
                error="응답이 비어있음"
            )

        data = safe_json_parse(content_text)

        headline = (data.get("headline") or "").strip()
        summary = (data.get("summary") or "").strip()

        if not headline or not summary:
            return RowResult(
                bill_id="",
                title=title,
                body=body,
                headline=headline,
                summary=summary,
                categories=[],
                vote_for={},
                vote_against={},
                success=False,
                error="headline 또는 summary가 비어있음"
            )

        cats = data.get("categories") or []
        if isinstance(cats, str):
            try:
                obj = json.loads(cats)
                cats = obj if isinstance(obj, list) else [str(obj)]
            except Exception:
                cats = [cats]

        vote = data.get("vote") or {}
        v_for = _ensure_dict_i(vote.get("for", {}))
        v_again = _ensure_dict_i(vote.get("against", {}))

        return RowResult(
            bill_id="",
            title=title,
            body=body,
            headline=headline,
            summary=summary,
            categories=cats,
            vote_for=v_for,
            vote_against=v_again,
            success=True,
            error=None
        )
    except Exception as e:
        return RowResult(
            bill_id="",
            title=title,
            body=body,
            headline="",
            summary="",
            categories=[],
            vote_for={},
            vote_against={},
            success=False,
            error=str(e)
        )

# ---------- API 키 관리 ----------

class APIKeyManager:
    """여러 API 키를 순환 관리하는 클래스"""
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_index = 0
        self.used_keys = set()  # 할당량 초과된 키 추적
    
    def get_current_key(self) -> str:
        """현재 사용할 API 키 반환"""
        if self.current_index >= len(self.api_keys):
            return None
        return self.api_keys[self.current_index]
    
    def switch_to_next_key(self) -> bool:
        """다음 API 키로 전환. 더 이상 키가 없으면 False 반환"""
        if self.current_index < len(self.api_keys):
            self.used_keys.add(self.current_index)
        
        self.current_index += 1
        
        # 사용 가능한 키 찾기
        while self.current_index < len(self.api_keys):
            if self.current_index not in self.used_keys:
                return True
            self.current_index += 1
        
        return False
    
    def has_more_keys(self) -> bool:
        """사용 가능한 키가 더 있는지 확인"""
        return self.current_index < len(self.api_keys)
    
    def get_key_info(self) -> str:
        """현재 키 정보 반환 (디버깅용)"""
        if self.current_index < len(self.api_keys):
            key_preview = self.api_keys[self.current_index][:20] + "..."
            return f"API 키 {self.current_index + 1}/{len(self.api_keys)} ({key_preview})"
        return "사용 가능한 API 키 없음"

# ---------- 메인 처리 ----------

def process_batch(model_name: str, batch_size: int = 50, start_date: str = '2025-01-01', 
                 timeout: int = 60, base_sleep: float = 2.5, api_key_manager: APIKeyManager = None):
    """의안 배치 처리
    
    Returns:
        tuple: (success_count, error_count, quota_exceeded)
        - success_count: 성공한 의안 수
        - error_count: 실패한 의안 수
        - quota_exceeded: API 할당량 초과 여부 (True면 중단 필요)
    """
    
    if not HAS_GENAI:
        print("오류: google.generativeai 모듈이 설치되지 않았습니다.", file=sys.stderr)
        print("해결: pip install google-generativeai", file=sys.stderr)
        sys.exit(2)
    
    # API 키 관리자 초기화
    if api_key_manager is None:
        # 환경변수에서 API 키 가져오기
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("환경변수 GEMINI_API_KEY가 필요합니다.", file=sys.stderr)
            sys.exit(2)
        api_key_manager = APIKeyManager([api_key])
    
    start_time = time.time()
    print(f"[시작] 배치 크기: {batch_size}, 시작 날짜: {start_date}")
    print(f"[설정] 모델: {model_name}, Sleep: {base_sleep}초")
    print(f"[API 키] {api_key_manager.get_key_info()}")
    print("-" * 60)
    
    # 처리되지 않은 의안 가져오기
    print("처리되지 않은 의안 조회 중...", flush=True)
    bills = fetch_unprocessed_bills(limit=batch_size, start_date=start_date)
    
    if not bills:
        print("처리할 의안이 없습니다.")
        return (0, 0, False)
    
    print(f"[발견] 처리할 의안: {len(bills)}개")
    print("-" * 60)
    
    success_count = 0
    error_count = 0
    quota_exceeded = False
    
    for idx, bill in enumerate(bills, 1):
        bill_id = bill['bill_id']
        title = bill['title'] or ""
        body = bill['body'] or ""
        
        if not title and not body:
            print(f"[{idx}/{len(bills)}] 건너뜀: {bill_id} (제목/본문 없음)")
            continue
        
        print(f"\n[{idx}/{len(bills)}] 처리 중: {bill_id}")
        print(f"  제목: {title[:50]}...")
        print(f"  API 호출 중...", end='', flush=True)
        
        # 현재 API 키 가져오기
        current_api_key = api_key_manager.get_current_key()
        if not current_api_key:
            quota_exceeded = True
            print(f"  ⚠️ 사용 가능한 API 키가 없습니다.")
            print(f"  [중단] 모든 API 키의 할당량이 소진되었습니다.")
            break
        
        try:
            result = call_model_gemini(model_name, title, body, timeout=timeout, api_key=current_api_key)
            result.bill_id = bill_id
            print(" 완료", flush=True)
            
            # API 할당량 초과 확인
            if result.error and ("429" in result.error or "quota" in result.error.lower() or "exceeded" in result.error.lower()):
                print(f"  ⚠️ API 할당량 초과: {result.error[:100]}...")
                print(f"  [전환] 다음 API 키로 전환합니다...")
                
                # 다음 API 키로 전환
                if api_key_manager.switch_to_next_key():
                    new_key = api_key_manager.get_current_key()
                    print(f"  ✓ 새 API 키로 전환: {api_key_manager.get_key_info()}")
                    # 환경변수도 업데이트
                    os.environ["GEMINI_API_KEY"] = new_key
                    # 재시도하지 않고 다음 의안으로
                    error_count += 1
                    continue
                else:
                    quota_exceeded = True
                    print(f"  [중단] 모든 API 키의 할당량이 소진되었습니다.")
                    break
            
            if result.success and result.headline and result.summary:
                # DB 업데이트
                update_bill_summary(
                    bill_id=result.bill_id,
                    headline=result.headline,
                    summary=result.summary,
                    categories=result.categories,
                    vote_for=result.vote_for,
                    vote_against=result.vote_against
                )
                print(f"  ✓ 성공: {result.headline[:40]}...")
                success_count += 1
            else:
                error_msg = result.error or "결과가 비어있음"
                print(f"  ✗ 실패: {error_msg}")
                error_count += 1
                
        except Exception as e:
            error_str = str(e)
            # API 할당량 초과 확인
            if "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
                print(f"  ⚠️ API 할당량 초과: {error_str[:100]}...")
                print(f"  [전환] 다음 API 키로 전환합니다...")
                
                # 다음 API 키로 전환
                if api_key_manager.switch_to_next_key():
                    new_key = api_key_manager.get_current_key()
                    print(f"  ✓ 새 API 키로 전환: {api_key_manager.get_key_info()}")
                    # 환경변수도 업데이트
                    os.environ["GEMINI_API_KEY"] = new_key
                    # 재시도하지 않고 다음 의안으로
                    error_count += 1
                    continue
                else:
                    quota_exceeded = True
                    print(f"  [중단] 모든 API 키의 할당량이 소진되었습니다.")
                    break
            else:
                print(f"  ✗ 에러: {error_str}")
                import traceback
                traceback.print_exc()
                error_count += 1
        
        # Sleep (마지막 항목 제외, 할당량 초과가 아닐 때만)
        if idx < len(bills) and not quota_exceeded:
            jitter = random.uniform(-0.7, 0.7)
            sleep_time = max(0.5, base_sleep + jitter)
            print(f"  대기 중... ({sleep_time:.1f}초)", flush=True)
            time.sleep(sleep_time)
    
    elapsed_time = time.time() - start_time
    print("-" * 60)
    print(f"[완료] 성공: {success_count}개, 실패: {error_count}개, 전체: {len(bills)}개")
    if quota_exceeded:
        print(f"[중단] API 할당량 초과로 처리 중단")
    print(f"[소요 시간] {elapsed_time:.1f}초 ({elapsed_time/60:.1f}분)")
    if len(bills) > 0:
        print(f"[평균] 의안당 {elapsed_time/len(bills):.1f}초")
    
    return (success_count, error_count, quota_exceeded)

def main():
    ap = argparse.ArgumentParser(
        description="DB에 저장된 의안들을 50개씩 배치로 처리하여 AI 요약 생성 (기본 모델: gemini-2.5-flash)"
    )
    ap.add_argument("--model", default="gemini-2.5-flash", 
                   help="Gemini 모델명 (기본: gemini-2.5-flash)")
    ap.add_argument("--batch-size", type=int, default=50, 
                   help="한 번에 처리할 의안 수 (기본: 50)")
    ap.add_argument("--start-date", default="2025-01-01", 
                   help="처리 시작 날짜 (기본: 2025-01-01)")
    ap.add_argument("--timeout", type=int, default=60, 
                   help="모델 호출 타임아웃(초)")
    ap.add_argument("--sleep", type=float, default=2.5, 
                   help="요청 간 sleep 시간(초, 기본: 2.5)")
    ap.add_argument("--auto-continue", action="store_true", default=True,
                   help="자동으로 다음 배치 진행 (기본: True)")
    ap.add_argument("--max-batches", type=int, default=None,
                   help="최대 배치 수 (None이면 무제한)")
    ap.add_argument("--api-keys", type=str, default=None,
                   help="API 키 목록 (쉼표로 구분, 예: key1,key2,key3)")
    
    args = ap.parse_args()
    
    # API 키 목록 설정
    api_keys = []
    if args.api_keys:
        # 명령줄 인자에서 가져오기
        api_keys = [key.strip() for key in args.api_keys.split(",") if key.strip()]
    else:
        # 환경변수에서 가져오기 (여러 개 가능: GEMINI_API_KEY_1, GEMINI_API_KEY_2, ...)
        i = 1
        while True:
            key = os.environ.get(f"GEMINI_API_KEY_{i}")
            if not key:
                break
            api_keys.append(key)
            i += 1
        
        # 기본 GEMINI_API_KEY도 추가
        default_key = os.environ.get("GEMINI_API_KEY")
        if default_key:
            api_keys.insert(0, default_key)
    
    if not api_keys:
        print("오류: API 키가 제공되지 않았습니다.", file=sys.stderr)
        print("해결: --api-keys 옵션 사용 또는 GEMINI_API_KEY 환경변수 설정", file=sys.stderr)
        sys.exit(2)
    
    # API 키 관리자 생성
    api_key_manager = APIKeyManager(api_keys)
    
    total_success = 0
    total_error = 0
    batch_num = 0
    
    print("=" * 60)
    print("AI 요약 자동 배치 처리 시작")
    print(f"사용 가능한 API 키: {len(api_keys)}개")
    print("=" * 60)
    print()
    
    while True:
        batch_num += 1
        if args.max_batches and batch_num > args.max_batches:
            print(f"\n[완료] 최대 배치 수({args.max_batches})에 도달했습니다.")
            break
        
        print(f"\n{'=' * 60}")
        print(f"배치 #{batch_num} 시작")
        print(f"{'=' * 60}")
        
        success, error, quota_exceeded = process_batch(
            model_name=args.model,
            batch_size=args.batch_size,
            start_date=args.start_date,
            timeout=args.timeout,
            base_sleep=args.sleep,
            api_key_manager=api_key_manager
        )
        
        total_success += success
        total_error += error
        
        # API 할당량 초과 시 중단
        if quota_exceeded:
            print(f"\n{'=' * 60}")
            print(f"[중단] API 할당량 초과로 처리 중단")
            print(f"{'=' * 60}")
            break
        
        # 처리할 의안이 없으면 종료
        if success == 0 and error == 0:
            print(f"\n{'=' * 60}")
            print(f"[완료] 모든 의안 처리 완료")
            print(f"{'=' * 60}")
            break
        
        # 자동 진행 옵션이 꺼져있으면 중단
        if not args.auto_continue:
            print(f"\n{'=' * 60}")
            print(f"[중단] --auto-continue 옵션이 꺼져있어 중단합니다.")
            print(f"{'=' * 60}")
            break
        
        # 다음 배치로 진행
        print(f"\n[다음 배치] 3초 후 자동으로 다음 배치를 시작합니다...")
        time.sleep(3)
    
    print(f"\n{'=' * 60}")
    print(f"전체 처리 결과")
    print(f"{'=' * 60}")
    print(f"  총 배치 수: {batch_num}개")
    print(f"  총 성공: {total_success}개")
    print(f"  총 실패: {total_error}개")
    print(f"  총 처리: {total_success + total_error}개")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()

