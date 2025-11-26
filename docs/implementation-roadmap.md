# 구현 로드맵

> 데이터 수집 및 DB 구축 단계별 가이드

## 현재 상태

### ✅ 완료된 작업
- [x] API 검토 및 테스트 (3개 API 모두 확인)
- [x] 대량 데이터 분석 (1,000건 의안, 300건 의원, 298건 표결)
- [x] DB 설계 완료 (`docs/db-design-final.md`)
- [x] AI 코드 분석 완료 (`docs/ai-code-analysis.md`)
- [x] 필드 매핑 확인 완료

### ⏳ 다음 단계

---

## 추천 진행 순서

### Phase 1: DB 스키마 생성 및 검증 (1-2일)

**목적**: 테이블 구조를 먼저 만들고, 소량 데이터로 매핑 검증

**작업**:
1. **DB 선택 및 설정**
   - MySQL / PostgreSQL / SQLite 중 선택
   - DB 서버 설정 또는 로컬 DB 생성

2. **스키마 생성**
   - `docs/db-design-final.md`의 SQL 스크립트 실행
   - 테이블 생성 확인

3. **소량 데이터 매핑 테스트**
   - API에서 10건 정도만 가져오기
   - 필드 매핑 로직 작성 및 테스트
   - 데이터 삽입 확인

**왜 먼저?**
- DB 구조를 먼저 확정하면 데이터 매핑 로직을 명확히 할 수 있음
- 소량 데이터로 문제를 빠르게 발견 가능
- 전체 데이터 수집 전에 매핑 로직 검증

---

### Phase 2: 데이터 수집 스크립트 개발 (2-3일)

**목적**: API에서 데이터를 가져와서 DB에 저장하는 파이프라인 구축

**작업**:
1. **의안정보 수집 스크립트**
   - `AI/crawl/crawl_yesterday_law.py` 기반
   - CSV 대신 DB에 직접 INSERT
   - UPSERT 로직 (중복 처리)

2. **의원정보 수집 스크립트**
   - 국회의원 정보 통합 API 호출
   - DB에 INSERT

3. **표결정보 수집 스크립트**
   - 국회의원 본회의 표결정보 API 호출
   - 의안ID 매핑 후 INSERT

4. **에러 처리 및 로깅**
   - 실패한 데이터 재시도 로직
   - 로그 기록

---

### Phase 3: AI 처리 통합 (1-2일)

**목적**: 크롤링한 의안에 AI 요약/분류 적용

**작업**:
1. **AI 처리 스크립트 수정**
   - DB에서 의안 읽기
   - Gemini API 호출
   - DB에 결과 업데이트

2. **일일 배치 파이프라인**
   - 크롤링 → AI 처리 → DB 저장

---

### Phase 4: 전체 데이터 수집 (1-2일)

**목적**: 과거 데이터 전체 수집

**작업**:
1. **초기 전체 수집**
   - 22대 국회 의안 전체 수집
   - 의원 정보 전체 수집
   - 표결 정보 수집 (의안별)

2. **데이터 검증**
   - 중복 확인
   - NULL 값 확인
   - 관계 무결성 확인

---

## 추천 시작 방법

### 🎯 **Phase 1부터 시작하는 것을 추천합니다**

**이유**:
1. **빠른 피드백**: 소량 데이터로 매핑 문제를 빠르게 발견
2. **명확한 목표**: DB 구조가 확정되면 데이터 수집 로직이 명확해짐
3. **리스크 감소**: 전체 데이터 수집 전에 구조 검증

---

## Phase 1 상세 가이드

### 1단계: DB 선택 및 설정

**옵션**:
- **SQLite** (가장 간단): 파일 기반, 별도 서버 불필요
- **MySQL** (일반적): 서버 필요, 프로덕션에 적합
- **PostgreSQL** (고급): 서버 필요, 복잡한 쿼리에 적합

**추천**: 개발 초기에는 **SQLite**로 시작, 나중에 MySQL/PostgreSQL로 마이그레이션

### 2단계: 스키마 생성

**작업**:
1. `docs/db-design-final.md`의 SQL 스크립트를 DB에 맞게 수정
2. 테이블 생성 순서:
   - `bills` (의안)
   - `assembly_members` (의원)
   - `votes` (표결)
   - `user_votes` (사용자 투표)
   - `user_political_profile` (사용자 정치성향)

### 3단계: 소량 데이터 매핑 테스트

**작업**:
1. API에서 10건만 가져오기
2. 필드 매핑 로직 작성:
   ```python
   # 예시
   bill_data = {
       "billId": "PRC_...",
       "billName": "의안명",
       "billNo": "2211945",
       # ...
   }
   
   db_record = {
       "bill_id": bill_data["billId"],
       "title": bill_data["billName"],
       "bill_no": bill_data["billNo"],
       # ...
   }
   ```
3. INSERT 테스트
4. SELECT로 데이터 확인

---

## 다음 단계 결정

### 옵션 A: DB 스키마부터 (추천 ⭐)
- ✅ 빠른 검증
- ✅ 명확한 목표
- ✅ 리스크 감소

### 옵션 B: 데이터 수집부터
- ⚠️ 매핑 문제를 나중에 발견할 수 있음
- ⚠️ 수집한 데이터를 다시 처리해야 할 수 있음

---

## 필요한 도구

### Python 패키지
```txt
requests          # API 호출
mysql-connector-python  # MySQL 연결 (또는 pymysql)
psycopg2          # PostgreSQL 연결
sqlite3           # SQLite (내장)
python-dotenv     # 환경변수 관리
```

### 스크립트 구조
```
scripts/
├── db/
│   ├── init_db.py          # DB 초기화 (스키마 생성)
│   └── connection.py       # DB 연결 유틸
├── collect/
│   ├── collect_bills.py    # 의안 수집
│   ├── collect_members.py # 의원 수집
│   └── collect_votes.py   # 표결 수집
└── test/
    └── test_mapping.py    # 매핑 테스트
```

---

## 질문

1. **어떤 DB를 사용하시나요?** (SQLite/MySQL/PostgreSQL)
2. **로컬 개발 환경이 준비되어 있나요?**
3. **Phase 1부터 시작할까요, 아니면 다른 순서를 원하시나요?**



