# 유틸리티 스크립트

## AI 요약 관련

- **`check_ai_progress.py`**: AI 요약 진행 상황 확인
  - 사용법: `python scripts/utils/check_ai_progress.py`
  - 전체 의안 중 AI 요약 완료/미완료 통계 및 다음 처리 대상 확인

- **`check_skipped_bills_in_range.py`**: 처리된 의안 범위 내에서 건너뛰어진 의안 확인
  - 사용법: `python scripts/utils/check_skipped_bills_in_range.py`
  - 처리된 의안 번호 범위 내에서 누락된 의안 찾기

## 사용법

모든 스크립트는 프로젝트 루트에서 실행:

```bash
# AI 요약 진행 상황 확인
python scripts/utils/check_ai_progress.py

# 건너뛰어진 의안 확인
python scripts/utils/check_skipped_bills_in_range.py
```

## 환경 변수

모든 스크립트는 다음 환경 변수가 필요합니다:

- `DB_HOST`: 데이터베이스 호스트 (기본값: localhost)
- `DB_NAME`: 데이터베이스 이름 (기본값: mypoly_lawdata)
- `DB_USER`: 데이터베이스 사용자 (기본값: postgres)
- `DB_PASSWORD`: 데이터베이스 비밀번호 (필수)
- `DB_PORT`: 데이터베이스 포트 (기본값: 5432)

