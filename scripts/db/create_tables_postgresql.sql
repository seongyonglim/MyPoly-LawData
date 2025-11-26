-- ============================================
-- 프로덕션 DB 스키마 생성 스크립트 (PostgreSQL)
-- ============================================
-- 생성일: 2025-01-XX
-- 데이터베이스: PostgreSQL 12 이상 권장
-- ============================================

-- 확장 기능 활성화 (JSONB 인덱싱 등)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. 핵심 테이블
-- ============================================

-- 1.1 bills (의안 정보)
CREATE TABLE IF NOT EXISTS bills (
    -- 기본 정보 (PK)
    bill_id VARCHAR(50) PRIMARY KEY,
    
    -- 의안 기본 정보 (API 제공)
    bill_no VARCHAR(50),
    title VARCHAR(500) NOT NULL,
    proposal_date DATE,
    proposer_kind VARCHAR(50),
    
    -- 진행 정보 (API 제공)
    proc_stage_cd VARCHAR(50),
    pass_gubn VARCHAR(50),
    proc_date DATE,
    general_result VARCHAR(500),
    
    -- 원문 데이터 (API 제공)
    summary_raw TEXT,
    
    -- AI 처리 결과 (자체 생성)
    summary TEXT,
    categories JSONB,  -- JSONB: 더 빠르고 인덱싱 가능
    vote_for JSONB,    -- JSONB: 더 빠르고 인덱싱 가능
    vote_against JSONB,  -- JSONB: 더 빠르고 인덱싱 가능
    
    -- 메타 정보
    proc_stage_order INTEGER,
    proposer_count INTEGER DEFAULT 1,
    link_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- bills 테이블 코멘트
COMMENT ON TABLE bills IS '의안 정보';
COMMENT ON COLUMN bills.bill_id IS '의안ID (billId)';
COMMENT ON COLUMN bills.bill_no IS '의안번호 (billNo)';
COMMENT ON COLUMN bills.title IS '의안명 (billName)';
COMMENT ON COLUMN bills.proposal_date IS '제안일 (proposeDt)';
COMMENT ON COLUMN bills.proposer_kind IS '제안자구분 (proposerKind: 의원/정부)';
COMMENT ON COLUMN bills.proc_stage_cd IS '진행단계 코드 (procStageCd: 접수/심사/본회의)';
COMMENT ON COLUMN bills.pass_gubn IS '처리구분 (passGubn: 계류의안/처리완료)';
COMMENT ON COLUMN bills.proc_date IS '처리일 (procDt)';
COMMENT ON COLUMN bills.general_result IS '일반 결과 (generalResult)';
COMMENT ON COLUMN bills.summary_raw IS '제안이유 및 주요내용 원문 (summary)';
COMMENT ON COLUMN bills.summary IS 'AI 요약 결과 (Gemini)';
COMMENT ON COLUMN bills.categories IS '카테고리 분류 결과 (최대 2개)';
COMMENT ON COLUMN bills.vote_for IS '찬성 시 정치성향 가중치 (예: {"P": 1, "U": 1})';
COMMENT ON COLUMN bills.vote_against IS '반대 시 정치성향 가중치 (예: {"M": 1, "T": 1})';
COMMENT ON COLUMN bills.proc_stage_order IS '진행 단계 순서 (1=접수, 2=심사, 3=본회의, 4=처리완료)';
COMMENT ON COLUMN bills.proposer_count IS '제안자 수 (대표 발의자 외 추가 인원)';
COMMENT ON COLUMN bills.link_url IS '상세 링크 URL (의안 상세 페이지)';

-- bills 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_bill_no ON bills(bill_no);
CREATE INDEX IF NOT EXISTS idx_proposal_date ON bills(proposal_date);
CREATE INDEX IF NOT EXISTS idx_proc_stage_cd ON bills(proc_stage_cd);
CREATE INDEX IF NOT EXISTS idx_pass_gubn ON bills(pass_gubn);
CREATE INDEX IF NOT EXISTS idx_proc_stage_order ON bills(proc_stage_order);
CREATE INDEX IF NOT EXISTS idx_created_at ON bills(created_at);
-- JSONB 인덱스 (GIN 인덱스)
CREATE INDEX IF NOT EXISTS idx_categories_gin ON bills USING GIN (categories);
CREATE INDEX IF NOT EXISTS idx_vote_for_gin ON bills USING GIN (vote_for);
CREATE INDEX IF NOT EXISTS idx_vote_against_gin ON bills USING GIN (vote_against);

-- updated_at 자동 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- bills 테이블 updated_at 트리거
CREATE TRIGGER update_bills_updated_at BEFORE UPDATE ON bills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 1.2 assembly_members (국회의원 정보)
CREATE TABLE IF NOT EXISTS assembly_members (
    -- 기본 정보 (PK)
    member_id VARCHAR(50) PRIMARY KEY,
    
    -- 이름 정보 (API 제공)
    name VARCHAR(100) NOT NULL,
    name_chinese VARCHAR(100),
    name_english VARCHAR(200),
    
    -- 정당 및 선거 정보 (API 제공)
    party VARCHAR(100),
    district VARCHAR(200),
    district_type VARCHAR(100),
    
    -- 위원회 정보 (API 제공)
    committee VARCHAR(500),
    current_committee VARCHAR(200),
    
    -- 경력 정보 (API 제공)
    era VARCHAR(200),
    election_type VARCHAR(50),
    
    -- 개인 정보 (API 제공)
    gender VARCHAR(10),
    birth_date DATE,
    birth_type VARCHAR(10),
    duty_name VARCHAR(100),
    
    -- 연락처 정보 (API 제공, 대부분 NULL)
    phone VARCHAR(50),
    email VARCHAR(200),
    homepage_url VARCHAR(500),
    office_room VARCHAR(100),
    
    -- 보좌진 정보 (API 제공, 대부분 NULL)
    aide_name VARCHAR(500),
    secretary_name VARCHAR(500),
    assistant_name VARCHAR(500),
    
    -- 기타 정보 (API 제공)
    photo_url VARCHAR(500),
    brief_history TEXT,
    
    -- 매핑용 필드 (표결정보 API와 연결)
    mona_cd VARCHAR(50),
    member_no VARCHAR(50),
    
    -- 메타 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- assembly_members 테이블 코멘트
COMMENT ON TABLE assembly_members IS '국회의원 정보';
COMMENT ON COLUMN assembly_members.member_id IS '의원코드 (NAAS_CD)';
COMMENT ON COLUMN assembly_members.name IS '의원명 (NAAS_NM)';
COMMENT ON COLUMN assembly_members.name_chinese IS '한자명 (NAAS_CH_NM)';
COMMENT ON COLUMN assembly_members.name_english IS '영문명 (NAAS_EN_NM, 35% NULL)';
COMMENT ON COLUMN assembly_members.party IS '정당명 (PLPT_NM)';
COMMENT ON COLUMN assembly_members.district IS '선거구 (ELECD_NM, 12% NULL)';
COMMENT ON COLUMN assembly_members.district_type IS '선거구 구분명 (ELECD_DIV_NM)';
COMMENT ON COLUMN assembly_members.committee IS '소속위원회명 (BLNG_CMIT_NM, 9% NULL)';
COMMENT ON COLUMN assembly_members.current_committee IS '현재 위원회명 (CMIT_NM, 91% NULL)';
COMMENT ON COLUMN assembly_members.era IS '당선 대수 (GTELT_ERACO: 제22대, 제20대 등)';
COMMENT ON COLUMN assembly_members.election_type IS '선거 구분명 (RLCT_DIV_NM: 초선/재선/3선)';
COMMENT ON COLUMN assembly_members.gender IS '성별 (NTR_DIV: 남/여)';
COMMENT ON COLUMN assembly_members.birth_date IS '생년월일 (BIRDY_DT)';
COMMENT ON COLUMN assembly_members.birth_type IS '생년 구분 코드 (BIRDY_DIV_CD: 음/양)';
COMMENT ON COLUMN assembly_members.duty_name IS '직책명 (DTY_NM, 76% NULL)';
COMMENT ON COLUMN assembly_members.mona_cd IS '표결정보 API의 MONA_CD (매핑용)';
COMMENT ON COLUMN assembly_members.member_no IS '표결정보 API의 MEMBER_NO (매핑용)';

-- assembly_members 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_name ON assembly_members(name);
CREATE INDEX IF NOT EXISTS idx_party ON assembly_members(party);
CREATE INDEX IF NOT EXISTS idx_district ON assembly_members(district);
CREATE INDEX IF NOT EXISTS idx_mona_cd ON assembly_members(mona_cd);
CREATE INDEX IF NOT EXISTS idx_member_no ON assembly_members(member_no);
CREATE INDEX IF NOT EXISTS idx_era ON assembly_members(era);

-- assembly_members 테이블 updated_at 트리거
CREATE TRIGGER update_assembly_members_updated_at BEFORE UPDATE ON assembly_members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 1.3 votes (국회의원 표결 정보)
CREATE TABLE IF NOT EXISTS votes (
    -- 기본 정보 (PK)
    vote_id BIGSERIAL PRIMARY KEY,  -- BIGSERIAL: 자동 증가
    
    -- 의안 정보 (FK)
    bill_id VARCHAR(50) NOT NULL,
    bill_no VARCHAR(50),
    bill_name VARCHAR(500),
    
    -- 의원 정보 (FK)
    member_no VARCHAR(50),
    mona_cd VARCHAR(50),
    member_id VARCHAR(50),
    member_name VARCHAR(100),
    member_name_chinese VARCHAR(100),
    
    -- 정당 및 선거구 정보 (API 제공)
    party_name VARCHAR(100),
    party_code VARCHAR(50),
    district_name VARCHAR(200),
    district_code VARCHAR(50),
    
    -- 표결 정보 (API 제공)
    vote_result VARCHAR(50),
    vote_date TIMESTAMP,  -- DATETIME → TIMESTAMP
    
    -- 기타 정보 (API 제공)
    era INTEGER,
    session_code VARCHAR(50),
    current_committee VARCHAR(200),
    current_committee_id VARCHAR(50),
    currents_code VARCHAR(50),
    dept_code VARCHAR(50),
    display_order INTEGER,
    law_title VARCHAR(500),
    bill_url VARCHAR(500),
    bill_name_url VARCHAR(500),
    
    -- 메타 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키 및 제약조건
    CONSTRAINT fk_votes_bill_id FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE,
    CONSTRAINT fk_votes_member_id FOREIGN KEY (member_id) REFERENCES assembly_members(member_id) ON DELETE SET NULL,
    CONSTRAINT unique_bill_member_vote UNIQUE (bill_id, member_no, vote_date)
);

-- votes 테이블 코멘트
COMMENT ON TABLE votes IS '국회의원 본회의 표결 정보';
COMMENT ON COLUMN votes.bill_id IS '의안ID (BILL_ID, FK → bills.bill_id)';
COMMENT ON COLUMN votes.member_id IS '의원코드 (FK → assembly_members.member_id, 매핑 후 설정)';
COMMENT ON COLUMN votes.vote_result IS '표결결과 (RESULT_VOTE_MOD: 찬성/반대/기권/불참)';

-- votes 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_bill_id ON votes(bill_id);
CREATE INDEX IF NOT EXISTS idx_member_id ON votes(member_id);
CREATE INDEX IF NOT EXISTS idx_member_no ON votes(member_no);
CREATE INDEX IF NOT EXISTS idx_mona_cd ON votes(mona_cd);
CREATE INDEX IF NOT EXISTS idx_vote_result ON votes(vote_result);
CREATE INDEX IF NOT EXISTS idx_vote_date ON votes(vote_date);
CREATE INDEX IF NOT EXISTS idx_party_name ON votes(party_name);

-- ============================================
-- 2. 사용자 관련 테이블
-- ============================================

-- 2.1 user_votes (사용자 투표)
-- ENUM 타입 생성
CREATE TYPE vote_result_type AS ENUM ('찬성', '반대');

CREATE TABLE IF NOT EXISTS user_votes (
    -- 기본 정보 (PK)
    user_vote_id BIGSERIAL PRIMARY KEY,
    
    -- 의안 정보 (FK)
    bill_id VARCHAR(50) NOT NULL,
    
    -- 사용자 정보
    user_id VARCHAR(100) NOT NULL,
    
    -- 투표 정보
    vote_result vote_result_type NOT NULL,  -- ENUM 타입 사용
    
    -- 메타 정보
    vote_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키 및 제약조건
    CONSTRAINT fk_user_votes_bill_id FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE,
    CONSTRAINT unique_user_bill UNIQUE (user_id, bill_id)
);

-- user_votes 테이블 코멘트
COMMENT ON TABLE user_votes IS '사용자 투표 정보';
COMMENT ON COLUMN user_votes.bill_id IS '의안ID (FK → bills.bill_id)';
COMMENT ON COLUMN user_votes.user_id IS '사용자 식별자 (세션ID 또는 사용자ID)';
COMMENT ON COLUMN user_votes.vote_result IS '투표 결과 (응원해요=찬성, 아쉬워요=반대)';

-- user_votes 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_bill_id ON user_votes(bill_id);
CREATE INDEX IF NOT EXISTS idx_user_id ON user_votes(user_id);
CREATE INDEX IF NOT EXISTS idx_vote_result ON user_votes(vote_result);
CREATE INDEX IF NOT EXISTS idx_vote_date ON user_votes(vote_date);

-- 2.2 user_political_profile (사용자 정치성향 프로필)
CREATE TABLE IF NOT EXISTS user_political_profile (
    -- 기본 정보 (PK)
    user_id VARCHAR(100) PRIMARY KEY,
    
    -- 정치성향 점수 (8개 축, 4쌍)
    p_score INTEGER DEFAULT 0,
    m_score INTEGER DEFAULT 0,
    u_score INTEGER DEFAULT 0,
    t_score INTEGER DEFAULT 0,
    n_score INTEGER DEFAULT 0,
    s_score INTEGER DEFAULT 0,
    o_score INTEGER DEFAULT 0,
    r_score INTEGER DEFAULT 0,
    
    -- 메타 정보
    test_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- user_political_profile 테이블 코멘트
COMMENT ON TABLE user_political_profile IS '사용자 정치성향 프로필';
COMMENT ON COLUMN user_political_profile.p_score IS '공공 중심 (P) 점수 (초기 0~5)';
COMMENT ON COLUMN user_political_profile.m_score IS '시장 중심 (M) 점수 (초기 0~5)';
COMMENT ON COLUMN user_political_profile.u_score IS '보편 적용 (U) 점수 (초기 0~5)';
COMMENT ON COLUMN user_political_profile.t_score IS '대상 맞춤 (T) 점수 (초기 0~5)';
COMMENT ON COLUMN user_political_profile.n_score IS '필요 기반 (N) 점수 (초기 0~5)';
COMMENT ON COLUMN user_political_profile.s_score IS '성과 기반 (S) 점수 (초기 0~5)';
COMMENT ON COLUMN user_political_profile.o_score IS '개방 실험 (O) 점수 (초기 0~5)';
COMMENT ON COLUMN user_political_profile.r_score IS '절차 안정 (R) 점수 (초기 0~5)';

-- user_political_profile 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_test_completed ON user_political_profile(test_completed);

-- user_political_profile 테이블 updated_at 트리거
CREATE TRIGGER update_user_political_profile_updated_at BEFORE UPDATE ON user_political_profile
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 2.3 member_political_profile (의원 정치성향 프로필)
CREATE TABLE IF NOT EXISTS member_political_profile (
    -- 기본 정보 (PK)
    member_id VARCHAR(50) PRIMARY KEY,
    
    -- 정치성향 점수 (8개 축, 표결 이력 기반 계산)
    p_score INTEGER DEFAULT 0,
    m_score INTEGER DEFAULT 0,
    u_score INTEGER DEFAULT 0,
    t_score INTEGER DEFAULT 0,
    n_score INTEGER DEFAULT 0,
    s_score INTEGER DEFAULT 0,
    o_score INTEGER DEFAULT 0,
    r_score INTEGER DEFAULT 0,
    
    -- 통계 정보
    total_votes INTEGER DEFAULT 0,
    last_calculated_at TIMESTAMP,
    
    -- 메타 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키
    CONSTRAINT fk_member_political_profile_member_id FOREIGN KEY (member_id) REFERENCES assembly_members(member_id) ON DELETE CASCADE
);

-- member_political_profile 테이블 코멘트
COMMENT ON TABLE member_political_profile IS '의원 정치성향 프로필 (표결 이력 기반)';

-- member_political_profile 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_total_votes ON member_political_profile(total_votes);

-- member_political_profile 테이블 updated_at 트리거
CREATE TRIGGER update_member_political_profile_updated_at BEFORE UPDATE ON member_political_profile
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 3. 매핑 및 설정 테이블
-- ============================================

-- 3.1 proc_stage_mapping (진행 단계 매핑)
CREATE TABLE IF NOT EXISTS proc_stage_mapping (
    -- 기본 정보 (PK)
    stage_code VARCHAR(50) PRIMARY KEY,
    stage_name VARCHAR(50) NOT NULL,
    stage_order INTEGER NOT NULL,
    description TEXT
);

-- proc_stage_mapping 테이블 코멘트
COMMENT ON TABLE proc_stage_mapping IS '진행 단계 매핑';
COMMENT ON COLUMN proc_stage_mapping.stage_code IS '진행 단계 코드';
COMMENT ON COLUMN proc_stage_mapping.stage_name IS '진행 단계 이름';
COMMENT ON COLUMN proc_stage_mapping.stage_order IS '진행 단계 순서 (1, 2, 3...)';

-- proc_stage_mapping 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_stage_order ON proc_stage_mapping(stage_order);

-- 초기 데이터 (ON CONFLICT 사용)
INSERT INTO proc_stage_mapping (stage_code, stage_name, stage_order, description) VALUES
('접수', '접수', 1, '의안이 접수된 단계'),
('심사', '심사', 2, '위원회 심사 단계'),
('본회의', '본회의', 3, '본회의 심의 단계'),
('처리완료', '처리완료', 4, '처리가 완료된 단계'),
('계류의안', '계류의안', 0, '계류 중인 의안')
ON CONFLICT (stage_code) DO UPDATE SET stage_name = EXCLUDED.stage_name;

-- 3.2 member_id_mapping (의원 식별자 매핑)
CREATE TABLE IF NOT EXISTS member_id_mapping (
    -- 기본 정보 (PK)
    mapping_id BIGSERIAL PRIMARY KEY,
    
    -- 의원 식별자
    naas_cd VARCHAR(50) NOT NULL,
    member_no VARCHAR(50),
    mona_cd VARCHAR(50),
    
    -- 검증 정보
    member_name VARCHAR(100),
    is_verified BOOLEAN DEFAULT FALSE,
    
    -- 메타 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 제약조건
    CONSTRAINT unique_naas_cd UNIQUE (naas_cd)
);

-- member_id_mapping 테이블 코멘트
COMMENT ON TABLE member_id_mapping IS '의원 식별자 매핑';
COMMENT ON COLUMN member_id_mapping.naas_cd IS '의원정보 API의 NAAS_CD';
COMMENT ON COLUMN member_id_mapping.member_no IS '표결정보 API의 MEMBER_NO';
COMMENT ON COLUMN member_id_mapping.mona_cd IS '표결정보 API의 MONA_CD';

-- member_id_mapping 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_member_no ON member_id_mapping(member_no);
CREATE INDEX IF NOT EXISTS idx_mona_cd ON member_id_mapping(mona_cd);
CREATE INDEX IF NOT EXISTS idx_member_name ON member_id_mapping(member_name);
CREATE INDEX IF NOT EXISTS idx_is_verified ON member_id_mapping(is_verified);

-- member_id_mapping 테이블 updated_at 트리거
CREATE TRIGGER update_member_id_mapping_updated_at BEFORE UPDATE ON member_id_mapping
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 3.3 bill_similarity (의안 유사도)
CREATE TABLE IF NOT EXISTS bill_similarity (
    -- 기본 정보 (PK)
    bill_id_1 VARCHAR(50) NOT NULL,
    bill_id_2 VARCHAR(50) NOT NULL,
    
    -- 유사도 정보
    similarity_score REAL NOT NULL,  -- FLOAT → REAL
    similarity_method VARCHAR(50),
    
    -- 메타 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키 및 제약조건
    CONSTRAINT pk_bill_similarity PRIMARY KEY (bill_id_1, bill_id_2),
    CONSTRAINT fk_bill_similarity_bill_id_1 FOREIGN KEY (bill_id_1) REFERENCES bills(bill_id) ON DELETE CASCADE,
    CONSTRAINT fk_bill_similarity_bill_id_2 FOREIGN KEY (bill_id_2) REFERENCES bills(bill_id) ON DELETE CASCADE
);

-- bill_similarity 테이블 코멘트
COMMENT ON TABLE bill_similarity IS '의안 유사도';
COMMENT ON COLUMN bill_similarity.bill_id_1 IS '의안ID 1';
COMMENT ON COLUMN bill_similarity.bill_id_2 IS '의안ID 2';
COMMENT ON COLUMN bill_similarity.similarity_score IS '유사도 점수 (0.0 ~ 1.0)';
COMMENT ON COLUMN bill_similarity.similarity_method IS '유사도 계산 방법 (category/embedding/keyword)';

-- bill_similarity 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_similarity_score ON bill_similarity(similarity_score DESC);
CREATE INDEX IF NOT EXISTS idx_bill_id_1 ON bill_similarity(bill_id_1);
CREATE INDEX IF NOT EXISTS idx_bill_id_2 ON bill_similarity(bill_id_2);
CREATE INDEX IF NOT EXISTS idx_similarity_method ON bill_similarity(similarity_method);

-- ============================================
-- 완료 메시지
-- ============================================
SELECT 'Database schema created successfully!' AS message;
