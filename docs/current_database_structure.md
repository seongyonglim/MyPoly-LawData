# 📊 현재 데이터베이스 테이블 구조

**최종 업데이트**: 2025-11-26

---

## 📋 테이블 목록 (총 10개)

### 핵심 테이블 (3개)
1. **bills** - 의안 정보 (7,421건)
2. **assembly_members** - 국회의원 정보 (306건)
3. **votes** - 표결 정보 (98,904건)

### 사용자 관련 테이블 (3개)
4. **user_votes** - 사용자 투표 (0건)
5. **user_political_profile** - 사용자 정치성향 프로필 (0건)
6. **member_political_profile** - 의원 정치성향 프로필 (0건)

### 매핑 및 설정 테이블 (4개)
7. **proc_stage_mapping** - 진행 단계 매핑 (5건)
8. **member_id_mapping** - 의원 식별자 매핑 (155건)
9. **bill_similarity** - 의안 유사도 (0건)

---

## 1. bills (의안 정보)

### 기본 정보
- **데이터 개수**: 7,421건
- **Primary Key**: `bill_id` (VARCHAR(50))

### 주요 컬럼

| 컬럼명 | 타입 | NULL | 설명 |
|--------|------|------|------|
| bill_id | VARCHAR(50) | NO | 의안ID (PK) |
| bill_no | VARCHAR(50) | YES | 의안번호 |
| title | VARCHAR(500) | NO | 의안명 |
| proposal_date | DATE | YES | 제안일 |
| proposer_kind | VARCHAR(50) | YES | 제안자구분 (의원/정부/위원장/의장) |
| **proposer_name** | VARCHAR(100) | YES | 제안자 이름 (추가됨) |
| proc_stage_cd | VARCHAR(50) | YES | 진행단계 코드 |
| pass_gubn | VARCHAR(50) | YES | 처리구분 (계류의안/처리의안) |
| proc_date | DATE | YES | 처리일 |
| general_result | VARCHAR(500) | YES | 일반 결과 |
| summary_raw | TEXT | YES | 제안이유 및 주요내용 원문 |
| summary | TEXT | YES | AI 요약 결과 (현재 NULL) |
| categories | JSONB | YES | 카테고리 분류 결과 (현재 NULL) |
| vote_for | JSONB | YES | 찬성 시 정치성향 가중치 (현재 NULL) |
| vote_against | JSONB | YES | 반대 시 정치성향 가중치 (현재 NULL) |
| proc_stage_order | INTEGER | YES | 진행 단계 순서 |
| proposer_count | INTEGER | YES | 제안자 수 (기본값: 1) |
| link_url | VARCHAR(500) | YES | 의안 원문 링크 |
| created_at | TIMESTAMP | YES | 생성일시 |
| updated_at | TIMESTAMP | YES | 수정일시 |

### 인덱스
- `bills_pkey` (bill_id)
- `idx_bill_no` (bill_no)
- `idx_proposal_date` (proposal_date)
- `idx_proc_stage_cd` (proc_stage_cd)
- `idx_pass_gubn` (pass_gubn)
- `idx_proc_stage_order` (proc_stage_order)
- `idx_created_at` (created_at)
- `idx_categories_gin` (categories) - GIN 인덱스
- `idx_vote_for_gin` (vote_for) - GIN 인덱스
- `idx_vote_against_gin` (vote_against) - GIN 인덱스

---

## 2. assembly_members (국회의원 정보)

### 기본 정보
- **데이터 개수**: 306건
- **Primary Key**: `member_id` (VARCHAR(50))

### 주요 컬럼

