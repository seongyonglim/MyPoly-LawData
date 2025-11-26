# Figma 화면 분석 - 의안 상세 화면

## 화면 구성 요소별 데이터 요구사항 분석

### 1. 상단 헤더
**표시 내용**: "의안 상세"
**필요 데이터**: 없음 (정적 텍스트)
**구현 가능성**: ✅ 구현 가능

---

### 2. AI 분석 배너
**표시 내용**: "AI가 안건을 분석했어요"
**필요 데이터**: 없음 (정적 텍스트)
**구현 가능성**: ✅ 구현 가능

---

### 3. 의안 기본 정보 카드

#### 3.1 카테고리 태그 + 날짜
**표시 내용**: 
- 카테고리 태그: "디지털" (예시)
- 날짜: "2025.08.08"

**필요 데이터**:
- 카테고리: `bills.categories` (JSON 배열, AI 분류 결과)
- 날짜: `bills.proposal_date` (제안일)

**API 제공 여부**:
- ✅ 카테고리: AI 요약 시 생성 (Gemini API)
- ✅ 날짜: 의안정보 API (`proposeDt`)

**DB 필드**: 
- `bills.categories` (JSON)
- `bills.proposal_date` (DATE)

**구현 가능성**: ✅ 구현 가능

#### 3.2 의안 제목
**표시 내용**: "필수 의료 안정적 보장 추구"

**필요 데이터**:
- 의안 제목: `bills.title`

**API 제공 여부**:
- ✅ 의안정보 API (`billName`)

**DB 필드**: 
- `bills.title` (VARCHAR)

**구현 가능성**: ✅ 구현 가능

#### 3.3 제안자 정보
**표시 내용**: "이수진 의원 외 11명"

**필요 데이터**:
- 제안자명: `bills.proposer_name`
- 제안자 수: 별도 계산 필요

**API 제공 여부**:
- ✅ 의안정보 API (`PPSR_NM` - 대표 발의자만 제공)
- ⚠️ 전체 발의자 수는 의안 상세 페이지에서 파싱 필요

**DB 필드**: 
- `bills.proposer_name` (VARCHAR)
- `bills.proposer_count` (INT) - 추가 필요

**구현 가능성**: ⚠️ 부분 구현 가능 (대표 발의자만 표시)

#### 3.4 심사 진행 단계
**표시 내용**: 
- "심사 진행 단계" (라벨)
- "1" (단계 번호)
- "접수" (단계명)

**필요 데이터**:
- 진행 단계 코드: `bills.proc_stage_cd`
- 진행 단계 번호: 단계 코드를 숫자로 변환

**API 제공 여부**:
- ✅ 의안정보 API (`procStageCd`: "접수", "심사" 등)

**DB 필드**: 
- `bills.proc_stage_cd` (VARCHAR)
- `bills.proc_stage_order` (INT) - 단계 순서 (추가 필요)

**구현 가능성**: ✅ 구현 가능 (단계 순서 매핑 테이블 필요)

---

### 4. AI 요약 섹션

#### 4.1 AI 요약 제목
**표시 내용**: "AI 요약"

**필요 데이터**: 없음 (정적 텍스트)
**구현 가능성**: ✅ 구현 가능

#### 4.2 AI 요약 본문
**표시 내용**: "필수의료가 지역 격차와 인프라 부족으로 위기에 놓였고..."

**필요 데이터**:
- AI 요약: `bills.summary`

**API 제공 여부**:
- ✅ Gemini API로 생성 (이미 구현됨)

**DB 필드**: 
- `bills.summary` (TEXT)

**구현 가능성**: ✅ 구현 가능

#### 4.3 더 많은 내용 보러가기 / 원본보기 버튼
**필요 데이터**:
- 원본 링크: `bills.link_url`

**API 제공 여부**:
- ✅ 의안정보 API (`LINK_URL`)

**DB 필드**: 
- `bills.link_url` (VARCHAR)

**구현 가능성**: ✅ 구현 가능

---

### 5. 사용자 투표 섹션

#### 5.1 질문 텍스트
**표시 내용**: "해당 안건에 대해 어떻게 생각하세요?"

**필요 데이터**: 없음 (정적 텍스트)
**구현 가능성**: ✅ 구현 가능

