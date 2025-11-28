#!/bin/bash
# Flask 앱 시작 스크립트

set -e

echo "=========================================="
echo "Flask 앱 시작"
echo "=========================================="

cd ~/MyPoly-LawData

# 가상환경 활성화
if [ ! -d "venv" ]; then
    echo "❌ 가상환경이 없습니다. 먼저 setup_vm_complete.sh를 실행하세요."
    exit 1
fi

source venv/bin/activate

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "❌ .env 파일이 없습니다. setup_env.sh를 실행하세요."
    exit 1
fi

# 환경 변수 로드
export $(cat .env | xargs)

# Cloud SQL Proxy 확인
if ! pgrep -f "cloud_sql_proxy" > /dev/null; then
    echo "⚠️ Cloud SQL Proxy가 실행 중이 아닙니다."
    echo "start_cloud_sql_proxy.sh를 먼저 실행하세요."
    exit 1
fi

echo "앱 시작 중..."
echo "접속 주소: http://VM공개IP:5000"
echo ""
echo "종료하려면 Ctrl+C를 누르세요."
echo ""

# 앱 실행
python app.py

