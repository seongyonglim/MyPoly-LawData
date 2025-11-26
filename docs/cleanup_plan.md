# 프로젝트 정리 계획

**생성일**: 2025-11-26

---

## 📋 정리 원칙

### ✅ 유지해야 할 파일
1. **데이터 수집 스크립트** (API로 데이터 불러오는 것)
2. **현재 사용 중인 파일** (app.py, templates, static 등)
3. **최종 버전 스크립트** (최신/최종 버전)
4. **중요 문서** (현재 상태, 최종 리포트 등)
5. **DB 스키마 파일** (create_tables_postgresql.sql)

### 🗑️ 정리 가능한 파일
1. **중간 단계 스크립트** (최종 버전이 있는 경우)
2. **테스트/디버깅 스크립트** (일회성 사용)
3. **중복된 문서** (구버전, 중간 단계 문서)
4. **사용하지 않는 배치 파일**
5. **임시 파일**

---

## 📁 디렉토리별 정리 계획

### 1. scripts/db/ (60개 파일)

#### ✅ 유지할 스크립트 (데이터 수집/관리)

**데이터 수집 (최종 버전)**
- `collect_bills_from_date.py` - 의안 수집 (날짜 필터)
- `collect_22nd_members_complete.py` - 22대 의원 수집 (최종)
- `collect_votes_from_date.py` - 표결 수집 (날짜 필터)

**데이터 정리/개선 (최종 버전)**
- `fix_duplicate_votes_final.py` - 중복 표결 정리 (최종)
- `improve_missing_proposer_names.py` - 제안자 이름 보완
- `generate_bill_links.py` - 의안 링크 생성

**데이터 검증/리포트**
- `comprehensive_data_quality_report.py` - 데이터 품질 리포트
- `validate_data_quality.py` - 데이터 품질 검증
- `show_table_structure.py` - 테이블 구조 확인

**DB 스키마**
- `create_tables_postgresql.sql` - PostgreSQL 스키마 (최종)

**README**
- `README_data_collection.md` - 데이터 수집 가이드

#### 🗑️ 정리 가능한 스크립트

**구버전/중간 단계 스크립트**
- `collect_bill_data.py` - 구버전 (collect_bills_from_date.py로 대체)
- `collect_member_data.py` - 구버전 (collect_22nd_members_complete.py로 대체)
- `collect_vote_data.py` - 구버전 (collect_votes_from_date.py로 대체)
- `collect_members_all_22nd.py` - 중간 버전
- `collect_all_members.py` - 구버전
- `collect_all_members_fixed.py` - 중간 버전
- `fix_duplicate_votes.py` - 구버전 (fix_duplicate_votes_final.py로 대체)
- `create_member_mapping.py` - 구버전
- `create_member_mapping_improved.py` - 중간 버전
- `create_member_mapping_final.py` - 최종이지만 이미 완료됨
- `extract_proposer_from_title.py` - 구버전 (improve_missing_proposer_names.py로 대체)
- `create_proposer_mapping.py` - 중간 버전

**매핑 개선 스크립트 (이미 완료)**
- `improve_mapping_comprehensive.py` - 이미 완료
- `improve_member_mapping_aggressive.py` - 이미 완료
- `improve_member_mapping_all_eras.py` - 이미 완료
- `fix_member_mapping_final.py` - 이미 완료
- `fix_remaining_members.py` - 이미 완료
- `complete_member_collection_and_mapping.py` - 이미 완료

**분석/체크 스크립트 (일회성)**
- `analyze_bill_status.py` - 일회성 분석
- `analyze_member_mapping_issue.py` - 일회성 분석
- `analyze_unmapped_proposers.py` - 일회성 분석
- `check_api_member_names.py` - 일회성 체크
- `check_api_response_structure.py` - 일회성 체크
- `check_assembly_members.py` - 일회성 체크
- `check_link_url_sample.py` - 일회성 체크
- `check_mapping_issue.py` - 일회성 체크
- `check_missing_22nd_members.py` - 일회성 체크
- `check_pass_gubn_types.py` - 일회성 체크
- `check_proc_stage.py` - 일회성 체크
- `check_proposer_issues.py` - 일회성 체크
- `check_proposer_mapping.py` - 일회성 체크
- `compare_names.py` - 일회성 비교

**검증 스크립트 (일회성)**
- `final_comprehensive_validation.py` - 일회성 검증
- `final_mapping_verification.py` - 일회성 검증
- `verify_all_data_collection.py` - 일회성 검증
- `verify_all_requirements.py` - 일회성 검증
- `verify_bill_link_format.py` - 일회성 검증

**리포트 스크립트 (일회성)**
- `complete_final_report.py` - 일회성 리포트
- `detailed_bill_vote_analysis.py` - 일회성 분석
- `final_proposer_mapping_report.py` - 일회성 리포트

**정리 스크립트 (이미 완료)**
- `cleanup_non_22nd_members.py` - 이미 완료
- `cleanup_old_bill_votes.py` - 이미 완료
- `extract_chairman_from_title.py` - 이미 완료

**테스트 스크립트**
- `test_bill_api_linkurl.py` - 테스트
- `test_link_url.py` - 테스트
- `test_mapping.py` - 테스트

**기타 스크립트**
- `comprehensive_data_fix.py` - 일회성 수정
- `fix_all_missing_data.py` - 일회성 수정
- `fix_missing_data_collection.py` - 일회성 수정
- `find_missing_members.py` - 일회성 찾기
- `init_db.py` - 사용 안 함 (create_tables_postgresql.sql로 대체)

**사용하지 않는 SQL**
- `create_tables.sql` - 구버전 (create_tables_postgresql.sql로 대체)
- `generate_erd_sql.sql` - 사용 안 함

