# 데이터 수집 스크립트

## 개요
국회 의안, 표결 결과, 의원 정보를 수집하는 스크립트입니다.

**중요**: 모든 스크립트는 **2025년 데이터만** 수집합니다 (2025-01-01 이후).

## 스크립트 목록

### 1. 의원 정보 수집
```bash
python scripts/db/collect_22nd_members_complete.py
```
- 22대 국회의원 정보 수집
- `assembly_members` 테이블에 저장
- 한 번만 실행하면 됩니다 (의원 정보는 변경이 적음)

### 2. 의안 정보 수집
```bash
# 2025-01-01부터 현재까지 (기본값)
python scripts/db/collect_bills_from_date.py

# 특정 날짜부터
python scripts/db/collect_bills_from_date.py 20250101

# 특정 기간
python scripts/db/collect_bills_from_date.py 20250101 20251231
```
- 의안 정보 수집
- `bills` 테이블에 저장
- **2024년 데이터는 자동으로 필터링됩니다**
- 중복 방지: `ON CONFLICT (bill_id) DO UPDATE` 사용

### 3. 표결 정보 수집
```bash
# 2025-01-01부터 현재까지 (기본값)
python scripts/db/collect_votes_from_date.py

# 특정 날짜부터
python scripts/db/collect_votes_from_date.py 20250101

# 특정 기간
python scripts/db/collect_votes_from_date.py 20250101 20251231
```
- 표결 결과 수집
- `votes` 테이블에 저장
- **2025년 의안의 표결만 수집합니다** (2024년 의안 제외)
- **2024년 표결 데이터는 자동으로 필터링됩니다**
- 중복 방지: 사전 체크 + `ON CONFLICT DO NOTHING` 사용

## 중복 방지 메커니즘

### 의안 데이터
- `bill_id`가 PRIMARY KEY이므로 자동으로 중복 방지
- `ON CONFLICT (bill_id) DO UPDATE`로 기존 데이터 업데이트

### 표결 데이터
- 사전 중복 체크: `(bill_id, member_no, vote_date, vote_result)` 조합 확인
- `ON CONFLICT (bill_id, member_no, vote_date) DO NOTHING` 사용
- 같은 의안, 같은 의원, 같은 날짜에 여러 번 투표 가능 (찬성/반대/기권)

## 2024년 데이터 필터링

모든 스크립트는 다음 필터를 적용합니다:
- **의안 수집**: `proposal_date >= '2025-01-01'` 강제 적용
- **표결 수집**: 
  - 2025년 의안만 대상 (`proposal_date >= '2025-01-01'`)
  - `vote_date >= '2025-01-01'` 강제 적용

## 환경 변수
`.env` 파일에 다음 변수가 필요합니다:
- `BILL_SERVICE_KEY`: 공공데이터포털 의안정보 API 키
- `ASSEMBLY_SERVICE_KEY`: 열린국회정보 API 키
- `LOCAL_DB_HOST`, `LOCAL_DB_NAME`, `LOCAL_DB_USER`, `LOCAL_DB_PASSWORD`, `LOCAL_DB_PORT`: 로컬 DB 정보

## 주기적 실행 권장

### 매일 실행 (cron 또는 스케줄러)
```bash
# 의안 정보 수집 (최근 7일)
python scripts/db/collect_bills_from_date.py $(date -d "7 days ago" +%Y%m%d)

# 표결 정보 수집 (최근 7일)
python scripts/db/collect_votes_from_date.py $(date -d "7 days ago" +%Y%m%d)
```

### 주간 실행
```bash
# 의안 정보 전체 업데이트
python scripts/db/collect_bills_from_date.py

# 표결 정보 전체 업데이트
python scripts/db/collect_votes_from_date.py
```

## 주의사항

1. **2024년 데이터는 수집되지 않습니다**: 스크립트에 강제 필터가 적용되어 있습니다.
2. **중복 데이터는 자동으로 처리됩니다**: 같은 스크립트를 여러 번 실행해도 안전합니다.
3. **API 호출 제한**: 스크립트는 API 호출 간격을 두고 실행됩니다 (의안: 1초, 표결: 0.5초).
