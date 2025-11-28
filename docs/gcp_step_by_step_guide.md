# GCP 설정 단계별 가이드 (처음부터)

## 현재 상태 확인
- ✅ 무료 체험판 활성화됨 (₩426,353 크레딧, 2026년 2월 28일 만료)
- ✅ "My First Project" 프로젝트 생성됨

---

## 1단계: Cloud SQL (PostgreSQL) 생성

### 1.1 데이터베이스 만들기 시작
1. 대시보드에서 **"데이터베이스 만들기"** (보라색 테두리) 클릭
   - 또는 상단 검색창에 "Cloud SQL" 검색

### 1.2 데이터베이스 엔진 선택
1. **"PostgreSQL"** 선택
2. **"다음"** 클릭

### 1.3 인스턴스 설정

#### 인스턴스 정보
- **인스턴스 ID**: `mypoly-postgres` 입력
- **비밀번호**: 
  - "생성" 버튼 클릭하여 자동 생성하거나
  - 직접 입력 (강력한 비밀번호, **반드시 기록!**)

#### 리전 및 영역
- **리전**: `asia-northeast3` (서울) 선택
- **영역**: `asia-northeast3-a` 선택

#### 머신 구성
- **머신 유형**: **"커스텀"** 클릭
  - 또는 "사전 설정"에서 **"db-f1-micro"** 선택
- **vCPU**: 1개
- **메모리**: 0.6GB (614MB)

#### 저장용량
- **저장용량 유형**: SSD
- **저장용량**: **10GB** 입력 (나중에 확장 가능)

#### 연결
- **공개 IP**: 체크 (기본값)
- **비공개 IP**: 체크 해제 (나중에 필요하면 추가)

#### 백업
- **자동 백업**: 체크 해제 (비용 절약, 나중에 활성화 가능)

#### 가용성
- **가용성**: **"단일 영역"** 선택 (고가용성 불필요)

### 1.4 생성
1. 하단 **"인스턴스 만들기"** 클릭
2. 생성 완료까지 2-3분 소요

---

## 2단계: 데이터베이스 생성

### 2.1 Cloud SQL 인스턴스 페이지로 이동
1. 생성 완료 후 인스턴스 이름 클릭
2. 또는 상단 검색창에 "Cloud SQL" 검색 → 인스턴스 목록

### 2.2 데이터베이스 생성
1. 왼쪽 메뉴에서 **"데이터베이스"** 클릭
2. **"데이터베이스 만들기"** 클릭
3. 데이터베이스 이름: `mypoly_lawdata` 입력
4. **"만들기"** 클릭

### 2.3 연결 정보 확인
1. 인스턴스 개요 페이지에서:
   - **연결 이름**: `fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres` 형식
   - **공개 IP 주소**: 확인 (나중에 사용)
   - **비밀번호**: 위에서 설정한 비밀번호

---

## 3단계: Compute Engine VM 생성

### 3.1 VM 만들기 시작
1. 대시보드에서 **"VM 만들기"** 클릭
   - 또는 상단 검색창에 "Compute Engine" 검색

### 3.2 인스턴스 설정

#### 기본 정보
- **이름**: `mypoly-app-server` 입력
- **리전**: `asia-northeast3` (서울) 선택
- **영역**: `asia-northeast3-a` 선택

#### 머신 구성
- **머신 패밀리**: **일반 용도**
- **시리즈**: **E2**
- **머신 유형**: **e2-micro** 선택
  - vCPU: 2개 (공유)
  - 메모리: 1GB

#### 부팅 디스크
- **운영체제**: **Ubuntu**
- **버전**: **Ubuntu 22.04 LTS** 선택
- **부팅 디스크 유형**: **표준 영구 디스크**
- **크기**: 10GB (기본값)

#### 방화벽
- **HTTP 트래픽 허용**: ✅ 체크
- **HTTPS 트래픽 허용**: ✅ 체크

### 3.3 생성
1. 하단 **"만들기"** 클릭
2. 생성 완료까지 1-2분 소요

---

## 4단계: VM 초기 설정

### 4.1 VM에 SSH 접속
1. VM 인스턴스 목록에서 `mypoly-app-server` 찾기
2. **"SSH"** 버튼 클릭 (브라우저에서 자동 연결)

### 4.2 초기 설정 스크립트 실행
SSH 창에서 다음 명령어 실행:

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

## 5단계: Cloud SQL Proxy 설정

### 5.1 Cloud SQL Proxy 다운로드
VM SSH 창에서:

```bash
# Cloud SQL Proxy 다운로드
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy
sudo mv cloud_sql_proxy /usr/local/bin/
```

