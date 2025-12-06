# 데이터베이스 스크립트

## 📋 주요 수집 스크립트

### 의안 데이터 수집
- **`collect_bills_from_date.py`**: 특정 날짜 범위의 의안 정보 수집
  - 사용법: `python scripts/db/collect_bills_from_date.py [시작일] [종료일]`
  - 예시: `python scripts/db/collect_bills_from_date.py 20250101 20251205`

### 표결 데이터 수집
- **`collect_votes_from_date.py`**: 특정 날짜 범위의 표결 정보 수집
  - 사용법: `python scripts/db/collect_votes_from_date.py [시작일] [종료일]`
  - 예시: `python scripts/db/collect_votes_from_date.py 20250101 20251205`

### 의원 데이터 수집
- **`collect_22nd_members_complete.py`**: 22대 국회 의원 정보 수집

## 🔧 데이터 품질 관리 스크립트

### 종합 점검 및 수정
- **`comprehensive_data_fix.py`**: 전체 데이터 품질 점검 및 수정 (링크 URL, 의원 매핑)
- **`final_comprehensive_fix.py`**: 최종 전체 데이터 품질 점검 및 수정
- **`comprehensive_field_check.py`**: 전체 필드 완성도 확인

### 특정 필드 보완
- **`improve_missing_proposer_names.py`**: 제안자 이름 누락 보완
- **`improve_member_mapping.py`**: 의원 정보 매핑 개선
- **`generate_bill_links.py`**: 의안 링크 URL 생성

### 검증 스크립트
- **`final_data_validation.py`**: 최종 데이터 무결성 검증
- **`validate_data_quality.py`**: 데이터 품질 검증
- **`comprehensive_data_quality_report.py`**: 종합 데이터 품질 리포트 생성

## 🔍 점검 스크립트

### 필드 확인
- **`check_all_api_fields.py`**: API 응답의 모든 필드 확인
- **`check_proposer_final.py`**: 제안자 정보 최종 확인
- **`check_member_mapping.py`**: 의원 매핑 상태 확인
- **`check_proposer_column.py`**: 제안자 컬럼 확인
- **`check_missing_column_translations.py`**: 누락된 컬럼 번역 확인
- **`check_votes_null_columns.py`**: 표결 데이터 NULL 컬럼 확인
- **`check_foreign_keys.py`**: 외래키 확인

### 테이블 구조
- **`show_table_structure.py`**: 테이블 구조 확인
- **`list_tables.py`**: 테이블 목록 확인
- **`analyze_unused_tables.py`**: 사용되지 않는 테이블 분석
- **`analyze_member_id_mapping.py`**: 의원 ID 매핑 분석

## 🗄️ 데이터베이스 스키마

- **`create_tables_postgresql.sql`**: PostgreSQL 테이블 생성 스크립트
- **`create_indexes.sql`**: 인덱스 생성 스크립트
- **`check_indexes.sql`**: 인덱스 확인 스크립트

## 🛠️ 유틸리티 스크립트

- **`init_tables_on_startup.py`**: 시작 시 테이블 초기화
- **`update_member_ids_from_votes.py`**: 표결 정보에서 의원 ID 업데이트
- **`fix_duplicate_votes_final.py`**: 중복 표결 데이터 수정
- **`remove_similarity_method_column.py`**: 유사도 메서드 컬럼 제거
- **`delete_unused_tables.py`**: 사용되지 않는 테이블 삭제

## 📝 사용 가이드

### 초기 설정
1. 데이터베이스 연결 정보를 `.env` 파일에 설정
2. `create_tables_postgresql.sql` 실행하여 테이블 생성

### 데이터 수집
1. 의원 정보 수집: `python scripts/db/collect_22nd_members_complete.py`
2. 의안 정보 수집: `python scripts/db/collect_bills_from_date.py`
3. 표결 정보 수집: `python scripts/db/collect_votes_from_date.py`

### 데이터 품질 관리
1. 종합 점검: `python scripts/db/comprehensive_data_fix.py`
2. 제안자 정보 보완: `python scripts/db/improve_missing_proposer_names.py`
3. 의원 매핑 개선: `python scripts/db/improve_member_mapping.py`

## ⚠️ 주의사항

- 모든 스크립트는 환경 변수에서 데이터베이스 연결 정보를 읽습니다
- API 키는 환경 변수로 관리하며, 코드에 하드코딩하지 않습니다
- 데이터 수집 전에 데이터베이스 백업을 권장합니다

