#!/bin/bash
# VM에서 실행: 데이터 수집 프로세스 확인 및 중지

echo "=========================================="
echo "VM 데이터 수집 프로세스 확인 및 중지"
echo "=========================================="

echo ""
echo "[1] 실행 중인 데이터 수집 프로세스 확인..."
ps aux | grep -E "collect_votes|collect_bills" | grep -v grep

echo ""
echo "[2] 프로세스 중지 중..."
pkill -f collect_votes_from_date.py
pkill -f collect_bills_from_date.py

sleep 2

echo ""
echo "[3] 재확인..."
ps aux | grep -E "collect_votes|collect_bills" | grep -v grep

if [ $? -eq 1 ]; then
    echo "✅ 모든 데이터 수집 프로세스가 중지되었습니다."
else
    echo "⚠️ 일부 프로세스가 여전히 실행 중일 수 있습니다."
fi

echo ""
echo "=========================================="
echo "완료"
echo "=========================================="