| 컬럼명 | 타입 | NULL | 설명 |
|--------|------|------|------|
| member_id | VARCHAR(50) | NO | 의원코드 (PK, NAAS_CD) |
| name | VARCHAR(100) | NO | 의원명 |
| name_chinese | VARCHAR(100) | YES | 한자명 |
| name_english | VARCHAR(200) | YES | 영문명 |
| party | VARCHAR(100) | YES | 정당명 |
| district | VARCHAR(200) | YES | 선거구 |
| district_type | VARCHAR(100) | YES | 선거구 구분명 |
| committee | VARCHAR(500) | YES | 소속위원회명 |
| current_committee | VARCHAR(200) | YES | 현재 위원회명 |
| era | VARCHAR(200) | YES | 당선 대수 (제22대 등) |
| election_type | VARCHAR(50) | YES | 선거 구분명 (초선/재선/3선) |
| gender | VARCHAR(10) | YES | 성별 |
| birth_date | DATE | YES | 생년월일 |
| birth_type | VARCHAR(10) | YES | 생년 구분 코드 |
| duty_name | VARCHAR(100) | YES | 직책명 |
| phone | VARCHAR(50) | YES | 전화번호 |
| email | VARCHAR(200) | YES | 이메일 |
| homepage_url | VARCHAR(500) | YES | 홈페이지 URL |
| office_room | VARCHAR(100) | YES | 사무실 호수 |
| aide_name | VARCHAR(500) | YES | 보좌관 이름 |
| secretary_name | VARCHAR(500) | YES | 비서 이름 |
| assistant_name | VARCHAR(500) | YES | 조수 이름 |
| photo_url | VARCHAR(500) | YES | 사진 URL |
| brief_history | TEXT | YES | 약력 |
| mona_cd | VARCHAR(50) | YES | 표결정보 API의 MONA_CD |
| member_no | VARCHAR(50) | YES | 표결정보 API의 MEMBER_NO |
| created_at | TIMESTAMP | YES | 생성일시 |
| updated_at | TIMESTAMP | YES | 수정일시 |

### 인덱스
- `assembly_members_pkey` (member_id)
- `idx_name` (name)
- `idx_party` (party)
- `idx_district` (district)
- `idx_mona_cd` (mona_cd)
- `idx_member_no` (member_no)
- `idx_era` (era)

---

## 3. votes (표결 정보)

### 기본 정보
- **데이터 개수**: 98,904건
- **Primary Key**: `vote_id` (BIGSERIAL)
- **Unique Constraint**: (bill_id, member_no, vote_date)

### 주요 컬럼

| 컬럼명 | 타입 | NULL | 설명 |
|--------|------|------|------|
| vote_id | BIGSERIAL | NO | 표결ID (PK, 자동 증가) |
| bill_id | VARCHAR(50) | NO | 의안ID (FK → bills.bill_id) |
| bill_no | VARCHAR(50) | YES | 의안번호 |
| bill_name | VARCHAR(500) | YES | 의안명 |
| member_no | VARCHAR(50) | YES | 의원번호 (표결정보 API) |
| mona_cd | VARCHAR(50) | YES | MONA 코드 |
| **member_id** | VARCHAR(50) | YES | 의원코드 (FK → assembly_members.member_id) |
| member_name | VARCHAR(100) | YES | 의원명 |
| member_name_chinese | VARCHAR(100) | YES | 의원 한자명 |
| party_name | VARCHAR(100) | YES | 정당명 |
| party_code | VARCHAR(50) | YES | 정당 코드 |
| district_name | VARCHAR(200) | YES | 선거구명 |
| district_code | VARCHAR(50) | YES | 선거구 코드 |
| vote_result | VARCHAR(50) | YES | 표결결과 (찬성/반대/기권/불참) |
| vote_date | TIMESTAMP | YES | 표결일시 |
| era | INTEGER | YES | 국회 대수 |
| session_code | VARCHAR(50) | YES | 회기 코드 |
| current_committee | VARCHAR(200) | YES | 현재 위원회 |
| current_committee_id | VARCHAR(50) | YES | 현재 위원회 ID |
| currents_code | VARCHAR(50) | YES | 현황 코드 |
| dept_code | VARCHAR(50) | YES | 부서 코드 |
| display_order | INTEGER | YES | 표시 순서 |
| law_title | VARCHAR(500) | YES | 법률 제목 |
| bill_url | VARCHAR(500) | YES | 의안 URL |
| bill_name_url | VARCHAR(500) | YES | 의안명 URL |
| created_at | TIMESTAMP | YES | 생성일시 |

### 인덱스
- `votes_pkey` (vote_id)
- `idx_bill_id` (bill_id)
- `idx_member_id` (member_id)
- `idx_member_no` (member_no)
- `idx_mona_cd` (mona_cd)
- `idx_vote_result` (vote_result)
- `idx_vote_date` (vote_date)
- `idx_party_name` (party_name)
- `unique_bill_member_vote` (bill_id, member_no, vote_date)

