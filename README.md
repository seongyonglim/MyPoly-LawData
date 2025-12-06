# MyPoly-LawData

2025년 국회 의안 표결 결과 데이터 수집 및 분석 시스템

## 📋 프로젝트 개요

국회 의안 정보, 표결 결과, 의원 정보를 수집하고 AI를 활용하여 분석하는 웹 대시보드 시스템입니다.

## 🚀 빠른 시작

### 1. 환경 설정

`.env` 파일 생성 및 다음 정보 입력:
```
# 로컬 DB
LOCAL_DB_HOST=localhost
LOCAL_DB_NAME=mypoly_lawdata
LOCAL_DB_USER=postgres
LOCAL_DB_PASSWORD=your_password
LOCAL_DB_PORT=5432

# GCP Cloud SQL (선택)
CLOUD_DB_HOST=your_cloud_sql_ip
CLOUD_DB_NAME=mypoly_lawdata
CLOUD_DB_USER=postgres
CLOUD_DB_PASSWORD=your_cloud_password
CLOUD_DB_PORT=5432

# API Keys
BILL_SERVICE_KEY=your_bill_api_key
ASSEMBLY_SERVICE_KEY=your_assembly_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 설정

```bash
# PostgreSQL 데이터베이스 생성 후
psql -U postgres -d mypoly_lawdata -f scripts/db/create_tables_postgresql.sql
```

### 4. 데이터 수집

```bash
# 의원 정보 수집
python scripts/db/collect_22nd_members_complete.py

# 의안 정보 수집 (2025-01-01부터 현재까지)
python scripts/db/collect_bills_from_date.py 20250101

# 표결 정보 수집
python scripts/db/collect_votes_from_date.py 20250101

# AI 요약 (의안 제목 및 요약 생성)
python ai_summarizer/bill_headline_summarizer_db.py
```

### 5. 애플리케이션 실행

```bash
python app.py
```

웹 브라우저에서 `http://localhost:5000` 접속

## 📁 프로젝트 구조

```
MyPoly-LawData/
├── app.py                          # Flask 웹 애플리케이션
├── ai_summarizer/                  # AI 요약 스크립트
│   └── bill_headline_summarizer_db.py
├── scripts/
│   ├── db/                         # 데이터 수집 스크립트
│   │   ├── collect_bills_from_date.py      # 의안 정보 수집
│   │   ├── collect_votes_from_date.py     # 표결 정보 수집
│   │   ├── collect_22nd_members_complete.py # 의원 정보 수집
│   │   ├── create_tables_postgresql.sql    # DB 스키마
│   │   └── README.md                       # 상세 사용 가이드
│   └── gcp/                        # GCP 마이그레이션
│       ├── migrate_direct_public_ip.py     # 데이터 마이그레이션
│       └── README.md                       # 마이그레이션 가이드
├── templates/                      # HTML 템플릿
├── static/                         # CSS, JavaScript
└── .env                           # 환경 변수 (Git에 포함되지 않음)
```

## 🔑 주요 기능

1. **데이터 수집**
   - 의안 정보 수집 (`scripts/db/collect_bills_from_date.py`)
   - 표결 결과 수집 (`scripts/db/collect_votes_from_date.py`)
   - 의원 정보 수집 (`scripts/db/collect_22nd_members_complete.py`)

2. **AI 분석**
   - 의안 제목 및 요약 생성 (`ai_summarizer/bill_headline_summarizer_db.py`)

3. **데이터 마이그레이션**
   - 로컬 → GCP Cloud SQL (`scripts/gcp/migrate_direct_public_ip.py`)

4. **웹 대시보드**
   - 의안 대시보드
   - 의안 데이터 품질 대시보드
   - 의원 데이터 품질 대시보드
   - 테이블 구조 조회

## 📝 데이터 갱신 워크플로우

1. 로컬에서 데이터 수집
   ```bash
   python scripts/db/collect_bills_from_date.py 20250101
   python scripts/db/collect_votes_from_date.py 20250101
   python ai_summarizer/bill_headline_summarizer_db.py
   ```

2. GCP로 마이그레이션
   ```bash
   python scripts/gcp/migrate_direct_public_ip.py
   ```

3. GCP VM에서 앱 재시작 (필요시)

## 🔒 보안

- 모든 API 키와 비밀번호는 환경 변수로 관리
- `.env` 파일은 `.gitignore`에 포함되어 Git에 커밋되지 않음
