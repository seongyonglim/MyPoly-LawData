# VM 빠른 시작 가이드

## ✅ 완료된 것
- ✅ 로컬 코드 GitHub에 푸시 완료
- ✅ VM 자동 설정 스크립트 준비 완료

---

## VM SSH 창에서 실행할 명령어

### 1단계: 초기 설정 (한 번만 실행)

```bash
# 사용자 홈 디렉토리로 이동
cd ~

# GitHub에서 코드 클론
git clone https://github.com/seongyonglim/MyPoly-LawData.git
cd MyPoly-LawData

# 스크립트 실행 권한 부여
chmod +x scripts/gcp/*.sh

# 초기 설정 실행 (Python, Git, PostgreSQL 클라이언트, 가상환경 등)
./scripts/gcp/setup_vm_complete.sh
```

**예상 시간**: 5-10분

---

### 2단계: 환경 변수 설정

```bash
cd ~/MyPoly-LawData

# 환경 변수 설정 스크립트 실행
./scripts/gcp/setup_env.sh
```

**비밀번호 입력**: `Mypoly!2025` (Cloud SQL 비밀번호)

---

### 3단계: Cloud SQL Proxy 시작

```bash
cd ~/MyPoly-LawData

# 연결 이름 설정 (GCP 콘솔에서 복사)
export CLOUD_SQL_CONNECTION_NAME="fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres"

# Cloud SQL Proxy 시작
./scripts/gcp/start_cloud_sql_proxy.sh
```

**연결 이름 확인 방법**:
1. GCP 콘솔 → Cloud SQL → 인스턴스 개요
2. "연결 이름" 복사

---

### 4단계: 앱 실행

```bash
cd ~/MyPoly-LawData

# 앱 시작
./scripts/gcp/start_app.sh
```

**접속 확인**:
1. VM의 공개 IP 확인 (Compute Engine → VM 인스턴스)
2. 브라우저에서: `http://VM공개IP:5000`

---

## 한 번에 실행 (복사해서 붙여넣기)

```bash
# 1. 초기 설정
cd ~ && git clone https://github.com/seongyonglim/MyPoly-LawData.git && cd MyPoly-LawData && chmod +x scripts/gcp/*.sh && ./scripts/gcp/setup_vm_complete.sh

# 2. 환경 변수 설정 (비밀번호 입력 필요)
./scripts/gcp/setup_env.sh

# 3. Cloud SQL Proxy 시작 (연결 이름 필요)
export CLOUD_SQL_CONNECTION_NAME="fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres"
./scripts/gcp/start_cloud_sql_proxy.sh

# 4. 앱 실행
./scripts/gcp/start_app.sh
```

---

## 문제 해결

### Cloud SQL Proxy 연결 실패
```bash
# 로그 확인
tail -f /tmp/cloud_sql_proxy.log

# 재시작
pkill -f cloud_sql_proxy
./scripts/gcp/start_cloud_sql_proxy.sh
```

### 앱 실행 오류
```bash
# 환경 변수 확인
cat .env

# 가상환경 활성화 확인
source venv/bin/activate
python --version
```

---

## 다음 단계

앱이 실행되면:
1. 로컬 데이터를 Cloud SQL로 마이그레이션
2. 자동 배포 설정 (Cloud Build)

