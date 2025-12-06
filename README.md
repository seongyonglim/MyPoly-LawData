# MyPoly-LawData

2025년 국회 의안 표결 결과 데이터 수집 및 분석 시스템

## 📋 프로젝트 개요

국회 의안 정보, 표결 결과, 의원 정보를 수집하고 AI를 활용하여 분석하는 웹 대시보드 시스템입니다.

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# .env 파일 생성 (예시는 .env.example 참고)
cp .env.example .env

# .env 파일에 다음 정보 입력:
# - DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT
# - BILL_SERVICE_KEY (공공데이터포털 의안정보 API)
# - ASSEMBLY_SERVICE_KEY (열린국회정보 API)
# - GEMINI_API_KEY (Google Gemini API)
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
│   ├── db/                         # 데이터베이스 관련 스크립트
│   │   ├── collect_bills_from_date.py      # 의안 정보 수집
│   │   ├── collect_votes_from_date.py     # 표결 정보 수집
│   │   ├── collect_22nd_members_complete.py # 의원 정보 수집
│   │   ├── comprehensive_data_fix.py       # 데이터 품질 점검 및 수정
│   │   └── README.md                       # 상세 사용 가이드
│   └── test_api_samples.py         # API 테스트 스크립트
├── templates/                      # HTML 템플릿
├── static/                         # CSS, JavaScript
└── docs/                           # 문서

```

## 🔑 환경 변수

필수 환경 변수:

- `DB_HOST`: 데이터베이스 호스트 (기본값: localhost)
- `DB_NAME`: 데이터베이스 이름 (기본값: mypoly_lawdata)
- `DB_USER`: 데이터베이스 사용자 (기본값: postgres)
- `DB_PASSWORD`: 데이터베이스 비밀번호 (필수)
- `DB_PORT`: 데이터베이스 포트 (기본값: 5432)
- `BILL_SERVICE_KEY`: 공공데이터포털 의안정보 API 키 (필수)
- `ASSEMBLY_SERVICE_KEY`: 열린국회정보 API 키 (필수)
- `GEMINI_API_KEY`: Google Gemini API 키 (AI 요약용, 필수)

## 📊 주요 기능

- **의안 정보 수집**: 국회 의안 정보 자동 수집
- **표결 결과 수집**: 의원별 표결 결과 수집 및 분석
- **AI 요약**: Gemini API를 활용한 의안 요약 및 카테고리 분류
- **웹 대시보드**: 의안 및 표결 결과 시각화
- **데이터 품질 관리**: 자동 데이터 검증 및 보완

## 📝 데이터 수집 스크립트

자세한 사용법은 `scripts/db/README.md` 참고

## 🔒 보안

- 모든 API 키와 비밀번호는 환경 변수로 관리
- `.env` 파일은 `.gitignore`에 포함되어 Git에 커밋되지 않음
- 프로덕션 환경에서는 환경 변수 또는 시크릿 관리 서비스 사용 권장

## 📄 라이선스

이 프로젝트는 개인 프로젝트입니다.
