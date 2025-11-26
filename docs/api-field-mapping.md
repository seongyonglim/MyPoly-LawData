# API 필드 매핑 문서

## 개요

3개의 API에서 제공하는 필드명이 서로 다르므로, 통합 데이터베이스 설계를 위해 필드 매핑이 필요합니다.

## API 목록

### 1. 의안정보 통합 API
- **제공기관**: 열린국회정보
- **API 주소**: https://open.assembly.go.kr/portal/data/service/selectServicePage.do/OOWY4R001216HX11440
- **인증**: API Key (Encoded/Decoded 동일)

### 2. 국회의원 본회의 표결정보 API
- **제공기관**: 열린국회정보
- **API 주소**: https://www.data.go.kr/data/15125948/openapi.do
- **인증**: API Key (Encoded/Decoded 동일)

### 3. 국회의원 정보 통합 API
- **제공기관**: 열린국회정보
- **API 주소**: https://www.data.go.kr/data/15126133/openapi.do
- **인증**: API Key (Encoded/Decoded 동일)

## 필드 매핑 테이블

### 의안 정보 필드 매핑

| 통합 DB 필드명 | 의안정보 통합 API | 표결정보 API | 비고 |
|------------|----------------|------------|------|
| bill_id | BILL_ID | BILL_ID | ✅ 동일 (확인 필요) |
| bill_no | BILL_NO | BILL_NO | ✅ 동일 (확인 필요) |
| title | BILL_NM | BILL_NAME | ⚠️ 필드명 다름 (값은 동일할 것으로 추정) |
| era | ERACO | AGE | ⚠️ 필드명 다름 (대수) |
| bill_kind | BILL_KND | - | 의안정보 API만 제공 |
| proposer_kind | PPSR_KND | - | 의안정보 API만 제공 |
| proposer_name | PPSR_NM | - | 의안정보 API만 제공 |
| proposal_session | PPSL_SESS | - | 의안정보 API만 제공 |
| proposal_date | PPSL_DT | - | 의안정보 API만 제공 |
| committee | JRCMIT_NM | - | 의안정보 API만 제공 |
| result | RGS_CONF_RSLT | - | 의안정보 API만 제공 |
| result_date | RGS_RSLN_DT | - | 의안정보 API만 제공 |
| link_url | LINK_URL | - | 의안정보 API만 제공 |

### 국회의원 정보 필드 매핑

| 통합 DB 필드명 | 표결정보 API | 의원정보 통합 API | 비고 |
|------------|------------|----------------|------|
| member_id | MEMBER_NO | NAAS_CD | ⚠️ 필드명 다름 (값 동일 여부 확인 필요) |
| name | HG_NM | NAAS_NM | ⚠️ 필드명 다름 (값은 동일할 것으로 추정) |
| party | POLY_NM | PLPT_NM | ⚠️ 필드명 다름 (값은 동일할 것으로 추정) |
| district | ORIG_NM | ELECD_NM | ⚠️ 필드명 다름 (값은 동일할 것으로 추정) |
| committee | - | BLNG_CMIT_NM | 의원정보 API만 제공 |
| era | AGE | GTELT_ERACO | ⚠️ 필드명 다름 (대수) |
| gender | - | NTR_DIV | 의원정보 API만 제공 |

### 표결 정보 필드 매핑

| 통합 DB 필드명 | 표결정보 API | 비고 |
|------------|------------|------|
| vote_id | - | 자체 생성 (PK) |
| bill_id | BILL_ID | FK → bills.bill_id |
| member_id | MEMBER_NO | FK → assembly_members.member_id |
| vote_result | RESULT_VOTE_MOD | 찬성/반대/기권/불참 |
| vote_date | VOTE_DATE | 표결 일시 |

## 매핑 전략

### 1. 공통 식별자 확인 필요
- **BILL_ID**: 의안정보 API와 표결정보 API에서 동일한 값인지 확인 필요
- **MEMBER_NO vs NAAS_CD**: 국회의원 식별자가 동일한지 확인 필요

### 2. 필드명 통일 전략
- DB 테이블에는 통합 필드명 사용
- API 응답 파싱 시 각 API의 원본 필드명을 통합 필드명으로 매핑
- 매핑 로직은 별도 모듈로 분리 (예: `api_mapper.py`)

### 3. 데이터 수집 순서
1. **의안정보 통합 API** → `bills` 테이블에 의안 기본 정보 저장
2. **국회의원 정보 통합 API** → `assembly_members` 테이블에 의원 정보 저장
3. **표결정보 API** → `votes` 테이블에 표결 정보 저장 (BILL_ID, MEMBER_NO로 FK 연결)

## 확인 필요 사항

### ✅ 확인 완료
- [x] 의안정보 API 실제 응답 확인 (2025-01-XX)
- [x] XML 응답 형식 확인
- [x] 실제 필드명 확인 (소문자 변환됨)

### 🔴 긴급 확인 필요
- [ ] 표결정보 API 엔드포인트 및 파라미터 확인 (현재 500 에러)
- [ ] 의원정보 API 엔드포인트 및 파라미터 확인 (현재 500 에러)
- [ ] BILL_ID가 의안정보 API와 표결정보 API에서 동일한 형식/값인지
- [ ] MEMBER_NO와 NAAS_CD가 동일한 식별자인지

### 🟡 검토 필요
- [x] 의안정보 API 실제 응답 형식 (XML) ✅
- [ ] 표결정보 API 실제 응답 형식
- [ ] 의원정보 API 실제 응답 형식
- [ ] 필드값의 데이터 타입 (문자열/숫자/날짜 형식)
- [ ] NULL/빈값 처리 방식
- [ ] 한글 인코딩 방식 (UTF-8 등)

### 🟢 추가 기능
- [x] API 응답 샘플 수집 및 검증 (의안정보 API 완료)
- [ ] 필드 매핑 테스트 스크립트 작성
- [ ] 데이터 정합성 검증 로직

## 실제 테스트 결과

자세한 내용은 `docs/api-test-results.md` 참고

### 의안정보 API 실제 필드명
- **billId** (BILL_ID) - 소문자로 변환됨
- **billName** (BILL_NM) - 소문자로 변환됨
- **billNo** (BILL_NO) - 소문자로 변환됨
- **passGubn** - 계류의안/처리완료 등 (새로 발견)
- **procStageCd** - 접수/심사 등 진행단계 (새로 발견)
- **proposeDt** (PPSL_DT) - 제안일
- **proposerKind** (PPSR_KND) - 제안자구분
- **summary** - 제안이유 및 주요내용

## 다음 단계

1. [ ] 실제 API 응답 샘플 확인 스크립트 실행
2. [ ] 공통 식별자 (BILL_ID, MEMBER_NO/NAAS_CD) 동일성 검증
3. [ ] 필드 매핑 모듈 구현
4. [ ] DB 설계 업데이트 (실제 API 필드 반영)

