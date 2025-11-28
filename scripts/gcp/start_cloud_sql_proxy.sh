#!/bin/bash
# Cloud SQL Proxy 시작 스크립트

set -e

# 연결 이름을 환경 변수에서 가져오거나 직접 입력
CONNECTION_NAME="${CLOUD_SQL_CONNECTION_NAME:-}"

if [ -z "$CONNECTION_NAME" ]; then
    echo "=========================================="
    echo "Cloud SQL Proxy 시작"
    echo "=========================================="
    echo ""
    echo "Cloud SQL 연결 이름을 입력하세요:"
    echo "예: fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres"
    read -p "연결 이름: " CONNECTION_NAME
fi

if [ -z "$CONNECTION_NAME" ]; then
    echo "❌ 연결 이름이 필요합니다."
    exit 1
fi

echo "연결 이름: $CONNECTION_NAME"
echo ""

# 기존 프로세스 확인 및 종료
if pgrep -f "cloud_sql_proxy" > /dev/null; then
    echo "기존 Cloud SQL Proxy 프로세스 종료 중..."
    pkill -f "cloud_sql_proxy"
    sleep 2
fi

# Cloud SQL Proxy 실행
echo "Cloud SQL Proxy 시작 중..."
nohup cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5432 > /tmp/cloud_sql_proxy.log 2>&1 &

# 잠시 대기
sleep 3

# 실행 확인
sleep 3

if pgrep -f "cloud_sql_proxy" > /dev/null; then
    echo "✅ Cloud SQL Proxy 실행 중"
    echo "로그 확인: tail -f /tmp/cloud_sql_proxy.log"
    echo "프로세스 확인: ps aux | grep cloud_sql_proxy"
    
    # 로그 확인 (오류 체크)
    if grep -q "ERROR\|error\|Error" /tmp/cloud_sql_proxy.log; then
        echo ""
        echo "⚠️ 로그에 오류가 있습니다. 확인하세요:"
        tail -20 /tmp/cloud_sql_proxy.log
    fi
else
    echo "❌ Cloud SQL Proxy 실행 실패"
    echo ""
    echo "로그 확인:"
    cat /tmp/cloud_sql_proxy.log
    echo ""
    echo "권한 오류인 경우:"
    echo "1. GCP 콘솔 → IAM 및 관리자 → IAM"
    echo "2. VM의 서비스 계정에 'Cloud SQL Client' 역할 추가"
    exit 1
fi

