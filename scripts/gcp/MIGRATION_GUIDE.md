# 로컬 DB → Cloud SQL 마이그레이션 가이드

## 📋 개요

로컬 PC의 PostgreSQL 데이터를 GCP Cloud SQL로 마이그레이션하는 방법입니다.

## 🔧 사전 준비

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

### 2. GCP 방화벽 규칙 설정

1. **GCP 콘솔** → **Cloud SQL** → 인스턴스 `mypoly-postgres` 클릭
2. **"연결"** 탭 클릭
3. **"승인된 네트워크"** 섹션에서 **"네트워크 추가"** 클릭
4. 다음 정보 입력:
   - **이름**: `로컬PC` (또는 원하는 이름)
   - **네트워크**: `YOUR_PUBLIC_IP/32` (로컬 PC의 공개 IP)
     - 공개 IP 확인: https://www.whatismyip.com/
5. **"저장"** 클릭

## 🚀 마이그레이션 실행

### Windows PowerShell

```powershell
# 프로젝트 디렉토리로 이동
cd C:\polywave\MyPoly-LawData

# 가상환경 활성화 (이미 있다면 생략 가능)
.venv\Scripts\Activate.ps1

# 또는 새로 만들기
# python -m venv .venv
# .venv\Scripts\Activate.ps1
# pip install psycopg2-binary python-dotenv

# 마이그레이션 실행
python scripts/gcp/migrate_direct_public_ip.py
```

### Linux/Mac

```bash
# 프로젝트 디렉토리로 이동
cd ~/MyPoly-LawData

# 가상환경 활성화
source venv/bin/activate

# 또는 새로 만들기
# python3 -m venv venv
# source venv/bin/activate
# pip install psycopg2-binary python-dotenv

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

- **기존 데이터 삭제**: Cloud SQL의 기존 데이터는 모두 삭제되고 로컬 데이터로 대체됩니다.
- **외래키 순서**: 테이블은 외래키 의존성을 고려한 순서로 마이그레이션됩니다.
- **배치 처리**: 대용량 데이터는 1000건씩 배치로 처리됩니다.
- **에러 처리**: 일부 레코드에서 오류가 발생해도 계속 진행됩니다.

## 🔍 문제 해결

### 연결 실패

**증상**: `❌ Cloud SQL 연결 실패`

**해결 방법**:
1. GCP 콘솔에서 방화벽 규칙 확인
2. 로컬 PC의 공개 IP가 "승인된 네트워크"에 추가되었는지 확인
3. Cloud SQL 인스턴스가 실행 중인지 확인
4. `.env` 파일의 `CLOUD_DB_HOST`와 `CLOUD_DB_PASSWORD` 확인

### 로컬 DB 연결 실패

**증상**: `❌ 로컬 DB 연결 실패`

**해결 방법**:
1. 로컬 PostgreSQL이 실행 중인지 확인
2. `.env` 파일의 `LOCAL_DB_PASSWORD` 확인
3. 로컬 DB의 데이터베이스 이름이 `mypoly_lawdata`인지 확인

## 📝 실행 예시

```
================================================================================
로컬 DB → Cloud SQL 데이터 마이그레이션 (공개 IP 직접 사용)
================================================================================

⚠️ 사전 준비:
1. GCP 콘솔 → Cloud SQL → 인스턴스 → 연결
2. '승인된 네트워크'에 로컬 PC의 공개 IP 추가
3. 공개 IP 확인: https://www.whatismyip.com/
================================================================================

[1] 로컬 DB 연결 중... (localhost:5432)
✅ 로컬 DB 연결 성공

[2] Cloud SQL 연결 중... (34.50.48.31:5432)
✅ Cloud SQL 연결 성공

[3] 데이터 마이그레이션 시작...

[proc_stage_mapping] 마이그레이션 중...
  📖 로컬 DB에서 데이터 읽는 중...
  📊 총 5건
  🗑️ 기존 데이터 삭제 중...
  ✅ 기존 데이터 삭제 완료
  💾 데이터 삽입 중...
  진행: 5/5건 (100%)
  ✅ 완료: 5건 삽입, 0건 오류

[assembly_members] 마이그레이션 중...
  ...

마이그레이션 완료! (소요 시간: 0:00:27.822953)
================================================================================
```

## 🔗 참고 문서

- [GCP 마이그레이션 완료 보고서](../docs/gcp_migration_summary.md)
- [Cloud SQL 설정 가이드](../docs/gcp_cloud_sql_setup_guide.md)