#### 5.2 투표 버튼
**표시 내용**: "응원해요" / "아쉬워요"

**필요 데이터**:
- 사용자 투표 결과: `user_votes.vote_result`
- 사용자 ID: `user_votes.user_id`

**API 제공 여부**:
- ❌ 자체 구현 필요

**DB 필드**: 
- `user_votes.user_vote_id` (PK)
- `user_votes.bill_id` (FK)
- `user_votes.user_id` (VARCHAR) - 세션ID 또는 사용자 식별자
- `user_votes.vote_result` (ENUM: '찬성', '반대') - "응원해요"=찬성, "아쉬워요"=반대
- `user_votes.vote_date` (TIMESTAMP)

**구현 가능성**: ✅ 구현 가능 (자체 DB)

#### 5.3 투표 결과 보기
**필요 데이터**:
- 해당 의안의 전체 투표 통계
- 찬성/반대 비율

**DB 쿼리**:
```sql
SELECT 
    COUNT(CASE WHEN vote_result = '찬성' THEN 1 END) as support_count,
    COUNT(CASE WHEN vote_result = '반대' THEN 1 END) as oppose_count,
    COUNT(*) as total_count
FROM user_votes
WHERE bill_id = ?
```

**구현 가능성**: ✅ 구현 가능

---

### 6. 나와 유사한 성향의 국회의원 섹션

#### 6.1 섹션 제목
**표시 내용**: "나와 유사한 성향의 국회의원은?"

**필요 데이터**: 없음 (정적 텍스트)
**구현 가능성**: ✅ 구현 가능

#### 6.2 의원 카드 (1위, 2위, 3위)
**표시 내용**:
- 순위 배지 (1위, 2위, 3위)
- 의원 사진
- 일치율 (85%, 60%, 60%)
- 의원 이름
- 정당명

**필요 데이터**:
- 의원 정보: `assembly_members` 테이블
- 일치율: 사용자 정치성향과 의원의 표결 이력 비교 결과

**API 제공 여부**:
- ✅ 의원정보 API (`NAAS_NM`, `PLPT_NM`, `NAAS_PIC`)
- ⚠️ 일치율: 자체 계산 필요

**DB 필드**: 
- `assembly_members.member_id` (PK)
- `assembly_members.name` (VARCHAR)
- `assembly_members.party` (VARCHAR)
- `assembly_members.photo_url` (VARCHAR) - `NAAS_PIC` 매핑

**추가 필요**:
- 사용자 정치성향 테이블 (별도 설계 필요)
- 의원별 표결 이력 분석 로직

**구현 가능성**: ⚠️ 부분 구현 가능
- 의원 정보 표시: ✅ 가능
- 일치율 계산: 사용자 정치성향 테스트 및 의원 표결 이력 분석 필요

---

### 7. 이 안건과 유사한 주제 섹션

#### 7.1 섹션 제목
**표시 내용**: "이 안건과 유사한 주제"

**필요 데이터**: 없음 (정적 텍스트)
**구현 가능성**: ✅ 구현 가능

#### 7.2 유사 의안 카드 (3개)
**표시 내용**:
- 아이콘 이미지
- 의안 제목: "공동주택관리법 어쩌고저쩌고"
- 요약: "분석하고 더 많은 정보 매칭..."
- 카테고리 태그: "경제", "보건"

**필요 데이터**:
- 유사 의안 목록: 카테고리, 키워드, AI 임베딩 기반 유사도 계산
- 의안 제목: `bills.title`
- 요약: `bills.summary`
- 카테고리: `bills.categories`

**API 제공 여부**:
- ✅ 의안정보 API로 의안 목록 조회 가능
- ⚠️ 유사도 계산: 자체 구현 필요

**DB 필드**: 
- `bills.bill_id` (PK)
- `bills.title` (VARCHAR)
- `bills.summary` (TEXT)
- `bills.categories` (JSON)

**추가 필요**:
- 유사도 계산 알고리즘
  - 방법 1: 카테고리 매칭 (간단)
  - 방법 2: AI 임베딩 벡터 유사도 (정확)
  - 방법 3: 키워드 유사도

