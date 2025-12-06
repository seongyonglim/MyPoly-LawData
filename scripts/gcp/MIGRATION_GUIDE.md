# 로컬 DB → Cloud SQL 마이그레이션 가이드

## 📋 개요

로컬 PC의 PostgreSQL 데이터를 GCP Cloud SQL로 마이그레이션하는 방법입니다.

## 🔧 방법 1: pg_dump + psql (쉘 명령어) - 권장

### 1. GCP 방화벽 규칙 설정

1. **GCP 콘솔** → **Cloud SQL** → 인스턴스 `mypoly-postgres` 클릭
2. **"연결"** 탭 클릭
3. **"승인된 네트워크"** 섹션에서 **"네트워크 추가"** 클릭
4. 다음 정보 입력:
   - **이름**: `로컬PC` (또는 원하는 이름)
   - **네트워크**: `YOUR_PUBLIC_IP/32` (로컬 PC의 공개 IP)
     - 공개 IP 확인: https://www.whatismyip.com/
5. **"저장"** 클릭

### 2. 로컬 DB 덤프 생성

**Windows PowerShell:**

```powershell
# 프로젝트 디렉토리로 이동
cd C:\polywave\MyPoly-LawData

# 덤프 파일 생성 (데이터만, 스키마 제외)
pg_dump -h localhost -U postgres -d mypoly_lawdata --data-only --no-owner --no-privileges > local_data.sql

# 또는 전체 덤프 (스키마 + 데이터)
pg_dump -h localhost -U postgres -d mypoly_lawdata --no-owner --no-privileges > local_data_full.sql
```

**Linux/Mac:**

```bash
cd ~/MyPoly-LawData

# 덤프 파일 생성
pg_dump -h localhost -U postgres -d mypoly_lawdata --data-only --no-owner --no-privileges > local_data.sql
```

### 3. Cloud SQL에 테이블 스키마 생성 (필요한 경우)

```powershell
# Cloud SQL 공개 IP로 직접 연결하여 스키마 생성
psql -h 34.50.48.31 -U postgres -d mypoly_lawdata -f scripts/db/create_tables_postgresql.sql
```

### 4. Cloud SQL에 데이터 복원

```powershell
# 덤프 파일을 Cloud SQL로 복원
psql -h 34.50.48.31 -U postgres -d mypoly_lawdata -f local_data.sql
```

**전체 명령어 예시:**

```powershell
# 1. 덤프 생성
pg_dump -h localhost -U postgres -d mypoly_lawdata --data-only --no-owner --no-privileges > local_data.sql

# 2. Cloud SQL에 스키마 생성 (처음 한 번만)
psql -h 34.50.48.31 -U postgres -d mypoly_lawdata -f scripts/db/create_tables_postgresql.sql

# 3. 데이터 복원
psql -h 34.50.48.31 -U postgres -d mypoly_lawdata -f local_data.sql
```

## 🔧 방법 2: Python 스크립트 사용

### 1. 환경 변수 설정

프로젝트 루트의 `.env` 파일에 다음을 추가:

```env
# 로컬 DB 설정
LOCAL_DB_HOST=localhost
LOCAL_DB_NAME=mypoly_lawdata
LOCAL_DB_USER=postgres
LOCAL_DB_PASSWORD=your_local_password
LOCAL_DB_PORT=5432

# Cloud SQL 설정
CLOUD_DB_HOST=34.50.48.31  # Cloud SQL 공개 IP (GCP 콘솔에서 확인)
CLOUD_DB_NAME=mypoly_lawdata
CLOUD_DB_USER=postgres
CLOUD_DB_PASSWORD=your_cloud_password
CLOUD_DB_PORT=5432
```

### 2. 마이그레이션 실행

```powershell
# 프로젝트 디렉토리로 이동
cd C:\polywave\MyPoly-LawData

# 가상환경 활성화
.venv\Scripts\Activate.ps1

# 필요한 패키지 설치 (처음 한 번만)
pip install python-dotenv psycopg2-binary

# 또는 requirements.txt의 모든 패키지 설치
# pip install -r requirements.txt

# 마이그레이션 실행
python scripts/gcp/migrate_direct_public_ip.py
```

## 📊 마이그레이션 대상 테이블

다음 순서로 마이그레이션됩니다:

1. `proc_stage_mapping` - 진행단계 매핑
2. `assembly_members` - 국회의원 정보
3. `bills` - 의안 정보
4. `votes` - 표결 정보

## ⚠️ 주의사항

### pg_dump 옵션 설명

- `--data-only`: 데이터만 덤프 (스키마 제외)
- `--no-owner`: 소유자 정보 제외 (Cloud SQL 권한 문제 방지)
- `--no-privileges`: 권한 정보 제외 (Cloud SQL 권한 문제 방지)

### psql 연결 시

- Cloud SQL 공개 IP: GCP 콘솔에서 확인
- 비밀번호: Cloud SQL 인스턴스 설정에서 확인
- 연결 실패 시: GCP 방화벽 규칙 확인

## 🔍 문제 해결

### 연결 실패

**증상**: `psql: could not connect to server`

**해결 방법**:
1. GCP 콘솔에서 방화벽 규칙 확인
2. 로컬 PC의 공개 IP가 "승인된 네트워크"에 추가되었는지 확인
3. Cloud SQL 인스턴스가 실행 중인지 확인

### 권한 오류

**증상**: `ERROR: permission denied`

**해결 방법**:
- `--no-owner --no-privileges` 옵션 사용
- 또는 `SET session_replication_role = replica;` 사용

### 인코딩 문제

**증상**: 한글이 깨짐

**해결 방법**:
```powershell
# UTF-8 인코딩 명시
$env:PGCLIENTENCODING="UTF8"
pg_dump -h localhost -U postgres -d mypoly_lawdata --data-only --no-owner --no-privileges > local_data.sql
```

## 📝 실행 예시

```powershell
# 1. 덤프 생성
PS C:\polywave\MyPoly-LawData> pg_dump -h localhost -U postgres -d mypoly_lawdata --data-only --no-owner --no-privileges > local_data.sql
Password: 

# 2. Cloud SQL에 스키마 생성
PS C:\polywave\MyPoly-LawData> psql -h 34.50.48.31 -U postgres -d mypoly_lawdata -f scripts/db/create_tables_postgresql.sql
Password: 

# 3. 데이터 복원
PS C:\polywave\MyPoly-LawData> psql -h 34.50.48.31 -U postgres -d mypoly_lawdata -f local_data.sql
Password: 
COPY 5
COPY 306
COPY 7421
COPY 98904
```

## 🔗 참고 문서

- [GCP 마이그레이션 완료 보고서](../docs/gcp_migration_summary.md)
- [Cloud SQL 설정 가이드](../docs/gcp_cloud_sql_setup_guide.md)
