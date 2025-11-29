# GCP 배포 가이드

## 목표
로컬에서 데이터 정제 → GitHub 푸시 → GCP 자동 배포

---

## 사전 준비

### 1. GCP 계정 설정
1. https://console.cloud.google.com 접속
2. 프로젝트 생성
3. 무료 크레딧 활성화 ($300, 90일)

### 2. 필요한 서비스
- **Compute Engine** (VM 인스턴스)
- **Cloud SQL** (PostgreSQL)
- **Cloud Build** (자동 배포)

---

## 빠른 시작

### 1단계: GCP 프로젝트 생성
```bash
# GCP 콘솔에서 프로젝트 생성
# 프로젝트 ID 기록: 예) mypoly-lawdata-123456
```

### 2단계: Cloud SQL 생성
```bash
# GCP 콘솔에서:
# 1. Cloud SQL → 인스턴스 만들기
# 2. PostgreSQL 선택
# 3. 인스턴스 ID: mypoly-postgres
# 4. 비밀번호 설정 (기록!)
# 5. 지역: asia-northeast3 (서울)
# 6. 머신: db-f1-micro (무료 티어)
```

### 3단계: Compute Engine VM 생성
```bash
# GCP 콘솔에서:
# 1. Compute Engine → VM 인스턴스 만들기
# 2. 이름: mypoly-app-server
# 3. 지역: asia-northeast3-a
# 4. 머신: e2-micro (무료 티어)
# 5. 부팅 디스크: Ubuntu 22.04 LTS
# 6. 방화벽: HTTP, HTTPS 허용
```

### 4단계: VM 초기 설정
```bash
# VM에 SSH 접속
gcloud compute ssh mypoly-app-server

# 초기 설정 스크립트 실행
cd /home/app
wget https://raw.githubusercontent.com/seongyonglim/MyPoly-LawData/main/scripts/gcp/setup_vm.sh
chmod +x setup_vm.sh
sudo ./setup_vm.sh
```

### 5단계: Cloud SQL Proxy 설정
```bash
# VM에서
cd /home/app
wget https://raw.githubusercontent.com/seongyonglim/MyPoly-LawData/main/scripts/gcp/setup_cloud_sql_proxy.sh
chmod +x setup_cloud_sql_proxy.sh

# 연결 이름 수정 후 실행
sudo ./setup_cloud_sql_proxy.sh
```

### 6단계: 데이터 마이그레이션
```bash
# 로컬에서
python scripts/gcp/migrate_data_to_cloud_sql.py
```

### 7단계: Cloud Build 트리거 설정
```bash
# GCP 콘솔에서:
# 1. Cloud Build → 트리거 만들기
# 2. GitHub 저장소 연결
# 3. 저장소: seongyonglim/MyPoly-LawData
# 4. 구성 파일: cloudbuild.yaml
```

---

## 개발 워크플로우

### 로컬에서 개발
```bash
# 1. 데이터 정제
python scripts/db/fix_data.py

# 2. 코드 수정
# app.py, templates 등 수정

# 3. 로컬 테스트
python app.py
# http://localhost:5000 확인
```

### GitHub에 푸시 (자동 배포)
```bash
git add .
git commit -m "데이터 정제 및 코드 수정"
git push origin main
# → Cloud Build가 자동으로 GCP에 배포
```

### 배포 확인
```bash
# VM에 SSH 접속
gcloud compute ssh mypoly-app-server

# 서비스 상태 확인
sudo systemctl status mypoly-app

# 로그 확인
sudo journalctl -u mypoly-app -f
```

---

## 환경 변수 설정

### 로컬 (.env)
```
DB_HOST=localhost
DB_NAME=mypoly_lawdata
DB_USER=postgres
DB_PASSWORD=로컬비밀번호
DB_PORT=5432
```

### GCP VM (.env)
```
DB_HOST=127.0.0.1  # Cloud SQL Proxy
DB_NAME=mypoly_lawdata
DB_USER=postgres
DB_PASSWORD=CloudSQL비밀번호
DB_PORT=5432
```

---

## 문제 해결

### Cloud SQL 연결 실패
```bash
# Cloud SQL Proxy 실행 확인
sudo systemctl status cloud-sql-proxy

# 재시작
sudo systemctl restart cloud-sql-proxy
```

### 배포 실패
```bash
# Cloud Build 로그 확인
gcloud builds list
gcloud builds log [BUILD_ID]
```

### 서비스 시작 실패
```bash
# 로그 확인
sudo journalctl -u mypoly-app -n 50
```

---

## 참고 문서

- [GCP 설정 가이드](docs/gcp_setup_guide.md)
- [배포 워크플로우](docs/gcp_deployment_workflow.md)
- [GCP 배포 옵션 비교](docs/gcp_deployment_options.md)

