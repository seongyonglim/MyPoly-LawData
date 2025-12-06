# GCP 데이터 마이그레이션

## 개요
로컬 PostgreSQL 데이터를 GCP Cloud SQL로 마이그레이션하는 스크립트입니다.

## 사용법

### 1. 환경 변수 설정
`.env` 파일에 다음 변수를 추가:
```
LOCAL_DB_HOST=localhost
LOCAL_DB_NAME=mypoly_lawdata
LOCAL_DB_USER=postgres
LOCAL_DB_PASSWORD=your_local_password
LOCAL_DB_PORT=5432

CLOUD_DB_HOST=your_cloud_sql_ip
CLOUD_DB_NAME=mypoly_lawdata
CLOUD_DB_USER=postgres
CLOUD_DB_PASSWORD=your_cloud_password
CLOUD_DB_PORT=5432
```

### 2. 마이그레이션 실행
```bash
python scripts/gcp/migrate_direct_public_ip.py
```

## 주의사항
- GCP 콘솔에서 Cloud SQL 인스턴스의 공개 IP에 로컬 PC IP를 승인된 네트워크에 추가해야 합니다
- 마이그레이션 전에 로컬 DB의 모든 트랜잭션을 종료하세요
- 대용량 데이터는 시간이 오래 걸릴 수 있습니다