**사용하지 않는 배치 파일**
- `find_postgresql.bat` - 사용 안 함
- `run_dashboard.bat` - 사용 안 함 (대시보드 삭제됨)
- `setup_database.bat` - 구버전
- `setup_database.sh` - 구버전
- `setup_postgresql_18.bat` - 구버전
- `setup_postgresql_with_password.bat` - 구버전
- `setup_postgresql.bat` - 구버전
- `setup_postgresql.sh` - 구버전

**README (중복)**
- `README_member_collection.md` - README_data_collection.md에 통합 가능

#### 📊 scripts/db/ 정리 요약
- **유지**: 약 12개 파일
- **정리**: 약 48개 파일

---

### 2. scripts/ (루트)

#### ✅ 유지할 스크립트
- `test_api_samples.py` - API 샘플 테스트 (참고용)

#### 🗑️ 정리 가능한 스크립트
- `bulk_data_analysis.py` - 일회성 분석
- `find_bill_id.py` - 일회성 찾기

---

### 3. docs/ (42개 파일)

#### ✅ 유지할 문서

**현재 상태/최종 리포트**
- `current_database_structure.md` - 현재 DB 구조 (최신)
- `data_status_for_designers.md` - 디자이너용 리포트 (최신)
- `data_quality_improvements.md` - 데이터 품질 개선 (최신)
- `final_data_collection_report_2025.md` - 최종 수집 리포트

**DB 설계 (최종)**
- `db-design-production.md` - 프로덕션 DB 설계 (최종)

**데이터 수집 가이드**
- `README_data_collection_2025.md` - 데이터 수집 가이드 (최신)

**API 문서**
- `api-authentication.md` - API 인증 가이드
- `api-field-mapping.md` - API 필드 매핑

**README**
- `README.md` - 메인 README

#### 🗑️ 정리 가능한 문서

**구버전/중간 단계 문서**
- `current_db_status.md` - 구버전 (current_database_structure.md로 대체)
- `data_collection_summary.md` - 구버전 (final_data_collection_report_2025.md로 대체)
- `data_collection_improvements.md` - 중간 단계
- `db-design.md` - 구버전 (db-design-production.md로 대체)
- `db-design-final.md` - 중간 버전
- `db-setup-guide.md` - 구버전
- `db-setup-guide-postgresql.md` - 구버전 (참고용으로만)

**일회성 분석 문서**
- `member_mapping_analysis.md` - 일회성 분석
- `api-crawling-results.md` - 일회성 결과
- `bulk-analysis-results.md` - 일회성 결과
- `api-adequacy-review.md` - 일회성 리뷰
- `api-review.md` - 일회성 리뷰
- `api-test-results.md` - 일회성 테스트

**사용하지 않는 가이드**
- `db-dashboard-setup.md` - 대시보드 삭제됨
- `db-visualization-guide.md` - 대시보드 삭제됨
- `db-mysql-vs-postgresql.md` - 이미 결정됨
- `db-selection-guide.md` - 이미 결정됨
- `gcp-postgresql-setup.md` - 사용 안 함
- `db-integration-guide.md` - 구버전

**구현 관련 (참고용으로만)**
- `implementation-checklist.md` - 참고용
- `implementation-roadmap.md` - 참고용
- `implementation-summary.md` - 참고용
- `feature-mapping.md` - 참고용
- `figma-screen-analysis.md` - 참고용
- `figma-sharing-guide.md` - 참고용
- `member-detail-analysis.md` - 참고용
- `political-profile-system.md` - 참고용
- `ai-code-analysis.md` - 참고용
- `crawling-strategy-updated.md` - 참고용
- `data-collection-strategy.md` - 참고용

**임시 파일**
- `final_report_output.txt` - 임시 출력 파일

#### 📊 docs/ 정리 요약
- **유지**: 약 10개 파일
- **정리**: 약 32개 파일

---

### 4. api_samples/ (6개 파일)

#### ✅ 유지할 파일
- 모든 파일 유지 (API 샘플은 참고용으로 중요)

---

### 5. static/, templates/ (현재 사용 중)

#### ✅ 유지할 파일
- 모든 파일 유지 (현재 사용 중)

---

### 6. 루트 파일

#### ✅ 유지할 파일
- `app.py` - Flask 앱 (현재 사용 중)
- `requirements.txt` - 의존성
- `README.md` - 메인 README

#### 🗑️ 정리 가능한 파일
- `test_app.py` - 테스트 스크립트 (일회성)
- `test_search.py` - 테스트 스크립트 (일회성)

---

## 📊 전체 정리 요약

### 정리 가능한 파일 수
- **scripts/db/**: 약 48개 파일
- **scripts/**: 약 2개 파일
- **docs/**: 약 32개 파일
- **루트**: 약 2개 파일
- **총계**: 약 84개 파일

### 유지할 파일 수
- **scripts/db/**: 약 12개 파일
- **scripts/**: 약 1개 파일
- **docs/**: 약 10개 파일
- **api_samples/**: 6개 파일 (모두 유지)
- **static/, templates/**: 모두 유지
- **루트**: 3개 파일
- **총계**: 약 32개 파일

---

## 🎯 정리 실행 계획

### 1단계: 백업 확인
- 정리 전 현재 상태 확인

### 2단계: 스크립트 정리
- 구버전/중간 단계 스크립트 삭제
- 일회성 분석/테스트 스크립트 삭제
- 사용하지 않는 배치 파일 삭제

### 3단계: 문서 정리
- 구버전/중간 단계 문서 삭제
- 일회성 분석 문서 삭제
- 사용하지 않는 가이드 삭제

### 4단계: 최종 확인
- 유지한 파일들이 정상 작동하는지 확인

