#!/bin/bash
# Cloud SQL Proxy 설정 스크립트
# Cloud SQL에 안전하게 연결하기 위한 프록시 설정

set -e

echo "=========================================="
echo "Cloud SQL Proxy 설정 시작"
echo "=========================================="

# Cloud SQL Proxy 다운로드
echo "[1/3] Cloud SQL Proxy 다운로드 중..."
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy
sudo mv cloud_sql_proxy /usr/local/bin/

# systemd 서비스 파일 생성
echo "[2/3] systemd 서비스 파일 생성 중..."
# 연결 이름은 사용자가 설정해야 함
CONNECTION_NAME="프로젝트ID:지역:인스턴스ID"  # 여기를 수정하세요!

sudo tee /etc/systemd/system/cloud-sql-proxy.service > /dev/null <<EOF
[Unit]
Description=Cloud SQL Proxy
After=network.target

[Service]
Type=simple
User=app
ExecStart=/usr/local/bin/cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5432
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "[3/3] 서비스 활성화 중..."
sudo systemctl daemon-reload
sudo systemctl enable cloud-sql-proxy

echo "=========================================="
echo "Cloud SQL Proxy 설정 완료!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "1. CONNECTION_NAME을 실제 Cloud SQL 연결 이름으로 수정"
echo "2. sudo systemctl start cloud-sql-proxy (프록시 시작)"
echo "3. app.py에서 DB_HOST를 localhost로 설정 (프록시를 통해 연결)"

