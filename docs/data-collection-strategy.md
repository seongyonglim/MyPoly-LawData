# 데이터 수집 및 매핑 전략

## 개요

3개의 API에서 데이터를 수집하여 통합 데이터베이스에 저장하는 전략을 정의합니다.

## 데이터 수집 순서

### 1단계: 의안 정보 수집
**API**: 의안정보 통합 API  
**대상 테이블**: `bills`

**수집 주기**:
- 초기: 전체 의안 수집 (22대 국회)
- 이후: 일일 배치 (신규/업데이트된 의안만)

**수집 데이터**:
- BILL_ID (PK)
- BILL_NO
- BILL_NM → title
- ERACO → era
- BILL_KND → bill_kind
- PPSR_KND → proposer_kind
- PPSR_NM → proposer_name
- PPSL_DT → proposal_date
- JRCMIT_NM → committee
- RGS_CONF_RSLT → result
- RGS_RSLN_DT → result_date
- LINK_URL → link_url

**후처리**:
- AI 요약 및 카테고리 분류 (기존 Gemini 코드 활용)
- summary, categories, vote_for, vote_against 필드 업데이트

### 2단계: 국회의원 정보 수집
**API**: 국회의원 정보 통합 API  
**대상 테이블**: `assembly_members`

**수집 주기**:
- 초기: 전체 의원 정보 수집 (22대 국회)
- 이후: 의원 변경 시 (보궐선거, 정당 변경 등)

**수집 데이터**:
- NAAS_CD → member_id (PK)
- NAAS_NM → name
- PLPT_NM → party
- ELECD_NM → district
- BLNG_CMIT_NM → committee
- GTELT_ERACO → era
- NTR_DIV → gender

**주의사항**:
- MEMBER_NO (표결정보 API)와 NAAS_CD가 동일한지 확인 필요
- 동일하지 않다면 매핑 테이블 필요

### 3단계: 표결 정보 수집
**API**: 국회의원 본회의 표결정보 API  
**대상 테이블**: `votes`

**수집 주기**:
- 표결 발생 시 실시간 또는 일일 배치
- 의안별로 표결 정보 수집

**수집 데이터**:
- BILL_ID → bill_id (FK → bills.bill_id)
- MEMBER_NO → member_id (FK → assembly_members.member_id)
- RESULT_VOTE_MOD → vote_result
- VOTE_DATE → vote_date

**주의사항**:
- BILL_ID가 bills 테이블에 존재하는지 확인 (FK 제약)
- MEMBER_NO가 assembly_members 테이블에 존재하는지 확인
- MEMBER_NO와 NAAS_CD 매핑 필요 시 별도 처리

## 데이터 매핑 로직

### 필드명 매핑 규칙

```python
# 의안정보 API → DB
BILL_MAPPING = {
    "BILL_ID": "bill_id",
    "BILL_NO": "bill_no",
    "BILL_NM": "title",
    "ERACO": "era",
    "BILL_KND": "bill_kind",
    "PPSR_KND": "proposer_kind",
    "PPSR_NM": "proposer_name",
    "PPSL_DT": "proposal_date",
    "JRCMIT_NM": "committee",
    "RGS_CONF_RSLT": "result",
    "RGS_RSLN_DT": "result_date",
    "LINK_URL": "link_url",
}

# 표결정보 API → DB
VOTE_MAPPING = {
    "BILL_ID": "bill_id",
    "BILL_NO": "bill_no",
    "BILL_NAME": "title",  # 참고용 (이미 bills에 있음)
    "MEMBER_NO": "member_id",
    "HG_NM": "name",  # 참고용
    "RESULT_VOTE_MOD": "vote_result",
    "VOTE_DATE": "vote_date",
    "POLY_NM": "party",  # 참고용
    "ORIG_NM": "district",  # 참고용
}

# 의원정보 API → DB
MEMBER_MAPPING = {
    "NAAS_CD": "member_id",
    "NAAS_NM": "name",
    "PLPT_NM": "party",
    "ELECD_NM": "district",
    "BLNG_CMIT_NM": "committee",
    "GTELT_ERACO": "era",
    "NTR_DIV": "gender",
}
```

### 데이터 타입 변환

```python
def convert_bill_data(api_response):
    """의안정보 API 응답을 DB 형식으로 변환"""
    return {
        "bill_id": api_response.get("BILL_ID"),
        "bill_no": api_response.get("BILL_NO"),
        "title": api_response.get("BILL_NM"),
        "era": int(api_response.get("ERACO", 0)) if api_response.get("ERACO") else None,
        "bill_kind": api_response.get("BILL_KND"),
        "proposer_kind": api_response.get("PPSR_KND"),
        "proposer_name": api_response.get("PPSR_NM"),
        "proposal_date": parse_date(api_response.get("PPSL_DT")),
        "committee": api_response.get("JRCMIT_NM"),
        "result": api_response.get("RGS_CONF_RSLT"),
        "result_date": parse_date(api_response.get("RGS_RSLN_DT")),
        "link_url": api_response.get("LINK_URL"),
    }
```

## 데이터 정합성 검증

### 1. FK 제약 검증
- 표결 정보 수집 시 BILL_ID가 bills 테이블에 존재하는지 확인
- 표결 정보 수집 시 MEMBER_NO가 assembly_members 테이블에 존재하는지 확인

### 2. 중복 데이터 처리
- **의안**: BILL_ID 기준으로 UPSERT (존재하면 업데이트, 없으면 INSERT)
- **의원**: member_id 기준으로 UPSERT
- **표결**: (bill_id, member_id) 조합으로 UNIQUE 제약, UPSERT

### 3. 데이터 업데이트 감지
- 의안 정보: proposal_date 또는 updated_at 기준으로 변경 감지
- 표결 정보: vote_date 기준으로 신규 표결 감지

## 수집 스크립트 구조

```
scripts/
├── collect_bills.py          # 의안 정보 수집
├── collect_members.py         # 의원 정보 수집
├── collect_votes.py           # 표결 정보 수집
├── api_mapper.py              # 필드 매핑 유틸리티
└── data_validator.py          # 데이터 정합성 검증
```

## 에러 처리 및 재시도

### API 호출 실패 시
- 최대 3회 재시도 (지수 백오프)
- 실패한 데이터는 별도 로그 저장
- 일일 배치 실패 시 다음 배치에서 재시도

### 데이터 검증 실패 시
- FK 제약 위반: 로그 기록 후 스킵
- 필수 필드 누락: 기본값 설정 또는 스킵
- 데이터 타입 오류: 변환 실패 시 NULL 처리

## 성능 최적화

### 배치 처리
- API 호출은 페이지네이션으로 배치 처리
- DB INSERT는 배치 단위로 일괄 처리 (예: 100건씩)

### 캐싱
- 의원 정보는 변경 빈도가 낮으므로 메모리 캐싱
- 의안 정보는 최근 N일치만 캐싱

### 인덱스 활용
- BILL_ID, member_id 등 FK 필드에 인덱스 생성
- 조회 성능 최적화를 위한 복합 인덱스 고려

## 모니터링

### 수집 현황 추적
- 일일 수집 건수
- 실패 건수 및 원인
- 데이터 업데이트 현황

### 알림
- 수집 실패 시 알림
- 데이터 정합성 오류 시 알림
- API 호출 제한 경고