### 5.2 연결 이름 확인
1. GCP 콘솔에서 Cloud SQL 인스턴스 페이지로 이동
2. 인스턴스 개요에서 **"연결 이름"** 복사
   - 예: `fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres`

### 5.3 Cloud SQL Proxy 실행
VM SSH 창에서:

```bash
# 연결 이름을 실제 값으로 변경
CONNECTION_NAME="fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres"

# 백그라운드로 실행
nohup cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5432 > /tmp/cloud_sql_proxy.log 2>&1 &

# 실행 확인
ps aux | grep cloud_sql_proxy
```

---

## 6단계: 환경 변수 설정

### 6.1 .env 파일 생성
VM SSH 창에서:

```bash
cd /home/app/MyPoly-LawData

# .env 파일 생성
cat > .env << EOF
DB_HOST=127.0.0.1
DB_NAME=mypoly_lawdata
DB_USER=postgres
DB_PASSWORD=여기에_Cloud_SQL_비밀번호_입력
DB_PORT=5432
EOF

# 권한 설정
chmod 600 .env
```

### 6.2 app.py 수정 확인
`.env` 파일을 읽도록 `app.py`가 수정되어 있는지 확인 (이미 완료됨)

---

## 7단계: 로컬 데이터를 Cloud SQL로 마이그레이션

### 7.1 로컬에서 실행
로컬 PC에서:

```bash
# Cloud SQL Proxy가 실행 중이어야 함 (VM에서)
# 로컬에서 VM의 Cloud SQL Proxy로 연결하려면:
# 1. VM의 공개 IP 확인
# 2. VM의 방화벽 규칙에 5432 포트 추가

# 또는 직접 마이그레이션 스크립트 실행
# (VM의 Cloud SQL Proxy를 통해)
python scripts/gcp/migrate_data_to_cloud_sql.py
```

### 7.2 또는 pg_dump 사용
로컬 PC에서:

```bash
# 로컬 데이터 덤프
pg_dump -h localhost -U postgres -d mypoly_lawdata > local_data.sql

# Cloud SQL로 가져오기 (GCP 콘솔에서)
# 1. Cloud SQL 인스턴스 페이지
# 2. "가져오기" 클릭
# 3. SQL 파일 업로드
# 4. 데이터베이스: mypoly_lawdata 선택
```

---

## 8단계: 앱 실행

### 8.1 VM에서 앱 실행
VM SSH 창에서:

```bash
cd /home/app/MyPoly-LawData
source venv/bin/activate

# 환경 변수 로드
export $(cat .env | xargs)

# 앱 실행
python app.py
```

### 8.2 접속 확인
1. VM의 **공개 IP 주소** 확인 (Compute Engine → VM 인스턴스)
2. 브라우저에서: `http://VM공개IP:5000` 접속

---

## 9단계: 자동 배포 설정 (Cloud Build)

### 9.1 Cloud Build API 활성화
1. 상단 검색창에 "Cloud Build API" 검색
2. **"사용 설정"** 클릭

### 9.2 GitHub 연동
1. 상단 검색창에 "Cloud Build" → "트리거" 검색
2. **"트리거 만들기"** 클릭
3. 이름: `github-deploy`
4. 이벤트: **"푸시할 때"** 선택
5. 소스: **"GitHub (첫 번째 빌드)"** 선택
6. GitHub 인증 및 저장소 연결
7. 저장소: `seongyonglim/MyPoly-LawData` 선택
8. 분기: `main`
9. 구성: **"Cloud Build 구성 파일"** 선택
10. 위치: `cloudbuild.yaml`
11. **"만들기"** 클릭

---

## 완료!

이제 다음 워크플로우가 가능합니다:

```
로컬에서 개발
  ↓
GitHub 푸시
  ↓
자동으로 GCP에 배포
  ↓
로컬에서 정제한 데이터 그대로 표시
```

---

## 문제 해결

### Cloud SQL 연결 실패
```bash
# VM에서 Cloud SQL Proxy 확인
ps aux | grep cloud_sql_proxy

# 재시작
pkill cloud_sql_proxy
nohup cloud_sql_proxy -instances=연결이름=tcp:5432 > /tmp/cloud_sql_proxy.log 2>&1 &
```

### 앱 실행 오류
```bash
# 로그 확인
python app.py

# 환경 변수 확인
cat .env
```

### 방화벽 문제
1. GCP 콘솔 → "VPC 네트워크" → "방화벽"
2. "방화벽 규칙 만들기"
3. 이름: `allow-flask-5000`
4. 대상: `모든 인스턴스`
5. 소스 IP: `0.0.0.0/0`
6. 프로토콜: TCP, 포트: `5000`

