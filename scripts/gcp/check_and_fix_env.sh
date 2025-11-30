#!/bin/bash
# VM 환경 변수 확인 및 수정 스크립트

set -e

echo "================================================================================"
echo "VM 환경 변수 확인 및 수정"
echo "================================================================================"
echo ""

cd ~/MyPoly-LawData || exit 1

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. 생성합니다..."
    cat > .env << 'EOF'
DB_HOST=127.0.0.1
DB_NAME=mypoly_lawdata
DB_USER=postgres
DB_PASSWORD=Mypoly!2025
DB_PORT=5432
EOF
    chmod 600 .env
    echo "✅ .env 파일 생성 완료"
else
    echo "✅ .env 파일이 존재합니다."
    echo ""
    echo "현재 .env 파일 내용:"
    echo "----------------------------------------"
    cat .env
    echo "----------------------------------------"
    echo ""
    read -p ".env 파일을 수정하시겠습니까? (y/n): " answer
    if [ "$answer" = "y" ]; then
        echo ""
        echo "Cloud SQL 비밀번호를 입력하세요:"
        read -s DB_PASSWORD
        
        if [ -z "$DB_PASSWORD" ]; then
            echo "❌ 비밀번호가 필요합니다."
            exit 1
        fi
        
        cat > .env << EOF
DB_HOST=127.0.0.1
DB_NAME=mypoly_lawdata
DB_USER=postgres
DB_PASSWORD=$DB_PASSWORD
DB_PORT=5432
EOF
        chmod 600 .env
        echo "✅ .env 파일 업데이트 완료"
    fi
fi

echo ""
echo "================================================================================"
echo "Cloud SQL Proxy 상태 확인"
echo "================================================================================"
echo ""

if pgrep -f cloud_sql_proxy > /dev/null; then
    echo "✅ Cloud SQL Proxy가 실행 중입니다."
    ps aux | grep cloud_sql_proxy | grep -v grep
else
    echo "❌ Cloud SQL Proxy가 실행 중이지 않습니다."
    echo ""
    echo "Cloud SQL Proxy를 시작하려면:"
    echo "  export CLOUD_SQL_CONNECTION_NAME='fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres'"
    echo "  nohup cloud_sql_proxy -instances=\$CLOUD_SQL_CONNECTION_NAME=tcp:5432 > /tmp/cloud_sql_proxy.log 2>&1 &"
    echo ""
    echo "또는 systemd 서비스 사용:"
    echo "  sudo systemctl start cloud-sql-proxy"
    echo "  sudo systemctl status cloud-sql-proxy"
fi

echo ""
echo "================================================================================"
echo "Flask 앱 상태 확인"
echo "================================================================================"
echo ""

if pgrep -f "python.*app.py" > /dev/null; then
    echo "⚠️  Flask 앱이 이미 실행 중입니다."
    ps aux | grep "python.*app.py" | grep -v grep
    echo ""
    read -p "Flask 앱을 재시작하시겠습니까? (y/n): " restart
    if [ "$restart" = "y" ]; then
        echo "기존 프로세스 종료 중..."
        pkill -f "python.*app.py"
        sleep 2
        
        echo "환경 변수 로드 후 Flask 앱 시작 중..."
        source venv/bin/activate
        export $(cat .env | xargs)
        nohup python app.py > /tmp/flask_app.log 2>&1 &
        sleep 2
        
        if pgrep -f "python.*app.py" > /dev/null; then
            echo "✅ Flask 앱이 시작되었습니다."
        else
            echo "❌ Flask 앱 시작 실패. 로그 확인: tail -f /tmp/flask_app.log"
        fi
    fi
else
    echo "Flask 앱이 실행 중이지 않습니다."
    echo ""
    read -p "Flask 앱을 시작하시겠습니까? (y/n): " start
    if [ "$start" = "y" ]; then
        source venv/bin/activate
        export $(cat .env | xargs)
        nohup python app.py > /tmp/flask_app.log 2>&1 &
        sleep 2
        
        if pgrep -f "python.*app.py" > /dev/null; then
            echo "✅ Flask 앱이 시작되었습니다."
        else
            echo "❌ Flask 앱 시작 실패. 로그 확인: tail -f /tmp/flask_app.log"
        fi
    fi
fi

echo ""
echo "================================================================================"
echo "systemd 서비스 상태 확인"
echo "================================================================================"
echo ""

if systemctl list-units --type=service | grep -q "mypoly-app.service"; then
    echo "systemd 서비스가 설정되어 있습니다."
    echo ""
    echo "서비스 상태:"
    sudo systemctl status mypoly-app.service --no-pager -l || true
    echo ""
    read -p "systemd 서비스를 재시작하시겠습니까? (y/n): " restart_service
    if [ "$restart_service" = "y" ]; then
        echo ""
        echo "⚠️  systemd 서비스를 재시작하면 .env 파일이 다시 로드됩니다."
        echo "서비스 파일을 업데이트하려면 create_systemd_services.sh를 다시 실행하세요."
        echo ""
        sudo systemctl restart mypoly-app.service
        sleep 2
        sudo systemctl status mypoly-app.service --no-pager -l || true
    fi
else
    echo "systemd 서비스가 설정되어 있지 않습니다."
    echo "서비스를 생성하려면:"
    echo "  export CLOUD_SQL_CONNECTION_NAME='fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres'"
    echo "  ./scripts/gcp/create_systemd_services.sh"
fi

echo ""
echo "================================================================================"
echo "완료"
echo "================================================================================"
echo ""
echo "다음 명령어로 로그를 확인할 수 있습니다:"
echo "  tail -f /tmp/flask_app.log"
echo "  sudo journalctl -u mypoly-app -f"
echo "  sudo journalctl -u cloud-sql-proxy -f"

