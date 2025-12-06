# GCP VM에서 앱 실행하기

## 방법 1: 직접 실행 (간단)
```bash
cd ~/MyPoly-LawData
python3 app.py
```

## 방법 2: 백그라운드 실행
```bash
cd ~/MyPoly-LawData

# nohup으로 백그라운드 실행
nohup python3 app.py > app.log 2>&1 &

# 프로세스 확인
ps aux | grep app.py

# 로그 확인
tail -f app.log

# 종료
pkill -f "python3 app.py"
```

## 방법 3: systemd 서비스 설정 (영구 실행)
```bash
cd ~/MyPoly-LawData

# 서비스 파일 생성
sudo nano /etc/systemd/system/mypoly-lawdata.service
```

서비스 파일 내용:
```ini
[Unit]
Description=MyPoly LawData Flask App
After=network.target

[Service]
Type=simple
User=seongyonglim3
WorkingDirectory=/home/seongyonglim3/MyPoly-LawData
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /home/seongyonglim3/MyPoly-LawData/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

서비스 활성화:
```bash
# 서비스 파일 리로드
sudo systemctl daemon-reload

# 서비스 시작
sudo systemctl start mypoly-lawdata

# 서비스 상태 확인
sudo systemctl status mypoly-lawdata

# 부팅 시 자동 시작
sudo systemctl enable mypoly-lawdata

# 로그 확인
sudo journalctl -u mypoly-lawdata -f
```

## 방법 4: screen/tmux 사용
```bash
# screen 설치 (없는 경우)
sudo apt install screen

# screen 세션 시작
screen -S mypoly

# 앱 실행
cd ~/MyPoly-LawData
python3 app.py

# 세션에서 나가기 (Ctrl+A, D)
# 세션 다시 접속
screen -r mypoly
```

## 포트 확인
```bash
# 앱이 실행 중인 포트 확인
netstat -tlnp | grep python
# 또는
ss -tlnp | grep python
```

## 환경 변수 확인
```bash
# .env 파일 확인
cat .env

# 필요한 환경 변수가 모두 있는지 확인
# - DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT
# - BILL_SERVICE_KEY, ASSEMBLY_SERVICE_KEY, GEMINI_API_KEY
```

