#!/bin/bash
# GCP VM 초기 설정 스크립트
# VM 생성 후 한 번만 실행

set -e

echo "=========================================="
echo "GCP VM 초기 설정 시작"
echo "=========================================="

# 1. 시스템 업데이트
echo "[1/6] 시스템 업데이트 중..."
sudo apt-get update
sudo apt-get upgrade -y

# 2. Python 3.11 설치
echo "[2/6] Python 3.11 설치 중..."
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# 3. PostgreSQL 클라이언트 설치 (Cloud SQL 연결용)
echo "[3/6] PostgreSQL 클라이언트 설치 중..."
sudo apt-get install -y postgresql-client

# 4. Git 설치
echo "[4/6] Git 설치 중..."
sudo apt-get install -y git

# 5. 앱 디렉토리 생성
echo "[5/6] 앱 디렉토리 생성 중..."
mkdir -p /home/app
cd /home/app

# 6. GitHub에서 코드 클론
echo "[6/6] GitHub에서 코드 클론 중..."
if [ -d "MyPoly-LawData" ]; then
    echo "이미 존재하는 디렉토리입니다. 건너뜁니다."
else
    git clone https://github.com/seongyonglim/MyPoly-LawData.git
fi

cd MyPoly-LawData

# 7. 가상환경 생성 및 의존성 설치
echo "[7/7] 가상환경 생성 및 의존성 설치 중..."
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 8. systemd 서비스 파일 생성
echo "systemd 서비스 파일 생성 중..."
sudo tee /etc/systemd/system/mypoly-app.service > /dev/null <<EOF
[Unit]
Description=MyPoly LawData Flask App
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/home/app/MyPoly-LawData
Environment="PATH=/home/app/MyPoly-LawData/venv/bin"
ExecStart=/home/app/MyPoly-LawData/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 9. 서비스 활성화 (자동 시작)
sudo systemctl daemon-reload
sudo systemctl enable mypoly-app

echo "=========================================="
echo "초기 설정 완료!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "1. Cloud SQL 연결 정보를 .env 파일에 설정"
echo "2. sudo systemctl start mypoly-app (서비스 시작)"
echo "3. sudo systemctl status mypoly-app (상태 확인)"

