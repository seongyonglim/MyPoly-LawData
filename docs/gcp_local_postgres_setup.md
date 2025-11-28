# 로컬 PostgreSQL 외부 접속 설정 (VM에서 접속하기 위해)

## 1단계: 로컬 PC의 공개 IP 확인

### Windows PowerShell:
```powershell
(Invoke-WebRequest -Uri 'https://api.ipify.org').Content
```

또는 브라우저에서: https://www.whatismyip.com/

---

## 2단계: PostgreSQL 설정 변경

### 2-1. postgresql.conf 수정

PostgreSQL 설치 경로에서 `postgresql.conf` 파일 찾기:
- 일반 경로: `C:\Program Files\PostgreSQL\17\data\postgresql.conf`

**수정할 내용:**
```conf
# 기존:
# listen_addresses = 'localhost'

# 변경:
listen_addresses = '*'
```

### 2-2. pg_hba.conf 수정

같은 폴더의 `pg_hba.conf` 파일 수정:

**파일 끝에 추가:**
```
# 외부 접속 허용 (모든 IP)
host    all             all             0.0.0.0/0               md5
```

### 2-3. PostgreSQL 재시작

**Windows 서비스에서:**
1. `Win + R` → `services.msc`
2. "postgresql-x64-17" 찾기
3. 우클릭 → "다시 시작"

또는 PowerShell (관리자 권한):
```powershell
Restart-Service postgresql-x64-17
```

---

## 3단계: Windows 방화벽 설정

### PowerShell (관리자 권한):
```powershell
New-NetFirewallRule -DisplayName "PostgreSQL" -Direction Inbound -LocalPort 5432 -Protocol TCP -Action Allow
```

또는:
1. Windows 방화벽 → "고급 설정"
2. "인바운드 규칙" → "새 규칙"
3. "포트" 선택 → TCP → 5432
4. "연결 허용" 선택
5. 이름: "PostgreSQL"

---

## 4단계: 연결 테스트

### VM에서 테스트:
```bash
psql -h [로컬PC공개IP] -U postgres -d mypoly_lawdata
```

비밀번호 입력: `maza_970816`

---

## 5단계: VM에서 마이그레이션 실행

```bash
cd ~/MyPoly-LawData
source venv/bin/activate

# 로컬 DB IP 설정
export LOCAL_DB_IP='[로컬PC공개IP]'

# Cloud SQL Proxy 실행 중인지 확인
ps aux | grep cloud_sql_proxy

# 마이그레이션 실행
python scripts/gcp/migrate_direct_python.py
```

---

## 보안 참고사항

⚠️ **주의**: 이 설정은 모든 IP에서 접속을 허용합니다.
- 마이그레이션 완료 후 `pg_hba.conf`에서 해당 줄을 제거하거나
- 특정 IP만 허용하도록 변경하는 것을 권장합니다.

**특정 IP만 허용:**
```
host    all             all             [VM의공개IP]/32        md5
```

