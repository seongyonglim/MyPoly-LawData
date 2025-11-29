# 최종 파일 정리 분석 보고서

## 📋 분석 일시
2025년 11월

## 🔍 Git 추적 파일 분석

### CSV 파일 (9개) - Git에 추적됨

**현재 상태**:
- `assembly_members.csv` - Git 추적 중
- `assembly_members_fixed.csv` - Git 추적 중
- `bills.csv` - Git 추적 중
- `bills_fixed.csv` - Git 추적 중
- `votes.csv` - Git 추적 중
- `votes_fixed.csv` - Git 추적 중
- `proc_stage_mapping.csv` - Git 추적 중
- `proc_stage_mapping_fixed.csv` - Git 추적 중

**분석 결과**:
- ✅ 코드에서 참조되지 않음
- ✅ 데이터 수집은 API → DB 직접 저장 방식
- ✅ 마이그레이션 시도 중 생성된 임시 파일
- ✅ 현재 서비스에서 사용하지 않음
- ✅ 향후 기능에서도 사용 계획 없음

**결론**: **삭제 가능** ✅

---

### SQL 파일 (8개)

#### 필수 유지 파일 (1개)
- ✅ `scripts/db/create_tables_postgresql.sql` - **필수 유지**
  - 테이블 생성에 사용
  - `init_tables_on_startup.py`에서 참조
  - `create_tables_in_cloud_sql.sh`에서 참조
  - 문서에서 여러 곳에서 참조

#### 삭제 가능 파일 (7개)
- ❌ `local_data.sql` - 마이그레이션 시도 중 생성
- ❌ `local_data_fixed.sql` - 마이그레이션 시도 중 생성
- ❌ `local_data_no_extensions.sql` - 마이그레이션 시도 중 생성
- ❌ `local_data_utf8.sql` - 마이그레이션 시도 중 생성
- ❌ `local_data_final.sql` - 마이그레이션 시도 중 생성
- ❌ `local_data_final_clean.sql` - 마이그레이션 시도 중 생성
- ❌ `local_data_inserts.sql` - 마이그레이션 시도 중 생성

**분석 결과**:
- ✅ 코드에서 참조되지 않음
- ✅ 마이그레이션 완료로 더 이상 불필요
- ✅ .gitignore에 `*.sql`이 있지만 이미 Git에 추적됨
- ✅ 삭제 후 Git에서 제거 필요

**결론**: **삭제 가능** ✅

---

## 📝 문서 업데이트 필요

다음 문서들에서 구버전 마이그레이션 방법을 언급하고 있지만, 문서 자체는 유지:

- `docs/gcp_next_steps_after_sql.md` - `local_data.sql` 언급
- `docs/gcp_step_by_step_guide.md` - `local_data.sql` 언급
- `docs/gcp_setup_guide.md` - `local_data.sql` 언급
- `scripts/gcp/setup_cloud_sql_complete.sh` - 구버전 마이그레이션 방법 언급

**조치**: 문서는 유지하되, 최신 방법(`migrate_direct_public_ip.py`)을 참조하도록 업데이트 권장

---

## ✅ 최종 정리 계획

### 삭제할 파일 (16개)

**CSV 파일 (8개)**:
1. `assembly_members.csv`
2. `assembly_members_fixed.csv`
3. `bills.csv`
4. `bills_fixed.csv`
5. `votes.csv`
6. `votes_fixed.csv`
7. `proc_stage_mapping.csv`
8. `proc_stage_mapping_fixed.csv`

**SQL 파일 (7개)**:
1. `local_data.sql`
2. `local_data_fixed.sql`
3. `local_data_no_extensions.sql`
4. `local_data_utf8.sql`
5. `local_data_final.sql`
6. `local_data_final_clean.sql`
7. `local_data_inserts.sql`

**스크립트 (1개)**:
- `scripts/gcp/setup_cloud_sql_complete.sh` - 구버전 마이그레이션 방법 언급 (업데이트 필요하지만 삭제는 안 함)

---

## 🔒 안전성 검증

### 현재 서비스에 영향 없음 확인
- ✅ CSV 파일: 코드에서 참조되지 않음
- ✅ SQL 덤프 파일: 코드에서 참조되지 않음
- ✅ 데이터 수집: API → DB 직접 저장
- ✅ 테이블 생성: `create_tables_postgresql.sql` 유지

### 향후 기능에 영향 없음 확인
- ✅ 데이터 수집: API에서 직접 수집
- ✅ 데이터 마이그레이션: `migrate_direct_public_ip.py` 사용
- ✅ 테이블 생성: `create_tables_postgresql.sql` 유지

---

## 📊 정리 후 예상 효과

- **Git 저장소 크기 감소**: 약 40MB (CSV + SQL 파일)
- **프로젝트 구조 명확화**: 불필요한 파일 제거
- **유지보수 용이성 향상**: 핵심 파일만 유지

---

**결론**: 위 15개 파일은 안전하게 삭제 가능합니다. ✅

