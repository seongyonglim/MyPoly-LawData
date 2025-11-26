# AI 디렉토리 코드 분석

> 의안 크롤링 및 AI 처리 코드 분석 문서

## 개요

AI 디렉토리에는 의안 데이터를 크롤링하고, AI를 통해 요약/카테고리 분류/정치성향 가중치를 생성하는 코드가 있습니다.

---

## 디렉토리 구조

```
AI/
├── crawl/                          # 의안 크롤링 스크립트
│   ├── crawl_yesterday_law.py     # 전날 의안 크롤링 (일일 배치용)
│   ├── crawl_recent_n_law.py      # 최근 N건 의안 크롤링
│   └── bills_YYYYMMDD.csv          # 크롤링 결과 CSV 파일들
│
├── 20251008_Gemini/                # 최신 Gemini 버전 (현재 사용 중)
│   ├── bill_headline_summarizer.py # AI 요약/분류 스크립트
│   ├── bills_YYYYMMDD.csv          # 입력 CSV
│   ├── outputs_<model>_YYYYMMDD.csv # 출력 CSV (요약 결과)
│   └── results_<model>_YYYYMMDD.json # 처리 통계 JSON
│
└── [이전 버전들]                    # 20250911, 20250919, 20251007 등
```

---

## 1. 의안 크롤링 코드

### 1.1 `crawl_yesterday_law.py` (일일 배치용)

**목적**: 전날(KST 자정 기준) 발의된 의안만 수집

**주요 기능**:
- 22대 국회 의안만 수집 (`start_ord=22`, `end_ord=22`)
- 전날 날짜 기준 필터링 (`start_propose_date`, `end_propose_date`)
- CSV 파일로 저장 (`bills_YYYYMMDD.csv`)

**출력 CSV 구조**:
```csv
date,billNo,billId,title,body,link
2025-09-18,2214458,PRC_...,"의안명","제안이유 및 주요내용",https://...
```

**주요 필드**:
- `date`: 제안일
- `billNo`: 의안번호
- `billId`: 의안ID
- `title`: 의안명
- `body`: 제안이유 및 주요내용 (요약)
- `link`: 상세 링크 URL

**특징**:
- TLS 1.2 고정 (HTTPS 보안)
- 재시도 로직 포함
- 페이지네이션 처리 (최대 10페이지)
- 중복 제거 (billId 기준)

---

### 1.2 `crawl_recent_n_law.py` (최근 N건)

**목적**: 최근 N건의 의안 수집

**주요 기능**:
- 최근 200건 또는 500건, 2000건 수집
- 날짜 필터 없이 최신순으로 수집
- CSV 파일로 저장

---

## 2. AI 요약 및 분류 코드

### 2.1 `bill_headline_summarizer.py` (Gemini 버전)

**목적**: 의안 제목과 본문을 받아서 다음을 생성:
1. **headline**: 뉴스형 헤드라인 (20~36자)
2. **summary**: 쉬운말 요약 (2~3문장, 180자 이내)
3. **categories**: 카테고리 분류 (16개 중 1~2개)
4. **vote**: 정치성향 가중치 (찬성/반대 시 영향)

**입력**: CSV 파일 (`bills_YYYYMMDD.csv`)
- `title`: 의안 제목
- `body`: 제안이유 및 주요내용

**출력**: CSV 파일 (`outputs_<model>_YYYYMMDD.csv`)
- `headline`: 뉴스형 헤드라인
- `summary`: 쉬운말 요약
- `categories`: JSON 배열 (예: `["일자리", "복지"]`)
- `vote_for`: JSON 객체 (예: `{"P":1, "U":1}`)
- `vote_against`: JSON 객체 (예: `{"M":1, "T":1}`)

---

## 3. 정치성향 가중치 시스템

### 3.1 정치성향 축 (8개, 4쌍)

| 축 | 설명 | 반대 축 |
|---|------|--------|
| **P** (공공 중심) | 공공 재정투입, 공공서비스 확대 | **M** (시장 중심) |
| **U** (보편 적용) | 보편적 급여, 요금 인하 | **T** (대상 맞춤) |
| **N** (필요 기반) | 취약계층 선별 지원 | **S** (성과 기반) |
| **O** (개방 실험) | 규제샌드박스, 신기술 실험 | **R** (절차 안정) |

### 3.2 가중치 부여 규칙

**기본 원칙**:
- 같은 축에서 양쪽을 동시에 넣지 않음 (P와 M 동시 선택 불가)
- 1~3개 축을 선택하여 +1 가중치 부여 (기본 2개 권장)
- 찬성("for"): 의안의 핵심 변화 방향과 부합하는 축
- 반대("against"): 거울 반대 축 또는 특정 가치 강화 축

**매핑 가이드 예시**:
- 공공 재정투입 확대/공공서비스 보편 공급 → **P, U**
- 민영화/규제완화/경쟁촉진 → **M, S**
- 취약계층 선별 지원/바우처 → **T, N**
- 규정 강화/심사 엄격화 → **R**
- 규제샌드박스/신기술 실험 → **O**

---

## 4. 카테고리 시스템

### 4.1 16개 카테고리

1. 일자리
2. 재정
3. 금융
4. 교육
5. 보건
6. 복지
7. 주거
8. 교통
9. 환경
10. 에너지
11. 디지털
12. 안전
13. 청년
14. 여성
15. 국방
16. 문화

### 4.2 카테고리 경계 규칙

