#!/bin/bash
# VM에서 캐시 클리어 및 앱 재시작

cd ~/MyPoly-LawData

echo "============================================================"
echo "캐시 클리어 및 앱 재시작"
echo "============================================================"

# 1. 실행 중인 앱 프로세스 종료
echo "[1] 실행 중인 앱 프로세스 종료 중..."
pkill -f "python.*app.py"
sleep 3

# 2. 포트 5000을 사용하는 프로세스 확인 및 종료
echo "[2] 포트 5000 사용 프로세스 확인 중..."
PORT_PID=$(lsof -ti:5000 2>/dev/null || fuser 5000/tcp 2>/dev/null | awk '{print $1}')

if [ ! -z "$PORT_PID" ]; then
    echo "  포트 5000을 사용하는 프로세스 발견: PID $PORT_PID"
    kill -9 $PORT_PID 2>/dev/null
    sleep 2
    echo "  프로세스 종료 완료"
else
    echo "  포트 5000을 사용하는 프로세스 없음"
fi

# 3. 다시 한 번 확인
REMAINING=$(pgrep -f "python.*app.py" | wc -l)
if [ "$REMAINING" -gt 0 ]; then
    echo "  남은 프로세스 강제 종료 중..."
    pkill -9 -f "python.*app.py"
    sleep 2
fi

# 4. Flask 캐시 디렉토리 삭제 (있는 경우)
echo "[3] Flask 캐시 클리어 중..."
if [ -d "flask_cache" ]; then
    rm -rf flask_cache
    echo "  flask_cache 디렉토리 삭제 완료"
fi

# 5. Python 캐시 파일 삭제
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
echo "  Python 캐시 파일 삭제 완료"

# 6. 앱 시작
echo "[4] 앱 시작 중..."
nohup python3 app.py > app.log 2>&1 &
sleep 3

# 7. 프로세스 확인
if pgrep -f "python.*app.py" > /dev/null; then
    echo "✅ 앱이 성공적으로 시작되었습니다!"
    echo "  PID: $(pgrep -f 'python.*app.py')"
    echo "  로그: tail -f ~/MyPoly-LawData/app.log"
    echo ""
    echo "⚠️ 브라우저에서 Ctrl+Shift+R (또는 Cmd+Shift+R)로 강력 새로고침하세요!"
else
    echo "❌ 앱 시작 실패. 로그를 확인하세요:"
    echo "  tail -f ~/MyPoly-LawData/app.log"
fi

echo "============================================================"

