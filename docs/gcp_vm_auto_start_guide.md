# VM 자동 실행 설정 가이드

PC를 꺼도 VM에서 Flask 앱이 계속 실행되도록 설정하는 방법입니다.

## 빠른 시작 (3단계)

### 1. VM에 SSH 접속

```bash
gcloud compute ssh mypoly-app-server --zone=asia-northeast3-a
```

또는 일반 SSH:
```bash
ssh seongyonglim3@34.64.212.103
```

### 2. systemd 서비스 생성

```bash
cd ~/MyPoly-LawData
git pull origin main
chmod +x scripts/gcp/create_systemd_services.sh

# Cloud SQL 연결 이름 설정 (한 번만)
export CLOUD_SQL_CONNECTION_NAME="fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres"

# 서비스 생성
./scripts/gcp/create_systemd_services.sh
```

또는 연결 이름을 직접 입력:
```bash
./scripts/gcp/create_systemd_services.sh
# 프롬프트가 나오면 연결 이름 입력
```

### 3. 서비스 시작

```bash
chmod +x scripts/gcp/manage_services.sh
./scripts/gcp/manage_services.sh start
```

## 확인

### 서비스 상태 확인

```bash
./scripts/gcp/manage_services.sh status
```

두 서비스가 모두 "active (running)" 상태여야 합니다.

### 로그 확인

```bash
# Flask 앱 로그
./scripts/gcp/manage_services.sh logs mypoly-app

# Cloud SQL Proxy 로그
./scripts/gcp/manage_services.sh logs cloud-sql-proxy
```

## 완료!

이제:
- ✅ PC를 꺼도 VM에서 계속 실행됩니다
- ✅ VM이 재시작되면 자동으로 시작됩니다
- ✅ 앱이 크래시되면 자동으로 재시작됩니다
- ✅ SSH 연결을 끊어도 계속 실행됩니다

## 서비스 관리 명령어

```bash
# 서비스 시작
./scripts/gcp/manage_services.sh start

# 서비스 중지
./scripts/gcp/manage_services.sh stop

# 서비스 재시작
./scripts/gcp/manage_services.sh restart

# 서비스 상태 확인
./scripts/gcp/manage_services.sh status

# 로그 보기 (Flask 앱)
./scripts/gcp/manage_services.sh logs mypoly-app

# 로그 보기 (Cloud SQL Proxy)
./scripts/gcp/manage_services.sh logs cloud-sql-proxy
```

## 문제 해결

### 서비스가 시작되지 않을 때

1. 상태 확인:
   ```bash
   sudo systemctl status mypoly-app
   ```

2. 로그 확인:
   ```bash
   sudo journalctl -u mypoly-app -n 50
   ```

3. 일반적인 원인:
   - `.env` 파일이 없거나 잘못됨
   - Cloud SQL Proxy가 실행되지 않음
   - 데이터베이스 연결 오류

### Cloud SQL Proxy 연결 문제

1. 로그 확인:
   ```bash
   sudo journalctl -u cloud-sql-proxy -f
   ```

2. 연결 이름 확인:
   ```bash
   sudo systemctl cat cloud-sql-proxy | grep instances
   ```

3. 수동으로 테스트:
   ```bash
   /usr/local/bin/cloud_sql_proxy -instances=fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres=tcp:5432
   ```

## 참고

- 서비스 파일 위치: `/etc/systemd/system/mypoly-app.service`, `/etc/systemd/system/cloud-sql-proxy.service`
- 로그 위치: `sudo journalctl -u mypoly-app`, `sudo journalctl -u cloud-sql-proxy`
- 자동 시작 설정: `sudo systemctl enable mypoly-app` (이미 설정됨)

