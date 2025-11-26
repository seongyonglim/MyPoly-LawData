# 프로덕션 DB 설계 (최종)

> 실제 앱 배포를 위한 완전한 데이터베이스 설계
> 
> **기반 데이터**: 
> - 의안정보 API: 1,000건 분석
> - 의원정보 API: 300건 분석  
> - 표결정보 API: 298건 분석

---

## 목차

1. [핵심 테이블](#1-핵심-테이블)
2. [사용자 관련 테이블](#2-사용자-관련-테이블)
3. [매핑 및 설정 테이블](#3-매핑-및-설정-테이블)
4. [인덱스 전략](#인덱스-전략)
5. [데이터 무결성](#데이터-무결성)
6. [마이그레이션 가이드](#마이그레이션-가이드)

---

## 1. 핵심 테이블

### 1.1 bills (의안 정보)

**데이터 소스**: 의안정보 통합 API  
**분석 샘플**: 1,000건  
**실제 필드**: 10개

```sql
CREATE TABLE bills (
    -- 기본 정보 (PK)
    bill_id VARCHAR(50) PRIMARY KEY COMMENT '의안ID (billId)',
    
    -- 의안 기본 정보 (API 제공)
    bill_no VARCHAR(50) COMMENT '의안번호 (billNo)',
    title VARCHAR(500) NOT NULL COMMENT '의안명 (billName)',
    proposal_date DATE COMMENT '제안일 (proposeDt)',
    proposer_kind VARCHAR(50) COMMENT '제안자구분 (proposerKind: 의원/정부)',
    
    -- 진행 정보 (API 제공)
    proc_stage_cd VARCHAR(50) COMMENT '진행단계 코드 (procStageCd: 접수/심사/본회의)',
    pass_gubn VARCHAR(50) COMMENT '처리구분 (passGubn: 계류의안/처리완료)',
    proc_date DATE COMMENT '처리일 (procDt)',
    general_result VARCHAR(500) COMMENT '일반 결과 (generalResult)',
    
    -- 원문 데이터 (API 제공)
    summary_raw TEXT COMMENT '제안이유 및 주요내용 원문 (summary)',
    
    -- AI 처리 결과 (자체 생성)
    summary TEXT COMMENT 'AI 요약 결과 (Gemini)',
    categories JSON COMMENT '카테고리 분류 결과 (최대 2개)',
    vote_for JSON COMMENT '찬성 시 정치성향 가중치 (예: {"P": 1, "U": 1})',
    vote_against JSON COMMENT '반대 시 정치성향 가중치 (예: {"M": 1, "T": 1})',
    
    -- 메타 정보
    proc_stage_order INT COMMENT '진행 단계 순서 (1=접수, 2=심사, 3=본회의, 4=처리완료)',
    proposer_count INT DEFAULT 1 COMMENT '제안자 수 (대표 발의자 외 추가 인원)',
    link_url VARCHAR(500) COMMENT '상세 링크 URL (의안 상세 페이지)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 인덱스
    INDEX idx_bill_no (bill_no),
    INDEX idx_proposal_date (proposal_date),
    INDEX idx_proc_stage_cd (proc_stage_cd),
    INDEX idx_pass_gubn (pass_gubn),
    INDEX idx_proc_stage_order (proc_stage_order),
    INDEX idx_created_at (created_at)
) COMMENT='의안 정보';
```

**JSON 필드 예시**:
```json
// categories
["경제", "보건"]

// vote_for
{"P": 1, "U": 1}

// vote_against
{"M": 1, "T": 1}
```

---

### 1.2 assembly_members (국회의원 정보)

**데이터 소스**: 국회의원 정보 통합 API  
**분석 샘플**: 300건  
**실제 필드**: 23개

```sql
CREATE TABLE assembly_members (
    -- 기본 정보 (PK)
    member_id VARCHAR(50) PRIMARY KEY COMMENT '의원코드 (NAAS_CD)',
    
    -- 이름 정보 (API 제공)
    name VARCHAR(100) NOT NULL COMMENT '의원명 (NAAS_NM)',
    name_chinese VARCHAR(100) COMMENT '한자명 (NAAS_CH_NM)',
    name_english VARCHAR(200) COMMENT '영문명 (NAAS_EN_NM, 35% NULL)',
    
    -- 정당 및 선거 정보 (API 제공)
    party VARCHAR(100) COMMENT '정당명 (PLPT_NM)',
    district VARCHAR(200) COMMENT '선거구 (ELECD_NM, 12% NULL)',
    district_type VARCHAR(100) COMMENT '선거구 구분명 (ELECD_DIV_NM)',
    
    -- 위원회 정보 (API 제공)
    committee VARCHAR(500) COMMENT '소속위원회명 (BLNG_CMIT_NM, 9% NULL)',
    current_committee VARCHAR(200) COMMENT '현재 위원회명 (CMIT_NM, 91% NULL)',
    
    -- 경력 정보 (API 제공)
    era VARCHAR(200) COMMENT '당선 대수 (GTELT_ERACO: 제22대, 제20대 등)',
    election_type VARCHAR(50) COMMENT '선거 구분명 (RLCT_DIV_NM: 초선/재선/3선)',
    
    -- 개인 정보 (API 제공)
    gender VARCHAR(10) COMMENT '성별 (NTR_DIV: 남/여)',
    birth_date DATE COMMENT '생년월일 (BIRDY_DT)',
    birth_type VARCHAR(10) COMMENT '생년 구분 코드 (BIRDY_DIV_CD: 음/양)',
    duty_name VARCHAR(100) COMMENT '직책명 (DTY_NM, 76% NULL)',
    
    -- 연락처 정보 (API 제공, 대부분 NULL)
    phone VARCHAR(50) COMMENT '전화번호 (NAAS_TEL_NO, 91% NULL)',
    email VARCHAR(200) COMMENT '이메일 (NAAS_EMAIL_ADDR, 91% NULL)',
    homepage_url VARCHAR(500) COMMENT '홈페이지 (NAAS_HP_URL, 92% NULL)',
    office_room VARCHAR(100) COMMENT '사무실 호실 (OFFM_RNUM_NO, 91% NULL)',
    
    -- 보좌진 정보 (API 제공, 대부분 NULL)
    aide_name VARCHAR(500) COMMENT '보좌관 (AIDE_NM, 91% NULL)',
    secretary_name VARCHAR(500) COMMENT '선임비서관 (CHF_SCRT_NM, 91% NULL)',
    assistant_name VARCHAR(500) COMMENT '비서관 (SCRT_NM, 91% NULL)',
    
    -- 기타 정보 (API 제공)
    photo_url VARCHAR(500) COMMENT '사진 URL (NAAS_PIC)',
    brief_history TEXT COMMENT '약력 (BRF_HST, 85% NULL)',
    
    -- 매핑용 필드 (표결정보 API와 연결)
    mona_cd VARCHAR(50) COMMENT '표결정보 API의 MONA_CD (매핑용)',
    member_no VARCHAR(50) COMMENT '표결정보 API의 MEMBER_NO (매핑용)',
    
    -- 메타 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 인덱스
    INDEX idx_name (name),
    INDEX idx_party (party),
    INDEX idx_district (district),
    INDEX idx_mona_cd (mona_cd),
    INDEX idx_member_no (member_no),
    INDEX idx_era (era)
) COMMENT='국회의원 정보';
```

---

### 1.3 votes (국회의원 표결 정보)

**데이터 소스**: 국회의원 본회의 표결정보 API  
**분석 샘플**: 298건  
**실제 필드**: 26개

```sql
CREATE TABLE votes (
    -- 기본 정보 (PK)
    vote_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 의안 정보 (FK)
    bill_id VARCHAR(50) NOT NULL COMMENT '의안ID (BILL_ID, FK → bills.bill_id)',
    bill_no VARCHAR(50) COMMENT '의안번호 (BILL_NO, 참고용)',
    bill_name VARCHAR(500) COMMENT '의안명 (BILL_NAME, 참고용)',
    
    -- 의원 정보 (FK)
    member_no VARCHAR(50) COMMENT '의원번호 (MEMBER_NO, 표결정보 API)',
    mona_cd VARCHAR(50) COMMENT '의원코드 MONA (MONA_CD, 표결정보 API)',
    member_id VARCHAR(50) COMMENT '의원코드 (FK → assembly_members.member_id, 매핑 후 설정)',
    member_name VARCHAR(100) COMMENT '의원명 (HG_NM, 참고용)',
    member_name_chinese VARCHAR(100) COMMENT '의원 한자명 (HJ_NM, 참고용)',
    
    -- 정당 및 선거구 정보 (API 제공)
    party_name VARCHAR(100) COMMENT '정당명 (POLY_NM, 참고용)',
    party_code VARCHAR(50) COMMENT '정당 코드 (POLY_CD, 참고용)',
    district_name VARCHAR(200) COMMENT '선거구명 (ORIG_NM, 참고용)',
    district_code VARCHAR(50) COMMENT '선거구 코드 (ORIG_CD, 참고용)',
    
    -- 표결 정보 (API 제공)
    vote_result VARCHAR(50) COMMENT '표결결과 (RESULT_VOTE_MOD: 찬성/반대/기권/불참)',
    vote_date DATETIME COMMENT '표결 일시 (VOTE_DATE)',
    
    -- 기타 정보 (API 제공)
    era INT COMMENT '대수 (AGE)',
    session_code VARCHAR(50) COMMENT '회기 코드 (SESSION_CD)',
    current_committee VARCHAR(200) COMMENT '현재 위원회 (CURR_COMMITTEE)',
    current_committee_id VARCHAR(50) COMMENT '현재 위원회 ID (CURR_COMMITTEE_ID)',
    currents_code VARCHAR(50) COMMENT '현황 코드 (CURRENTS_CD)',
    dept_code VARCHAR(50) COMMENT '부서 코드 (DEPT_CD)',
    display_order INT COMMENT '표시 순서 (DISP_ORDER)',
    law_title VARCHAR(500) COMMENT '법률 제목 (LAW_TITLE)',
    bill_url VARCHAR(500) COMMENT '의안 URL (BILL_URL)',
    bill_name_url VARCHAR(500) COMMENT '의안명 URL (BILL_NAME_URL)',
    
    -- 메타 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키 및 제약조건
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES assembly_members(member_id) ON DELETE SET NULL,
    UNIQUE KEY unique_bill_member_vote (bill_id, member_no, vote_date),
    
    -- 인덱스
    INDEX idx_bill_id (bill_id),
    INDEX idx_member_id (member_id),
    INDEX idx_member_no (member_no),
    INDEX idx_mona_cd (mona_cd),
    INDEX idx_vote_result (vote_result),
    INDEX idx_vote_date (vote_date),
    INDEX idx_party_name (party_name)
) COMMENT='국회의원 본회의 표결 정보';
```

---

## 2. 사용자 관련 테이블

### 2.1 user_votes (사용자 투표)

**데이터 소스**: 자체 구현

```sql
CREATE TABLE user_votes (
    -- 기본 정보 (PK)
    user_vote_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 의안 정보 (FK)
    bill_id VARCHAR(50) NOT NULL COMMENT '의안ID (FK → bills.bill_id)',
    
    -- 사용자 정보
    user_id VARCHAR(100) NOT NULL COMMENT '사용자 식별자 (세션ID 또는 사용자ID)',
    
    -- 투표 정보
    vote_result ENUM('찬성', '반대') NOT NULL COMMENT '투표 결과 (응원해요=찬성, 아쉬워요=반대)',
    
    -- 메타 정보
    vote_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키 및 제약조건
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_bill (user_id, bill_id),
    
    -- 인덱스
    INDEX idx_bill_id (bill_id),
    INDEX idx_user_id (user_id),
    INDEX idx_vote_result (vote_result),
    INDEX idx_vote_date (vote_date)
) COMMENT='사용자 투표 정보';
```

---

### 2.2 user_political_profile (사용자 정치성향 프로필)

**데이터 소스**: 자체 구현 (정치성향 테스트)

```sql
CREATE TABLE user_political_profile (
    -- 기본 정보 (PK)
    user_id VARCHAR(100) PRIMARY KEY COMMENT '사용자 식별자',
    
    -- 정치성향 점수 (8개 축, 4쌍)
    -- P (공공 중심) / M (시장 중심)
    p_score INT DEFAULT 0 COMMENT '공공 중심 (P) 점수 (초기 0~5)',
    m_score INT DEFAULT 0 COMMENT '시장 중심 (M) 점수 (초기 0~5)',
    
    -- U (보편 적용) / T (대상 맞춤)
    u_score INT DEFAULT 0 COMMENT '보편 적용 (U) 점수 (초기 0~5)',
    t_score INT DEFAULT 0 COMMENT '대상 맞춤 (T) 점수 (초기 0~5)',
    
    -- N (필요 기반) / S (성과 기반)
    n_score INT DEFAULT 0 COMMENT '필요 기반 (N) 점수 (초기 0~5)',
    s_score INT DEFAULT 0 COMMENT '성과 기반 (S) 점수 (초기 0~5)',
    
    -- O (개방 실험) / R (절차 안정)
    o_score INT DEFAULT 0 COMMENT '개방 실험 (O) 점수 (초기 0~5)',
    r_score INT DEFAULT 0 COMMENT '절차 안정 (R) 점수 (초기 0~5)',
    
    -- 메타 정보
    test_completed BOOLEAN DEFAULT FALSE COMMENT '정치성향 테스트 완료 여부',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 인덱스
    INDEX idx_test_completed (test_completed)
) COMMENT='사용자 정치성향 프로필';
```

**점수 업데이트 규칙**:
- 초기 테스트: 각 축별 0~5점 (배타적 쌍 방식)
- 투표 시: 의안의 `vote_for` 또는 `vote_against` 가중치 누적

---

### 2.3 member_political_profile (의원 정치성향 프로필)

**데이터 소스**: 자체 계산 (표결 이력 기반)

```sql
CREATE TABLE member_political_profile (
    -- 기본 정보 (PK)
    member_id VARCHAR(50) PRIMARY KEY COMMENT '의원코드 (FK → assembly_members.member_id)',
    
    -- 정치성향 점수 (8개 축, 표결 이력 기반 계산)
    p_score INT DEFAULT 0 COMMENT '공공 중심 (P) 점수',
    m_score INT DEFAULT 0 COMMENT '시장 중심 (M) 점수',
    u_score INT DEFAULT 0 COMMENT '보편 적용 (U) 점수',
    t_score INT DEFAULT 0 COMMENT '대상 맞춤 (T) 점수',
    n_score INT DEFAULT 0 COMMENT '필요 기반 (N) 점수',
    s_score INT DEFAULT 0 COMMENT '성과 기반 (S) 점수',
    o_score INT DEFAULT 0 COMMENT '개방 실험 (O) 점수',
    r_score INT DEFAULT 0 COMMENT '절차 안정 (R) 점수',
    
    -- 통계 정보
    total_votes INT DEFAULT 0 COMMENT '총 표결 참여 수',
    last_calculated_at TIMESTAMP COMMENT '마지막 계산 일시',
    
    -- 메타 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 외래키
    FOREIGN KEY (member_id) REFERENCES assembly_members(member_id) ON DELETE CASCADE,
    
    -- 인덱스
    INDEX idx_total_votes (total_votes)
) COMMENT='의원 정치성향 프로필 (표결 이력 기반)';
```

**점수 계산 방법**:
- 의원의 표결 이력(`votes`)을 기반으로 계산
- 찬성 투표: 해당 의안의 `vote_for` 가중치 누적
- 반대 투표: 해당 의안의 `vote_against` 가중치 누적

---

## 3. 매핑 및 설정 테이블

### 3.1 proc_stage_mapping (진행 단계 매핑)

```sql
CREATE TABLE proc_stage_mapping (
    -- 기본 정보 (PK)
    stage_code VARCHAR(50) PRIMARY KEY COMMENT '진행 단계 코드',
    stage_name VARCHAR(50) NOT NULL COMMENT '진행 단계 이름',
    stage_order INT NOT NULL COMMENT '진행 단계 순서 (1, 2, 3...)',
    description TEXT COMMENT '설명',
    
    -- 인덱스
    INDEX idx_stage_order (stage_order)
) COMMENT='진행 단계 매핑';

-- 초기 데이터
INSERT INTO proc_stage_mapping (stage_code, stage_name, stage_order, description) VALUES
('접수', '접수', 1, '의안이 접수된 단계'),
('심사', '심사', 2, '위원회 심사 단계'),
('본회의', '본회의', 3, '본회의 심의 단계'),
('처리완료', '처리완료', 4, '처리가 완료된 단계'),
('계류의안', '계류의안', 0, '계류 중인 의안');
```

---

### 3.2 member_id_mapping (의원 식별자 매핑)

**목적**: 표결정보 API의 `MEMBER_NO`, `MONA_CD`와 의원정보 API의 `NAAS_CD`를 매핑

```sql
CREATE TABLE member_id_mapping (
    -- 기본 정보 (PK)
    mapping_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 의원 식별자
    naas_cd VARCHAR(50) NOT NULL COMMENT '의원정보 API의 NAAS_CD',
    member_no VARCHAR(50) COMMENT '표결정보 API의 MEMBER_NO',
    mona_cd VARCHAR(50) COMMENT '표결정보 API의 MONA_CD',
    
    -- 검증 정보
    member_name VARCHAR(100) COMMENT '의원명 (검증용)',
    is_verified BOOLEAN DEFAULT FALSE COMMENT '매핑 검증 완료 여부',
    
    -- 메타 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 인덱스
    UNIQUE KEY unique_naas_cd (naas_cd),
    INDEX idx_member_no (member_no),
    INDEX idx_mona_cd (mona_cd),
    INDEX idx_member_name (member_name),
    INDEX idx_is_verified (is_verified)
) COMMENT='의원 식별자 매핑';
```

---

### 3.3 bill_similarity (의안 유사도)

**목적**: 의안 간 유사도 저장 (유사 의안 추천용)

```sql
CREATE TABLE bill_similarity (
    -- 기본 정보 (PK)
    bill_id_1 VARCHAR(50) NOT NULL COMMENT '의안ID 1',
    bill_id_2 VARCHAR(50) NOT NULL COMMENT '의안ID 2',
    
    -- 유사도 정보
    similarity_score FLOAT NOT NULL COMMENT '유사도 점수 (0.0 ~ 1.0)',
    similarity_method VARCHAR(50) COMMENT '유사도 계산 방법 (category/embedding/keyword)',
    
    -- 메타 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키 및 제약조건
    PRIMARY KEY (bill_id_1, bill_id_2),
    FOREIGN KEY (bill_id_1) REFERENCES bills(bill_id) ON DELETE CASCADE,
    FOREIGN KEY (bill_id_2) REFERENCES bills(bill_id) ON DELETE CASCADE,
    
    -- 인덱스
    INDEX idx_similarity_score (similarity_score DESC),
    INDEX idx_bill_id_1 (bill_id_1),
    INDEX idx_bill_id_2 (bill_id_2),
    INDEX idx_similarity_method (similarity_method)
) COMMENT='의안 유사도';
```

**유사도 계산 방법**:
- `category`: 카테고리 기반 유사도 (간단, 즉시 구현 가능)
- `embedding`: AI 임베딩 벡터 유사도 (정확, 추가 개발 필요)
- `keyword`: 키워드 유사도 (중간)

---

## 인덱스 전략

### 조회 성능 최적화

#### bills 테이블
- `idx_proposal_date`: 날짜 기준 정렬/필터링
- `idx_proc_stage_cd`: 진행 단계별 조회
- `idx_created_at`: 최신 의안 조회

#### votes 테이블
- `idx_bill_id`: 의안별 표결 조회
- `idx_member_id`: 의원별 표결 조회
- `idx_vote_result`: 표결 결과별 통계

#### user_votes 테이블
- `idx_bill_id`: 의안별 투표 통계
- `idx_user_id`: 사용자별 투표 이력

#### assembly_members 테이블
- `idx_name`: 이름 검색
- `idx_party`: 정당별 조회

---

## 데이터 무결성

### 외래키 제약조건

1. **votes.bill_id** → `bills.bill_id` (CASCADE)
2. **votes.member_id** → `assembly_members.member_id` (SET NULL)
3. **user_votes.bill_id** → `bills.bill_id` (CASCADE)
4. **member_political_profile.member_id** → `assembly_members.member_id` (CASCADE)
5. **bill_similarity** → `bills.bill_id` (CASCADE)

### UNIQUE 제약조건

1. **votes**: `(bill_id, member_no, vote_date)` - 동일 의안, 동일 의원, 동일 시간 중복 방지
2. **user_votes**: `(user_id, bill_id)` - 사용자는 의안당 1회만 투표 가능

---

## 마이그레이션 가이드

### 1단계: 기본 테이블 생성

```sql
-- 1. bills 테이블
-- 2. assembly_members 테이블
-- 3. votes 테이블
-- 4. user_votes 테이블
```

### 2단계: 매핑 테이블 생성

```sql
-- 1. proc_stage_mapping 테이블 + 초기 데이터
-- 2. member_id_mapping 테이블
```

### 3단계: 정치성향 테이블 생성

```sql
-- 1. user_political_profile 테이블
-- 2. member_political_profile 테이블
```

### 4단계: 유사도 테이블 생성 (선택)

```sql
-- 1. bill_similarity 테이블
```

---

## 데이터 수집 전략

### 초기 데이터 수집

1. **의안 정보**: 전체 의안 수집 (22대 국회)
2. **의원 정보**: 전체 의원 정보 수집 (22대 국회)
3. **표결 정보**: 처리완료된 의안의 표결 정보 수집
4. **의원 식별자 매핑**: `member_id_mapping` 테이블 생성

### 일일 배치 작업

1. **의안 정보**: 신규/업데이트된 의안 수집
2. **표결 정보**: 전날 표결된 의안의 표결 정보 수집
3. **AI 요약**: 신규 의안에 대해 Gemini API로 요약 및 카테고리 분류

### 주간 배치 작업

1. **의원 정보**: 의원 정보 업데이트 (정당 변경, 위원회 변경 등)
2. **의원 정치성향**: 표결 이력 기반 의원 정치성향 재계산

### 선택적 배치 작업

1. **의안 유사도**: 카테고리 기반 유사도 계산 (주간)
2. **의안 유사도 (고급)**: AI 임베딩 기반 유사도 계산 (월간)

---

## 주요 쿼리 예시

### 의안 상세 조회

```sql
SELECT 
    b.*,
    psm.stage_name,
    psm.stage_order,
    (SELECT COUNT(*) FROM user_votes uv WHERE uv.bill_id = b.bill_id AND uv.vote_result = '찬성') as support_count,
    (SELECT COUNT(*) FROM user_votes uv WHERE uv.bill_id = b.bill_id AND uv.vote_result = '반대') as oppose_count
FROM bills b
LEFT JOIN proc_stage_mapping psm ON b.proc_stage_cd = psm.stage_code
WHERE b.bill_id = ?
```

### 의원별 표결 통계

```sql
SELECT 
    am.member_id,
    am.name,
    am.party,
    COUNT(*) as total_votes,
    SUM(CASE WHEN v.vote_result = '찬성' THEN 1 ELSE 0 END) as support_count,
    SUM(CASE WHEN v.vote_result = '반대' THEN 1 ELSE 0 END) as oppose_count
FROM assembly_members am
LEFT JOIN votes v ON am.member_id = v.member_id
WHERE am.member_id = ?
GROUP BY am.member_id, am.name, am.party
```

### 유사 의안 추천 (카테고리 기반)

```sql
SELECT 
    b2.bill_id,
    b2.title,
    b2.summary,
    b2.categories,
    bs.similarity_score
FROM bills b1
INNER JOIN bill_similarity bs ON b1.bill_id = bs.bill_id_1
INNER JOIN bills b2 ON bs.bill_id_2 = b2.bill_id
WHERE b1.bill_id = ?
  AND bs.similarity_method = 'category'
ORDER BY bs.similarity_score DESC
LIMIT 3
```

### 사용자-의원 일치율 계산

```sql
SELECT 
    am.member_id,
    am.name,
    am.party,
    am.photo_url,
    (
        ABS(up.p_score - mp.p_score) +
        ABS(up.m_score - mp.m_score) +
        ABS(up.u_score - mp.u_score) +
        ABS(up.t_score - mp.t_score) +
        ABS(up.n_score - mp.n_score) +
        ABS(up.s_score - mp.s_score) +
        ABS(up.o_score - mp.o_score) +
        ABS(up.r_score - mp.r_score)
    ) as difference_score,
    100 - (
        ABS(up.p_score - mp.p_score) +
        ABS(up.m_score - mp.m_score) +
        ABS(up.u_score - mp.u_score) +
        ABS(up.t_score - mp.t_score) +
        ABS(up.n_score - mp.n_score) +
        ABS(up.s_score - mp.s_score) +
        ABS(up.o_score - mp.o_score) +
        ABS(up.r_score - mp.r_score)
    ) / 8 as match_percentage
FROM user_political_profile up
CROSS JOIN member_political_profile mp
INNER JOIN assembly_members am ON mp.member_id = am.member_id
WHERE up.user_id = ?
ORDER BY match_percentage DESC
LIMIT 3
```

---

## 다음 단계

1. **DB 스키마 생성**: 위 SQL 스크립트 실행
2. **초기 데이터 수집**: API를 통한 데이터 수집
3. **의원 식별자 매핑**: `member_id_mapping` 테이블 생성 및 매핑
4. **AI 요약 배치**: 신규 의안에 대한 AI 요약 및 카테고리 분류
5. **의원 정치성향 계산**: 표결 이력 기반 의원 정치성향 계산

---

## 참고 문서

- 대량 분석 결과: `api_samples/bulk_analysis/`
- 필드 매핑: `docs/api-field-mapping.md`
- 크롤링 전략: `docs/crawling-strategy-updated.md`
- 정치성향 시스템: `docs/political-profile-system.md`



