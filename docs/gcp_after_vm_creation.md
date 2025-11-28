# VM 생성 후 다음 단계

## ✅ 완료된 것
- Cloud SQL 인스턴스 `mypoly-postgres` 생성 완료
- 데이터베이스 `mypoly_lawdata` 생성 완료
- VM `mypoly-app-server` 생성 완료

---

## 다음 단계

### 1단계: VM에 SSH 접속

1. **VM 인스턴스 목록으로 이동**
   - 상단 검색창에 "Compute Engine" → "VM 인스턴스" 검색
   - 또는 대시보드에서 "VM 인스턴스" 클릭

2. **SSH 접속**
   - `mypoly-app-server` 인스턴스 찾기
   - **"SSH"** 버튼 클릭 (브라우저에서 자동 연결)

---

### 2단계: VM 초기 설정 (SSH 창에서 실행)

SSH 창이 열리면 다음 명령어를 **순서대로** 실행:

```bash
# 1. 시스템 업데이트
sudo apt-get update
sudo apt-get upgrade -y

# 2. Python 3.11 설치
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# 3. PostgreSQL 클라이언트 설치
sudo apt-get install -y postgresql-client

# 4. Git 설치
sudo apt-get install -y git

# 5. 앱 디렉토리 생성
mkdir -p /home/app
cd /home/app

# 6. GitHub에서 코드 클론
git clone https://github.com/seongyonglim/MyPoly-LawData.git
cd MyPoly-LawData

# 7. 가상환경 생성
python3.11 -m venv venv
source venv/bin/activate

# 8. 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 3단계: Cloud SQL Proxy 설정

SSH 창에서 계속:

```bash
# 1. Cloud SQL Proxy 다운로드
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy
sudo mv cloud_sql_proxy /usr/local/bin/

# 2. 연결 이름 확인 (GCP 콘솔에서 복사)
# 예: fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres

# 3. Cloud SQL Proxy 실행 (백그라운드)
CONNECTION_NAME="여기에_연결이름_붙여넣기"
nohup cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5432 > /tmp/cloud_sql_proxy.log 2>&1 &

# 4. 실행 확인
ps aux | grep cloud_sql_proxy
```

---

### 4단계: 환경 변수 설정

SSH 창에서:

```bash
cd /home/app/MyPoly-LawData

# .env 파일 생성
cat > .env << EOF
DB_HOST=127.0.0.1
DB_NAME=mypoly_lawdata
DB_USER=postgres
DB_PASSWORD=Mypoly!2025
DB_PORT=5432
EOF

# 권한 설정
chmod 600 .env
```

---

### 5단계: 로컬 데이터 마이그레이션

**로컬 PC에서** (VM이 아닌):

```bash
# 방법 1: 마이그레이션 스크립트 사용
# 먼저 scripts/gcp/migrate_data_to_cloud_sql.py 파일에서
# CLOUD_DB의 host를 VM의 공개 IP로 변경하거나
# 직접 Cloud SQL 공개 IP로 연결

# Cloud SQL 공개 IP로 직접 연결하려면:
# scripts/gcp/migrate_data_to_cloud_sql.py 파일 수정 필요
```

또는 **GCP 콘솔에서**:
1. Cloud SQL → 인스턴스 → "가져오기" 클릭
2. 로컬에서 pg_dump로 덤프한 SQL 파일 업로드

---

### 6단계: 앱 실행 및 테스트

SSH 창에서:

```bash
cd /home/app/MyPoly-LawData
source venv/bin/activate

# 환경 변수 로드
export $(cat .env | xargs)

# 앱 실행
python app.py
```

**접속 확인:**
1. VM의 **공개 IP 주소** 확인 (Compute Engine → VM 인스턴스)
2. 브라우저에서: `http://VM공개IP:5000` 접속

---

## 체크리스트

- [ ] VM에 SSH 접속 완료
- [ ] 초기 설정 완료 (Python, Git, PostgreSQL 클라이언트)
- [ ] GitHub에서 코드 클론 완료
- [ ] 가상환경 생성 및 의존성 설치 완료
- [ ] Cloud SQL Proxy 실행 중
- [ ] 환경 변수 설정 완료
- [ ] 로컬 데이터 마이그레이션 완료
- [ ] 앱 실행 및 접속 확인

