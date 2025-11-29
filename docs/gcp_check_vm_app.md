# VM에서 Flask 앱 확인 및 재시작

## 1. VM SSH 접속

```bash
ssh seongyonglim3@34.64.212.103
```

## 2. 앱 실행 상태 확인

```bash
cd ~/MyPoly-LawData
ps aux | grep "python app.py"
```

## 3. 앱이 실행 중이 아니면 시작

```bash
cd ~/MyPoly-LawData
source venv/bin/activate

# 환경 변수 확인
cat .env

# Cloud SQL Proxy 확인
ps aux | grep cloud_sql_proxy

# Cloud SQL Proxy가 실행 중이 아니면 시작
export CLOUD_SQL_CONNECTION_NAME="fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres"
./scripts/gcp/start_cloud_sql_proxy.sh

# 앱 시작
export $(cat .env | xargs)
python app.py
```

## 4. 백그라운드로 실행하려면

```bash
cd ~/MyPoly-LawData
source venv/bin/activate
export $(cat .env | xargs)
nohup python app.py > /tmp/app.log 2>&1 &
```

## 5. 로그 확인

```bash
tail -f /tmp/app.log
```

