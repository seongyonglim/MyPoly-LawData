#!/bin/bash
# VM에서 실행하는 의원 ID 업데이트 스크립트
# Cloud SQL Proxy를 통해 연결

set -e

echo "================================================================================"
echo "표결정보에서 의원 식별자 매핑 업데이트 (VM)"
echo "================================================================================"
echo ""

# 프로젝트 디렉토리로 이동
cd ~/MyPoly-LawData || exit 1

# 가상환경 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ 오류: venv 디렉토리를 찾을 수 없습니다."
    exit 1
fi

# .env 파일이 있으면 로드
if [ -f ".env" ]; then
    echo "📄 .env 파일에서 환경 변수 로드 중..."
    set -a
    source .env
    set +a
    echo "✅ 환경 변수 로드 완료"
else
    echo "⚠️  경고: .env 파일이 없습니다. 기본값을 사용합니다."
    echo ""
    echo "Cloud SQL Proxy를 통해 연결하려면 .env 파일을 생성하세요:"
    echo "  DB_HOST=127.0.0.1"
    echo "  DB_NAME=mypoly_lawdata"
    echo "  DB_USER=postgres"
    echo "  DB_PASSWORD='Mypoly!2025'"
    echo "  DB_PORT=5432"
    echo ""
    
    # 환경 변수 설정 (비밀번호는 작은따옴표로 감싸서 특수문자 처리)
    export DB_HOST=127.0.0.1
    export DB_NAME=mypoly_lawdata
    export DB_USER=postgres
    export DB_PASSWORD='Mypoly!2025'
    export DB_PORT=5432
fi

echo ""
echo "연결 정보:"
echo "  Host: ${DB_HOST:-localhost}"
echo "  Database: ${DB_NAME:-mypoly_lawdata}"
echo "  User: ${DB_USER:-postgres}"
echo "  Port: ${DB_PORT:-5432}"
echo ""

# Cloud SQL Proxy 실행 확인
if ! pgrep -f cloud_sql_proxy > /dev/null; then
    echo "⚠️  경고: Cloud SQL Proxy가 실행 중이지 않습니다."
    echo "Cloud SQL Proxy를 시작하세요:"
    echo "  cloud_sql_proxy -instances=CONNECTION_NAME=tcp:5432 &"
    echo ""
fi

# Python 스크립트 실행
echo "Python 스크립트 실행 중..."
echo ""

python scripts/db/update_member_ids_from_votes.py

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================================================"
    echo "✅ 업데이트 완료!"
    echo "================================================================================"
else
    echo ""
    echo "================================================================================"
    echo "❌ 업데이트 실패!"
    echo "================================================================================"
    exit 1
fi

