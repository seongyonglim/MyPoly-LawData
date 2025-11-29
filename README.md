# MyPoly-LawData

2025년 의안 표결 결과 웹 대시보드

## 프로젝트 소개

국회의원 표결 정보를 시각화하고 분석하는 웹 애플리케이션입니다.

## 주요 기능

- **의안 대시보드**: 2025년 의안 표결 결과를 한눈에 확인
- **테이블 구조 확인**: 데이터베이스 테이블 구조 및 통계 정보

## 기술 스택

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript

## 설치 및 실행

### 필수 요구사항

- Python 3.8 이상
- PostgreSQL 12 이상

### 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 설정
# scripts/db/create_tables_postgresql.sql 실행
psql -U postgres -d mypoly_lawdata -f scripts/db/create_tables_postgresql.sql
```

### 데이터 수집

```bash
# 22대 국회의원 정보 수집
python scripts/db/collect_22nd_members_complete.py

# 의안 정보 수집 (2025년 8월 1일 이후)
python scripts/db/collect_bills_from_date.py 20250801

# 표결 정보 수집 (2025년 10월 15일 이후)
python scripts/db/collect_votes_from_date.py 20251015
```

### 실행

```bash
python app.py
```

서버가 시작되면 http://localhost:5000 에서 접속할 수 있습니다.

## 프로젝트 구조

```
MyPoly-LawData/
├── app.py                 # Flask 애플리케이션
├── requirements.txt       # Python 의존성
├── scripts/
│   └── db/               # 데이터 수집 및 관리 스크립트
├── templates/            # HTML 템플릿
├── static/               # CSS, JavaScript 파일
└── docs/                 # 문서
```

## 배포

GCP (Google Cloud Platform)를 사용하여 배포할 수 있습니다.

자세한 배포 가이드는 `docs/gcp_migration_summary.md`를 참고하세요.

## 라이선스

이 프로젝트는 개인 프로젝트입니다.