- **디지털 vs 안전**: 개인정보·통신규제는 디지털, 범죄·피해자보호는 안전
- **복지 vs 교육/청년/여성**: 학생이면 교육, 19~34세면 청년, 여성 특정이면 여성, 그 외 보편적이면 복지
- **에너지 vs 환경**: 전력요금·원전은 에너지, 오염·보전은 환경
- 모호하면 핵심 영향 분야 1개 선택, 정말 애매할 때만 2개

---

## 5. 데이터 흐름

### 5.1 전체 프로세스

```
1. 크롤링 (crawl_yesterday_law.py)
   ↓
   bills_YYYYMMDD.csv 생성
   (date, billNo, billId, title, body, link)
   
2. AI 처리 (bill_headline_summarizer.py)
   ↓
   outputs_<model>_YYYYMMDD.csv 생성
   (headline, summary, categories, vote_for, vote_against)
   
3. DB 저장 (예정)
   ↓
   bills 테이블에 저장
   - summary: AI 요약
   - categories: JSON 배열
   - vote_for: JSON 객체
   - vote_against: JSON 객체
```

### 5.2 일일 배치 프로세스

```
매일 새벽 2시:
1. crawl_yesterday_law.py 실행
   → 전날 의안 크롤링
   → bills_YYYYMMDD.csv 저장

2. bill_headline_summarizer.py 실행
   → bills_YYYYMMDD.csv 읽기
   → Gemini API 호출 (의안별)
   → outputs_<model>_YYYYMMDD.csv 저장

3. DB 업데이트 (예정)
   → bills 테이블에 AI 처리 결과 저장
```

---

## 6. 코드 통합 전략

### 6.1 현재 코드 활용 방안

**크롤링 코드**:
- ✅ `crawl_yesterday_law.py`를 일일 배치에 활용
- ✅ CSV 대신 DB에 직접 저장하도록 수정 필요

**AI 처리 코드**:
- ✅ `bill_headline_summarizer.py`를 그대로 활용 가능
- ✅ CSV 입력 → DB 저장으로 변경 필요

### 6.2 수정 필요 사항

1. **크롤링 코드 수정**:
   - CSV 저장 대신 DB에 직접 INSERT
   - `bills` 테이블에 저장
   - 필드 매핑: `billId` → `bill_id`, `billName` → `title` 등

2. **AI 처리 코드 수정**:
   - CSV 입력 대신 DB에서 읽기
   - CSV 출력 대신 DB에 업데이트
   - `bills` 테이블의 `summary`, `categories`, `vote_for`, `vote_against` 필드 업데이트

3. **배치 스크립트 통합**:
   - 크롤링 → AI 처리 → DB 저장을 하나의 파이프라인으로 통합

---

## 7. DB 매핑

### 7.1 크롤링 데이터 → DB

| 크롤링 CSV 필드 | DB 필드 | 타입 |
|---------------|--------|------|
| `billId` | `bill_id` | VARCHAR(50) PK |
| `billNo` | `bill_no` | VARCHAR(50) |
| `title` | `title` | VARCHAR(500) |
| `body` | `summary_raw` | TEXT |
| `date` | `proposal_date` | DATE |
| `link` | `link_url` | VARCHAR(500) |

### 7.2 AI 처리 결과 → DB

| AI 출력 CSV 필드 | DB 필드 | 타입 |
|----------------|--------|------|
| `headline` | (별도 저장 안 함) | - |
| `summary` | `summary` | TEXT |
| `categories` | `categories` | JSON |
| `vote_for` | `vote_for` | JSON |
| `vote_against` | `vote_against` | JSON |

---

## 8. 사용 예시

### 8.1 크롤링 실행

```bash
cd AI/crawl
python crawl_yesterday_law.py
# → bills_20250918.csv 생성
```

### 8.2 AI 처리 실행

```bash
cd AI/20251008_Gemini
python bill_headline_summarizer.py \
    bills_20250918.csv \
    --model gemini-2.5-flash \
    --max-rows 50
# → outputs_gemini-2.5-flash_20250918.csv 생성
# → results_gemini-2.5-flash_20250918.json 생성
```

---

## 9. 주요 특징

### 9.1 크롤링 코드 특징

- ✅ TLS 1.2 보안 연결
- ✅ 재시도 로직 (최대 5회)
- ✅ 중복 제거
- ✅ 페이지네이션 처리
- ✅ 에러 핸들링

### 9.2 AI 처리 코드 특징

- ✅ Gemini API 사용 (JSON 응답 강제)
- ✅ System Instruction으로 프롬프트 고정
- ✅ 토큰 사용량 추적
- ✅ 에러 처리 및 재시도
- ✅ 출력 형식 검증 (헤드라인 길이, 금지어 등)

---

## 10. 다음 단계

1. **크롤링 코드 DB 연동**
   - CSV 저장 대신 DB INSERT
   - UPSERT 로직 추가

2. **AI 처리 코드 DB 연동**
   - DB에서 읽기 → AI 처리 → DB 업데이트

3. **배치 스크립트 통합**
   - 일일 배치 자동화

4. **에러 처리 강화**
   - 실패한 의안 재처리
   - 로깅 시스템

---

## 참고 파일

- 크롤링 코드: `AI/crawl/crawl_yesterday_law.py`
- AI 처리 코드: `AI/20251008_Gemini/bill_headline_summarizer.py`
- 샘플 CSV: `AI/crawl/bills_20250918.csv`
- 샘플 출력: `AI/20251008_Gemini/outputs_gemini-2.5-flash_20250918.csv`