**구현 가능성**: ⚠️ 부분 구현 가능
- 기본: 카테고리 기반 유사 의안 추천 ✅
- 고급: AI 임베딩 기반 유사도 계산 (추가 개발 필요)

---

## 데이터 연결 및 테이블 설계

### 핵심 테이블 관계

```
bills (의안)
├── bill_id (PK)
├── title
├── summary (AI 요약)
├── categories (AI 분류)
├── proposal_date
├── proposer_name
├── proc_stage_cd
└── link_url

user_votes (사용자 투표)
├── user_vote_id (PK)
├── bill_id (FK → bills.bill_id)
├── user_id
├── vote_result ('찬성'/'반대')
└── vote_date

assembly_members (국회의원)
├── member_id (PK)
├── name
├── party
└── photo_url

votes (국회의원 표결)
├── vote_id (PK)
├── bill_id (FK → bills.bill_id)
├── member_id (FK → assembly_members.member_id)
├── vote_result
└── vote_date
```

### 추가 필요 테이블

#### 1. proc_stage_mapping (진행 단계 매핑)
```sql
CREATE TABLE proc_stage_mapping (
    stage_code VARCHAR(50) PRIMARY KEY,
    stage_name VARCHAR(50) NOT NULL,
    stage_order INT NOT NULL,
    description TEXT
);

INSERT INTO proc_stage_mapping VALUES
('접수', '접수', 1, '의안이 접수된 단계'),
('심사', '심사', 2, '위원회 심사 단계'),
('본회의', '본회의', 3, '본회의 심의 단계'),
('처리완료', '처리완료', 4, '처리가 완료된 단계');
```

#### 2. user_political_profile (사용자 정치성향) - 추후 구현
```sql
CREATE TABLE user_political_profile (
    user_id VARCHAR(100) PRIMARY KEY,
    p_score INT,  -- 공공 중심 (P) 점수
    m_score INT,  -- 시장 중심 (M) 점수
    u_score INT,  -- 보편 적용 (U) 점수
    t_score INT,  -- 대상 맞춤 (T) 점수
    n_score INT,  -- 필요 기반 (N) 점수
    s_score INT,  -- 성과 기반 (S) 점수
    o_score INT,  -- 개방 실험 (O) 점수
    r_score INT,  -- 절차 안정 (R) 점수
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### 3. bill_similarity (의안 유사도) - 추후 구현
```sql
CREATE TABLE bill_similarity (
    bill_id_1 VARCHAR(50),
    bill_id_2 VARCHAR(50),
    similarity_score FLOAT,
    similarity_method VARCHAR(50),  -- 'category', 'embedding', 'keyword'
    PRIMARY KEY (bill_id_1, bill_id_2),
    FOREIGN KEY (bill_id_1) REFERENCES bills(bill_id),
    FOREIGN KEY (bill_id_2) REFERENCES bills(bill_id),
    INDEX idx_similarity_score (similarity_score DESC)
);
```

---

## 구현 가능성 종합

### ✅ 즉시 구현 가능
1. 의안 기본 정보 (제목, 날짜, 카테고리, 제안자)
2. AI 요약 표시
3. 심사 진행 단계 (단계 매핑 테이블 추가 필요)
4. 사용자 투표 기능
5. 유사 의안 추천 (카테고리 기반)

### ⚠️ 부분 구현 가능
1. 제안자 정보: 대표 발의자만 표시 (전체 발의자 수는 추가 파싱 필요)
2. 유사 성향 의원: 의원 정보는 표시 가능, 일치율 계산은 사용자 정치성향 테스트 필요

### ❌ 추가 개발 필요
1. 사용자 정치성향 테스트 및 저장
2. 의원-사용자 일치율 계산 알고리즘
3. AI 임베딩 기반 유사 의안 추천 (고급 기능)

---

## 다음 단계

1. **즉시 구현 가능한 기능부터 개발**
   - 의안 기본 정보 표시
   - AI 요약 표시
   - 사용자 투표 기능
   - 카테고리 기반 유사 의안 추천

2. **추가 테이블 생성**
   - `proc_stage_mapping` 테이블
   - 진행 단계 순서 매핑 데이터 입력

3. **추후 구현 기능**
   - 사용자 정치성향 테스트
   - 의원-사용자 일치율 계산
   - AI 임베딩 기반 유사도 계산

