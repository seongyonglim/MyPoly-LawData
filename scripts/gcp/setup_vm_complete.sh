#!/bin/bash
# GCP VM 완전 자동 설정 스크립트
# 이 스크립트는 VM 초기 설정을 모두 자동으로 수행합니다.

set -e

echo "=========================================="
echo "GCP VM 자동 설정 시작"
echo "=========================================="

# 1. 시스템 업데이트
echo "[1/8] 시스템 업데이트 중..."
sudo apt-get update
sudo apt-get upgrade -y

# 2. Python 3.11 설치
echo "[2/8] Python 3.11 설치 중..."
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# 3. PostgreSQL 클라이언트 설치
echo "[3/8] PostgreSQL 클라이언트 설치 중..."
sudo apt-get install -y postgresql-client

# 4. Git 설치 확인
echo "[4/8] Git 확인 중..."
if ! command -v git &> /dev/null; then
    sudo apt-get install -y git
fi

# 5. 앱 디렉토리 생성 및 코드 클론
echo "[5/8] GitHub에서 코드 클론 중..."
cd ~
if [ -d "MyPoly-LawData" ]; then
    echo "이미 존재하는 디렉토리입니다. 업데이트합니다."
    cd MyPoly-LawData
    git pull origin main
else
    git clone https://github.com/seongyonglim/MyPoly-LawData.git
    cd MyPoly-LawData
fi

# 6. 가상환경 생성 및 의존성 설치
echo "[6/8] 가상환경 생성 및 의존성 설치 중..."
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 7. Cloud SQL Proxy 다운로드
echo "[7/8] Cloud SQL Proxy 다운로드 중..."
if [ ! -f "/usr/local/bin/cloud_sql_proxy" ]; then
    wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
    chmod +x cloud_sql_proxy
    sudo mv cloud_sql_proxy /usr/local/bin/
fi

# 8. 환경 변수 파일 생성 (템플릿)
echo "[8/8] 환경 변수 파일 생성 중..."
cat > .env.template << EOF
DB_HOST=127.0.0.1
DB_NAME=mypoly_lawdata
DB_USER=postgres
DB_PASSWORD=여기에_Cloud_SQL_비밀번호_입력
DB_PORT=5432
EOF

echo "=========================================="
echo "초기 설정 완료!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "1. Cloud SQL 연결 이름 확인 (GCP 콘솔)"
echo "2. .env 파일 생성 (비밀번호 입력)"
echo "3. Cloud SQL Proxy 실행"
echo "4. 앱 실행"
echo ""
echo "현재 디렉토리: $(pwd)"
echo "가상환경 활성화: source venv/bin/activate"

