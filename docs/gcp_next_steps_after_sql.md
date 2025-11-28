# Cloud SQL 생성 후 다음 단계

## ✅ 완료된 것
- Cloud SQL 인스턴스 `mypoly-postgres` 생성 완료

---

## 다음 단계

### 1단계: 데이터베이스 생성

1. **Cloud SQL 인스턴스 페이지로 이동**
   - 우측 하단 알림에서 `mypoly-postgres` 클릭
   - 또는 상단 검색창에 "Cloud SQL" 검색 → 인스턴스 목록

2. **데이터베이스 생성**
   - 왼쪽 메뉴에서 **"데이터베이스"** 탭 클릭
   - **"데이터베이스 만들기"** 버튼 클릭
   - 데이터베이스 이름: `mypoly_lawdata` 입력
   - **"만들기"** 클릭

3. **연결 정보 확인** (나중에 사용)
   - 인스턴스 개요 페이지에서:
     - **연결 이름**: 복사해두기 (예: `fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres`)
     - **공개 IP 주소**: 확인

---

### 2단계: Compute Engine VM 생성

1. **VM 만들기 시작**
   - 대시보드에서 **"VM 만들기"** 클릭
   - 또는 상단 검색창에 "Compute Engine" → "VM 인스턴스" 검색

2. **인스턴스 설정**
   - **이름**: `mypoly-app-server`
   - **리전**: `asia-northeast3` (서울)
   - **영역**: `asia-northeast3-a`
   - **머신 유형**: `e2-micro` 선택
   - **부팅 디스크**: Ubuntu 22.04 LTS
   - **방화벽**: **HTTP 트래픽 허용** 체크
   - **"만들기"** 클릭

3. **VM 생성 완료 대기** (1-2분)

---

### 3단계: VM 초기 설정

1. **VM에 SSH 접속**
   - VM 인스턴스 목록에서 `mypoly-app-server` 찾기
   - **"SSH"** 버튼 클릭 (브라우저에서 자동 연결)

2. **초기 설정 명령어 실행** (SSH 창에서)
```bash
# 시스템 업데이트
sudo apt-get update
sudo apt-get upgrade -y

# Python 3.11 설치
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# PostgreSQL 클라이언트 설치
sudo apt-get install -y postgresql-client

# Git 설치
sudo apt-get install -y git

# 앱 디렉토리 생성
mkdir -p /home/app
cd /home/app

# GitHub에서 코드 클론
git clone https://github.com/seongyonglim/MyPoly-LawData.git
cd MyPoly-LawData

# 가상환경 생성
python3.11 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 4단계: Cloud SQL Proxy 설정

1. **Cloud SQL Proxy 다운로드** (VM SSH 창에서)
```bash
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy
sudo mv cloud_sql_proxy /usr/local/bin/
```

2. **연결 이름 확인**
   - GCP 콘솔 → Cloud SQL → 인스턴스 개요
   - **"연결 이름"** 복사 (예: `fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres`)

3. **Cloud SQL Proxy 실행** (VM SSH 창에서)
```bash
# 연결 이름을 실제 값으로 변경
CONNECTION_NAME="여기에_연결이름_붙여넣기"

# 백그라운드로 실행
nohup cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5432 > /tmp/cloud_sql_proxy.log 2>&1 &

# 실행 확인
ps aux | grep cloud_sql_proxy
```

---

### 5단계: 환경 변수 설정

**VM SSH 창에서:**
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

### 6단계: 로컬 데이터 마이그레이션

**로컬 PC에서:**
```bash
# 방법 1: 마이그레이션 스크립트 사용
# (VM의 Cloud SQL Proxy를 통해 연결)
python scripts/gcp/migrate_data_to_cloud_sql.py

# 방법 2: pg_dump 사용
pg_dump -h localhost -U postgres -d mypoly_lawdata > local_data.sql
# 그 다음 GCP 콘솔에서 Cloud SQL → 가져오기 → SQL 파일 업로드
```

---

### 7단계: 앱 실행 및 테스트

**VM SSH 창에서:**
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

- [ ] 데이터베이스 `mypoly_lawdata` 생성 완료
- [ ] VM `mypoly-app-server` 생성 완료
- [ ] VM 초기 설정 완료
- [ ] Cloud SQL Proxy 실행 중
- [ ] 환경 변수 설정 완료
- [ ] 로컬 데이터 마이그레이션 완료
- [ ] 앱 실행 및 접속 확인

---

## 문제 해결

### Cloud SQL 연결 실패
```bash
# VM에서 Cloud SQL Proxy 확인
ps aux | grep cloud_sql_proxy

# 로그 확인
tail -f /tmp/cloud_sql_proxy.log
```

### 앱 실행 오류
```bash
# 로그 확인
python app.py

# 환경 변수 확인
cat .env
```

