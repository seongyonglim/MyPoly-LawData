# VM에서 데이터 마이그레이션 실행 가이드

## 로컬 PC 설정 (관리자 권한 필요)

### 방법 1: Python 스크립트 자동 실행 (권장)

**PowerShell을 관리자 권한으로 실행** 후:

```powershell
cd C:\polywave\MyPoly-LawData
python scripts/db/setup_local_postgres_external_access.py
```

### 방법 2: 수동 설정

#### 1. postgresql.conf 수정

**파일 위치:** `C:\Program Files\PostgreSQL\17\data\postgresql.conf`

**찾기:** `listen_addresses`

**변경:**
```conf
listen_addresses = '*'
```

#### 2. pg_hba.conf 수정

**파일 위치:** `C:\Program Files\PostgreSQL\17\data\pg_hba.conf`

**파일 끝에 추가:**
```
# 외부 접속 허용 (VM에서 접속용)
host    all             all             0.0.0.0/0               md5
```

#### 3. PostgreSQL 재시작

**PowerShell (관리자 권한):**
```powershell
Restart-Service postgresql-x64-17
```

#### 4. Windows 방화벽 설정

**PowerShell (관리자 권한):**
```powershell
New-NetFirewallRule -DisplayName "PostgreSQL" -Direction Inbound -LocalPort 5432 -Protocol TCP -Action Allow
```

---

## VM에서 실행할 명령어

### 1. VM SSH 접속

```bash
ssh seongyonglim3@34.64.212.103
```

### 2. 최신 코드 가져오기

```bash
cd ~/MyPoly-LawData
git pull origin main
source venv/bin/activate
```

### 3. Cloud SQL Proxy 확인

```bash
# Cloud SQL Proxy가 실행 중인지 확인
ps aux | grep cloud_sql_proxy

# 실행 중이 아니면 시작
export CLOUD_SQL_CONNECTION_NAME="fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres"
./scripts/gcp/start_cloud_sql_proxy.sh
```

### 4. 마이그레이션 실행

```bash
# 로컬 DB IP 설정 (로컬 PC의 공개 IP)
# 공개 IP 확인: https://www.whatismyip.com/
export LOCAL_DB_IP='61.74.128.66'

# 마이그레이션 실행
python scripts/gcp/migrate_direct_python.py
```

---

## 예상 결과

```
================================================================================
로컬 DB → Cloud SQL 데이터 마이그레이션 (VM에서 실행)
================================================================================

로컬 DB IP: 61.74.128.66

[1] 로컬 DB 연결 중... (61.74.128.66:5432)
✅ 로컬 DB 연결 성공

[2] Cloud SQL 연결 중... (127.0.0.1:5432 via Proxy)
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

[bills] 마이그레이션 중...
  ...

[votes] 마이그레이션 중...
  ...

================================================================================
마이그레이션 완료! (소요 시간: 0:05:23)
================================================================================
```

---

## 문제 해결

### 로컬 DB 연결 실패

1. PostgreSQL이 재시작되었는지 확인
2. Windows 방화벽에서 포트 5432 허용 확인
3. 공개 IP가 올바른지 확인: https://www.whatismyip.com/

### Cloud SQL 연결 실패

1. Cloud SQL Proxy가 실행 중인지 확인
2. VM의 .env 파일에 DB 비밀번호가 올바른지 확인