### 외래키
- `bill_id` → `bills.bill_id` (ON DELETE CASCADE)
- `member_id` → `assembly_members.member_id` (ON DELETE SET NULL)

---

## 4. user_votes (사용자 투표)

### 기본 정보
- **데이터 개수**: 0건
- **Primary Key**: `user_vote_id` (BIGSERIAL)
- **Unique Constraint**: (user_id, bill_id)

### 주요 컬럼

| 컬럼명 | 타입 | NULL | 설명 |
|--------|------|------|------|
| user_vote_id | BIGSERIAL | NO | 사용자 투표ID (PK) |
| bill_id | VARCHAR(50) | NO | 의안ID (FK → bills.bill_id) |
| user_id | VARCHAR(100) | NO | 사용자 식별자 |
| vote_result | ENUM | NO | 투표 결과 (찬성/반대) |
| vote_date | TIMESTAMP | YES | 투표일시 |

### 외래키
- `bill_id` → `bills.bill_id` (ON DELETE CASCADE)

---

## 5. user_political_profile (사용자 정치성향 프로필)

### 기본 정보
- **데이터 개수**: 0건
- **Primary Key**: `user_id` (VARCHAR(100))

### 주요 컬럼

| 컬럼명 | 타입 | NULL | 설명 |
|--------|------|------|------|
| user_id | VARCHAR(100) | NO | 사용자 식별자 (PK) |
| p_score | INTEGER | YES | 공공 중심 점수 (기본값: 0) |
| m_score | INTEGER | YES | 시장 중심 점수 (기본값: 0) |
| u_score | INTEGER | YES | 보편 적용 점수 (기본값: 0) |
| t_score | INTEGER | YES | 대상 맞춤 점수 (기본값: 0) |
| n_score | INTEGER | YES | 필요 기반 점수 (기본값: 0) |
| s_score | INTEGER | YES | 성과 기반 점수 (기본값: 0) |
| o_score | INTEGER | YES | 개방 실험 점수 (기본값: 0) |
| r_score | INTEGER | YES | 절차 안정 점수 (기본값: 0) |
| test_completed | BOOLEAN | YES | 테스트 완료 여부 (기본값: false) |
| created_at | TIMESTAMP | YES | 생성일시 |
| updated_at | TIMESTAMP | YES | 수정일시 |

---

## 6. member_political_profile (의원 정치성향 프로필)

### 기본 정보
- **데이터 개수**: 0건
- **Primary Key**: `member_id` (VARCHAR(50))

### 주요 컬럼

| 컬럼명 | 타입 | NULL | 설명 |
|--------|------|------|------|
| member_id | VARCHAR(50) | NO | 의원코드 (PK, FK → assembly_members.member_id) |
| p_score | INTEGER | YES | 공공 중심 점수 (기본값: 0) |
| m_score | INTEGER | YES | 시장 중심 점수 (기본값: 0) |
| u_score | INTEGER | YES | 보편 적용 점수 (기본값: 0) |
| t_score | INTEGER | YES | 대상 맞춤 점수 (기본값: 0) |
| n_score | INTEGER | YES | 필요 기반 점수 (기본값: 0) |
| s_score | INTEGER | YES | 성과 기반 점수 (기본값: 0) |
| o_score | INTEGER | YES | 개방 실험 점수 (기본값: 0) |
| r_score | INTEGER | YES | 절차 안정 점수 (기본값: 0) |
| total_votes | INTEGER | YES | 총 표결 수 (기본값: 0) |
| last_calculated_at | TIMESTAMP | YES | 마지막 계산일시 |
| created_at | TIMESTAMP | YES | 생성일시 |
| updated_at | TIMESTAMP | YES | 수정일시 |

### 외래키
- `member_id` → `assembly_members.member_id` (ON DELETE CASCADE)

---

## 7. proc_stage_mapping (진행 단계 매핑)

### 기본 정보
- **데이터 개수**: 5건
- **Primary Key**: `stage_code` (VARCHAR(50))

### 주요 컬럼

| 컬럼명 | 타입 | NULL | 설명 |
|--------|------|------|------|
| stage_code | VARCHAR(50) | NO | 진행 단계 코드 (PK) |
| stage_name | VARCHAR(50) | NO | 진행 단계 이름 |
| stage_order | INTEGER | NO | 진행 단계 순서 |
| description | TEXT | YES | 설명 |

