# 데이터 수집 가이드

## 순서

데이터 수집은 다음 순서로 진행하세요:

### 1단계: 의안 정보 수집
```bash
python scripts/db/collect_bills_from_date.py [시작날짜]
```

- 의안정보 통합 API에서 데이터 수집
- `bills` 테이블에 저장
- 시작날짜 형식: `YYYYMMDD` (예: `20250801`)
- 기본값: `20250801` (2025년 8월 1일 이후)
- 예시: `python scripts/db/collect_bills_from_date.py 20250801`

### 2단계: 국회의원 정보 수집
```bash
python scripts/db/collect_22nd_members_complete.py
```

- 국회의원 정보 통합 API에서 데이터 수집
- `assembly_members` 테이블에 저장
- 22대 국회의원 전체 수집 (약 300명)

### 3단계: 표결 정보 수집
```bash
python scripts/db/collect_votes_from_date.py [시작날짜]
```

- 국회의원 본회의 표결정보 API에서 데이터 수집
- `votes` 테이블에 저장
- **주의**: `bills` 테이블에 데이터가 있어야 함
- 시작날짜 형식: `YYYYMMDD` (예: `20251015`)
- 기본값: `20251015` (2025년 10월 15일 이후)
- 예시: `python scripts/db/collect_votes_from_date.py 20251015`

## 데이터 확인

### PostgreSQL에서 확인
```sql
-- 의안 개수
SELECT COUNT(*) FROM bills;

-- 국회의원 개수
SELECT COUNT(*) FROM assembly_members;

-- 표결 정보 개수
SELECT COUNT(*) FROM votes;

-- 샘플 데이터 확인
SELECT * FROM bills LIMIT 5;
SELECT * FROM assembly_members LIMIT 5;
SELECT * FROM votes LIMIT 5;
```

## 주의사항

1. **API 호출 제한**: 각 스크립트는 API 호출 제한을 고려하여 1초씩 대기합니다.
2. **중복 처리**: `ON CONFLICT`를 사용하여 중복 데이터는 자동으로 업데이트됩니다.
3. **에러 처리**: 일부 데이터 오류는 건너뛰고 계속 진행합니다.

