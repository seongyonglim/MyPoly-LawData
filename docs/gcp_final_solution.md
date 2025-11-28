# 최종 해결 방법: VM에서 직접 로컬 DB 접속

## 문제 원인

1. **GCP 콘솔 가져오기**: 내부적으로 `--clean` 옵션 사용 → 소유자 권한 필요
2. **CSV 방식**: 인코딩, 데이터 타입 문제
3. **SQL 덤프**: 확장, 소유자 문제

## 해결책: VM에서 Python 스크립트 실행

VM에서 로컬 DB에 직접 접속하여 데이터를 읽고, Cloud SQL에 삽입합니다.

---

## 1단계: 로컬 PostgreSQL 외부 접속 허용

### 1-1. 공개 IP 확인

**PowerShell:**
```powershell
(Invoke-WebRequest -Uri 'https://api.ipify.org' -UseBasicParsing).Content
```

또는 브라우저: https://www.whatismyip.com/

### 1-2. postgresql.conf 수정

**파일 위치:** `C:\Program Files\PostgreSQL\17\data\postgresql.conf`

**수정:**
```conf
# 기존:
# listen_addresses = 'localhost'

# 변경:
listen_addresses = '*'
```

### 1-3. pg_hba.conf 수정

**파일 위치:** `C:\Program Files\PostgreSQL\17\data\pg_hba.conf`

**파일 끝에 추가:**
```
# 외부 접속 허용
host    all             all             0.0.0.0/0               md5
```

### 1-4. PostgreSQL 재시작

**PowerShell (관리자 권한):**
```powershell
Restart-Service postgresql-x64-17
```

### 1-5. Windows 방화벽 설정

**PowerShell (관리자 권한):**
```powershell
New-NetFirewallRule -DisplayName "PostgreSQL" -Direction Inbound -LocalPort 5432 -Protocol TCP -Action Allow
```

---

## 2단계: VM에서 마이그레이션 실행

### 2-1. VM SSH 접속

```bash
ssh seongyonglim3@34.64.212.103
```

### 2-2. 최신 코드 가져오기

```bash
cd ~/MyPoly-LawData
git pull origin main
source venv/bin/activate
```

### 2-3. Cloud SQL Proxy 확인

```bash
ps aux | grep cloud_sql_proxy
# 실행 중이 아니면:
cd ~/MyPoly-LawData
export CLOUD_SQL_CONNECTION_NAME="fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres"
./scripts/gcp/start_cloud_sql_proxy.sh
```

### 2-4. 마이그레이션 실행

```bash
# 로컬 DB IP 설정 (1단계에서 확인한 공개 IP)
export LOCAL_DB_IP='[로컬PC공개IP]'

# 마이그레이션 실행
python scripts/gcp/migrate_direct_python.py
```

---

## 예상 결과

```
================================================================================
로컬 DB → Cloud SQL 데이터 마이그레이션 (VM에서 실행)
================================================================================

로컬 DB IP: [공개IP]

[1] 로컬 DB 연결 중... ([공개IP]:5432)
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

## 이 방법의 장점

1. ✅ **권한 문제 없음**: TRUNCATE만 사용 (DROP 없음)
2. ✅ **인코딩 문제 없음**: Python으로 직접 처리
3. ✅ **데이터 타입 문제 없음**: psycopg2가 자동 변환
4. ✅ **빠름**: 배치 삽입 사용
5. ✅ **안전함**: 오류 발생 시 롤백

---

## 문제 발생 시

### 로컬 DB 연결 실패
- PostgreSQL이 재시작되었는지 확인
- Windows 방화벽에서 포트 5432 허용 확인
- 공개 IP가 올바른지 확인

### Cloud SQL 연결 실패
- Cloud SQL Proxy가 실행 중인지 확인
- VM의 .env 파일에 DB 비밀번호가 올바른지 확인

