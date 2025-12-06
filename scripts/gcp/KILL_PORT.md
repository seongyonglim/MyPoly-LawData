# 포트 사용 중인 프로세스 종료하기

## 포트 5000을 사용하는 프로세스 찾기 및 종료

```bash
# 1. 포트 5000을 사용하는 프로세스 찾기
sudo lsof -i :5000
# 또는
sudo netstat -tlnp | grep 5000
# 또는
sudo ss -tlnp | grep 5000

# 2. 프로세스 ID 확인 후 종료
# 예: PID가 12345인 경우
kill -9 12345

# 3. 또는 한 번에 종료
sudo fuser -k 5000/tcp
```

## 강제로 모든 Python 프로세스 종료 (주의)

```bash
# 모든 Python 프로세스 확인
ps aux | grep python

# 특정 사용자의 Python 프로세스만 종료
pkill -u seongyonglim3 python

# 또는 더 강력하게
killall -9 python3
killall -9 python
```

## 안전한 재시작 스크립트

```bash
cd ~/MyPoly-LawData

# 1. 포트 사용 프로세스 강제 종료
sudo fuser -k 5000/tcp 2>/dev/null

# 2. Python app.py 프로세스 종료
pkill -9 -f "python.*app.py"

# 3. 잠시 대기
sleep 3

# 4. 포트 확인
netstat -tlnp | grep 5000

# 5. 새로 실행
nohup python3 app.py > app.log 2>&1 &

# 6. 로그 확인
sleep 2
tail -f app.log
```

