#!/bin/bash
# 환경 변수 설정 스크립트

set -e

echo "=========================================="
echo "환경 변수 설정"
echo "=========================================="

cd ~/MyPoly-LawData

# .env 파일이 이미 있으면 백업
if [ -f ".env" ]; then
    echo "기존 .env 파일을 백업합니다..."
    cp .env .env.backup
fi

# 비밀번호 입력
echo ""
echo "Cloud SQL 비밀번호를 입력하세요:"
read -s DB_PASSWORD

if [ -z "$DB_PASSWORD" ]; then
    echo "❌ 비밀번호가 필요합니다."
    exit 1
fi

# .env 파일 생성
cat > .env << EOF
DB_HOST=127.0.0.1
DB_NAME=mypoly_lawdata
DB_USER=postgres
DB_PASSWORD=$DB_PASSWORD
DB_PORT=5432
EOF

# 권한 설정
chmod 600 .env

echo "✅ .env 파일 생성 완료"
echo "위치: $(pwd)/.env"

