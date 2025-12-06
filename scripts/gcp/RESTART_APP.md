# GCP VM에서 앱 재시작하기

## 기존 프로세스 종료 후 재시작

```bash
cd ~/MyPoly-LawData

# 1. 실행 중인 모든 app.py 프로세스 확인
ps aux | grep app.py

# 2. 기존 프로세스 종료
pkill -f "python.*app.py"
# 또는 특정 프로세스 ID로 종료
# kill 236434 1692341

# 3. 잠시 대기 (프로세스 종료 확인)
sleep 2

# 4. 포트 사용 확인
netstat -tlnp | grep 5000
# 또는
ss -tlnp | grep 5000

# 5. 새로 실행
nohup python3 app.py > app.log 2>&1 &

# 6. 프로세스 확인
ps aux | grep app.py

# 7. 로그 확인
tail -f app.log
```

## 한 번에 실행하는 스크립트

```bash
cd ~/MyPoly-LawData
pkill -f "python.*app.py" && sleep 2 && nohup python3 app.py > app.log 2>&1 &
tail -f app.log
```

## systemd 서비스 사용 시

```bash
sudo systemctl restart mypoly-lawdata
sudo systemctl status mypoly-lawdata
```

