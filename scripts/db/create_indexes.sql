-- 성능 최적화를 위한 인덱스 생성
-- 자주 사용되는 쿼리의 WHERE 절과 JOIN 조건에 인덱스 추가

-- bills 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_bills_proposal_date ON bills(proposal_date);
CREATE INDEX IF NOT EXISTS idx_bills_pass_gubn ON bills(pass_gubn);
CREATE INDEX IF NOT EXISTS idx_bills_proc_stage_cd ON bills(proc_stage_cd);
-- 한국어 전문 검색 인덱스는 PostgreSQL 확장이 필요하므로 제외
-- 필요시: CREATE EXTENSION IF NOT EXISTS pg_trgm; 후 trigram 인덱스 사용
-- CREATE INDEX IF NOT EXISTS idx_bills_title_trgm ON bills USING gin(title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_bills_title ON bills(title);  -- 일반 인덱스로 대체
CREATE INDEX IF NOT EXISTS idx_bills_proposal_date_pass_gubn ON bills(proposal_date, pass_gubn);

-- votes 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_votes_bill_id ON votes(bill_id);
CREATE INDEX IF NOT EXISTS idx_votes_member_id ON votes(member_id);
CREATE INDEX IF NOT EXISTS idx_votes_vote_result ON votes(vote_result);
CREATE INDEX IF NOT EXISTS idx_votes_vote_date ON votes(vote_date);
CREATE INDEX IF NOT EXISTS idx_votes_bill_id_vote_result ON votes(bill_id, vote_result);

-- assembly_members 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_assembly_members_member_id ON assembly_members(member_id);
CREATE INDEX IF NOT EXISTS idx_assembly_members_party ON assembly_members(party);
CREATE INDEX IF NOT EXISTS idx_assembly_members_name ON assembly_members(name);

-- 통계 쿼리 최적화를 위한 복합 인덱스
CREATE INDEX IF NOT EXISTS idx_bills_date_pass_votes ON bills(proposal_date, pass_gubn) 
    WHERE proposal_date >= '2025-01-01';

-- 설명
COMMENT ON INDEX idx_bills_proposal_date IS '의안 제안일 기준 필터링 및 정렬 최적화';
COMMENT ON INDEX idx_bills_pass_gubn IS '처리구분 필터링 최적화';
COMMENT ON INDEX idx_bills_proc_stage_cd IS '진행단계 필터링 최적화';
COMMENT ON INDEX idx_votes_bill_id IS '의안별 표결 결과 조회 최적화';
COMMENT ON INDEX idx_votes_member_id IS '의원별 표결 기록 조회 최적화';

