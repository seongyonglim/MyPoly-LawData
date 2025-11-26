# 구현 체크리스트 - 의안 상세 화면

## ✅ 즉시 구현 가능한 기능

### 1. 의안 기본 정보 표시
- [x] API 데이터 확인 완료
- [ ] DB 테이블 생성 (`bills`)
- [ ] 데이터 수집 스크립트 구현
- [ ] API 엔드포인트 구현
- [ ] 프론트엔드 연동

**필요 데이터**:
- 제목: `bills.title`
- 날짜: `bills.proposal_date`
- 카테고리: `bills.categories`
- 제안자: `bills.proposer_name`

### 2. AI 요약 표시
- [x] AI 요약 코드 이미 구현됨
- [ ] DB에 저장 로직 구현
- [ ] API 엔드포인트 구현
- [ ] 프론트엔드 연동

**필요 데이터**:
- 요약: `bills.summary`

### 3. 심사 진행 단계
- [x] API 데이터 확인 완료
- [ ] `proc_stage_mapping` 테이블 생성
- [ ] 단계 매핑 데이터 입력
- [ ] API 엔드포인트 구현
- [ ] 프론트엔드 연동

**필요 데이터**:
- 단계 코드: `bills.proc_stage_cd`
- 단계 순서: `proc_stage_mapping.stage_order`

### 4. 사용자 투표 기능
- [x] DB 설계 완료
- [ ] `user_votes` 테이블 생성
- [ ] 투표 API 구현 (POST)
- [ ] 투표 통계 API 구현 (GET)
- [ ] 프론트엔드 연동

**필요 데이터**:
- 사용자 투표: `user_votes` 테이블
- 투표 통계: 집계 쿼리

### 5. 유사 의안 추천 (기본)
- [x] 카테고리 데이터 확인 완료
- [ ] 카테고리 기반 유사도 계산 로직
- [ ] API 엔드포인트 구현
- [ ] 프론트엔드 연동

**필요 데이터**:
- 의안 목록: `bills` 테이블
- 카테고리: `bills.categories`

---

## ⚠️ 부분 구현 가능한 기능

### 6. 제안자 정보 (전체 발의자 수)
- [x] 대표 발의자 정보 확인 완료
- [ ] 전체 발의자 수 파싱 로직 (의안 상세 페이지 크롤링)
- [ ] DB 필드 추가 (`bills.proposer_count`)
- [ ] API 엔드포인트 구현

**현재 상태**: 대표 발의자만 표시 가능

### 7. 나와 유사한 성향의 국회의원
- [x] 의원 정보 API 확인 완료
- [ ] 의원 사진 URL 매핑
- [ ] 사용자 정치성향 테스트 구현 (추후)
- [ ] 일치율 계산 알고리즘 구현 (추후)
- [ ] API 엔드포인트 구현

**현재 상태**: 의원 정보 표시만 가능, 일치율 계산은 추후 구현

---

## ❌ 추후 구현 필요

### 8. 사용자 정치성향 테스트
- [ ] 정치성향 테스트 설문 구현
- [ ] `user_political_profile` 테이블 생성
- [ ] 점수 계산 로직
- [ ] API 엔드포인트 구현

### 9. AI 임베딩 기반 유사 의안 추천
- [ ] AI 임베딩 벡터 생성
- [ ] 벡터 유사도 계산
- [ ] `bill_similarity` 테이블 생성
- [ ] 배치 작업 구현

---

## 데이터 수집 우선순위

### Phase 1: 기본 데이터 수집 (즉시 시작 가능)
1. 의안 정보 수집 (`bills` 테이블)
2. AI 요약 및 카테고리 분류
3. 진행 단계 매핑 데이터 입력

### Phase 2: 표결 데이터 수집
1. 국회의원 정보 수집 (`assembly_members` 테이블)
2. 표결 정보 수집 (`votes` 테이블)
3. 의원 식별자 매핑 (`MONA_CD` ↔ `NAAS_CD`)

### Phase 3: 사용자 데이터
1. 사용자 투표 기능 구현
2. 투표 통계 집계

---

## API 엔드포인트 설계 (예시)

### 의안 상세 조회
```
GET /api/bills/{bill_id}
Response: {
  bill_id, title, proposal_date, categories,
  proposer_name, proc_stage_cd, proc_stage_order,
  summary, link_url, ...
}
```

### 사용자 투표
```
POST /api/bills/{bill_id}/vote
Body: { user_id, vote_result: '찬성' | '반대' }
```

### 투표 통계
```
GET /api/bills/{bill_id}/vote-stats
Response: {
  support_count, oppose_count, total_count,
  support_rate, oppose_rate
}
```

### 유사 의안 추천
```
GET /api/bills/{bill_id}/similar
Query: ?method=category&limit=3
Response: [
  { bill_id, title, summary, categories, ... }
]
```

### 유사 성향 의원 (추후)
```
GET /api/users/{user_id}/similar-members
Response: [
  { member_id, name, party, photo_url, match_rate, ... }
]
```

---

## 참고 문서
- `docs/figma-screen-analysis.md` - 화면별 상세 분석
- `docs/api-crawling-results.md` - API 제공 데이터
- `docs/db-design.md` - DB 설계 상세