---

## 8. member_id_mapping (의원 식별자 매핑)

### 기본 정보
- **데이터 개수**: 155건
- **Primary Key**: `mapping_id` (BIGSERIAL)
- **Unique Constraint**: (naas_cd)

### 주요 컬럼

| 컬럼명 | 타입 | NULL | 설명 |
|--------|------|------|------|
| mapping_id | BIGSERIAL | NO | 매핑ID (PK) |
| naas_cd | VARCHAR(50) | NO | 의원정보 API의 NAAS_CD (Unique) |
| member_no | VARCHAR(50) | YES | 표결정보 API의 MEMBER_NO |
| mona_cd | VARCHAR(50) | YES | 표결정보 API의 MONA_CD |
| member_name | VARCHAR(100) | YES | 의원명 |
| is_verified | BOOLEAN | YES | 검증 여부 (기본값: false) |
| created_at | TIMESTAMP | YES | 생성일시 |
| updated_at | TIMESTAMP | YES | 수정일시 |

---

## 9. bill_similarity (의안 유사도)

### 기본 정보
- **데이터 개수**: 0건
- **Primary Key**: (bill_id_1, bill_id_2)

### 주요 컬럼

| 컬럼명 | 타입 | NULL | 설명 |
|--------|------|------|------|
| bill_id_1 | VARCHAR(50) | NO | 의안ID 1 (FK → bills.bill_id) |
| bill_id_2 | VARCHAR(50) | NO | 의안ID 2 (FK → bills.bill_id) |
| similarity_score | REAL | NO | 유사도 점수 (0.0 ~ 1.0) |
| similarity_method | VARCHAR(50) | YES | 유사도 계산 방법 |
| created_at | TIMESTAMP | YES | 생성일시 |

### 외래키
- `bill_id_1` → `bills.bill_id` (ON DELETE CASCADE)
- `bill_id_2` → `bills.bill_id` (ON DELETE CASCADE)

---

## 📊 테이블 관계도

```
bills (의안)
  ├── votes (표결) [bill_id]
  ├── user_votes (사용자 투표) [bill_id]
  └── bill_similarity (의안 유사도) [bill_id_1, bill_id_2]

assembly_members (국회의원)
  ├── votes (표결) [member_id]
  ├── member_political_profile (의원 정치성향) [member_id]
  └── member_id_mapping (의원 식별자 매핑) [naas_cd]

user_political_profile (사용자 정치성향)
  └── (독립 테이블)

proc_stage_mapping (진행 단계 매핑)
  └── (설정 테이블)
```

---

## 🔑 주요 관계

### 1. bills ↔ votes
- **관계**: 1:N (하나의 의안에 여러 표결 결과)
- **외래키**: `votes.bill_id` → `bills.bill_id`
- **ON DELETE**: CASCADE

### 2. assembly_members ↔ votes
- **관계**: 1:N (한 의원이 여러 표결에 참여)
- **외래키**: `votes.member_id` → `assembly_members.member_id`
- **ON DELETE**: SET NULL

### 3. bills ↔ user_votes
- **관계**: 1:N (하나의 의안에 여러 사용자 투표)
- **외래키**: `user_votes.bill_id` → `bills.bill_id`
- **ON DELETE**: CASCADE

### 4. assembly_members ↔ member_political_profile
- **관계**: 1:1 (한 의원당 하나의 정치성향 프로필)
- **외래키**: `member_political_profile.member_id` → `assembly_members.member_id`
- **ON DELETE**: CASCADE

---

## 📝 참고사항

### 추가된 컬럼
- `bills.proposer_name` - 제안자 이름 (추가됨)

### 현재 NULL인 필드 (나중에 채울 예정)
- `bills.summary` - AI 요약 결과
- `bills.categories` - 카테고리 분류 결과
- `bills.vote_for` - 찬성 시 정치성향 가중치
- `bills.vote_against` - 반대 시 정치성향 가중치

### 사용되지 않는 테이블 (현재 데이터 0건)
- `user_votes` - 사용자 투표 기능 구현 시 사용
- `user_political_profile` - 사용자 정치성향 테스트 기능 구현 시 사용
- `member_political_profile` - 의원 정치성향 계산 기능 구현 시 사용
- `bill_similarity` - 의안 유사도 계산 기능 구현 시 사용

