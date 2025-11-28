# GCP VM 설정 스크립트

## 사용 순서

### 1. 초기 설정 (한 번만 실행)
```bash
cd ~
wget https://raw.githubusercontent.com/seongyonglim/MyPoly-LawData/main/scripts/gcp/setup_vm_complete.sh
chmod +x setup_vm_complete.sh
./setup_vm_complete.sh
```

또는 GitHub에서 클론한 후:
```bash
cd ~/MyPoly-LawData
chmod +x scripts/gcp/setup_vm_complete.sh
./scripts/gcp/setup_vm_complete.sh
```

### 2. 환경 변수 설정
```bash
cd ~/MyPoly-LawData
chmod +x scripts/gcp/setup_env.sh
./scripts/gcp/setup_env.sh
# Cloud SQL 비밀번호 입력
```

### 3. Cloud SQL Proxy 시작
```bash
cd ~/MyPoly-LawData
chmod +x scripts/gcp/start_cloud_sql_proxy.sh
./scripts/gcp/start_cloud_sql_proxy.sh
# 연결 이름 입력 (예: fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres)
```

### 4. 앱 실행
```bash
cd ~/MyPoly-LawData
chmod +x scripts/gcp/start_app.sh
./scripts/gcp/start_app.sh
```

## 빠른 시작 (한 번에 실행)

```bash
# 1. 초기 설정
cd ~
git clone https://github.com/seongyonglim/MyPoly-LawData.git
cd MyPoly-LawData
chmod +x scripts/gcp/*.sh
./scripts/gcp/setup_vm_complete.sh

# 2. 환경 변수 설정
./scripts/gcp/setup_env.sh

# 3. Cloud SQL Proxy 시작
export CLOUD_SQL_CONNECTION_NAME="fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres"
./scripts/gcp/start_cloud_sql_proxy.sh

# 4. 앱 실행
./scripts/gcp/start_app.sh
```

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

# 데이터베이스 연결 테스트
psql -h 127.0.0.1 -U postgres -d mypoly_lawdata
```

