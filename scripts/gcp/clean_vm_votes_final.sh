#!/bin/bash
# VM에서 실행: votes 테이블 최종 정리

echo "=========================================="
echo "VM votes 테이블 최종 정리"
echo "=========================================="

cd ~/MyPoly-LawData

echo ""
echo "[1] 중복 제거 중..."
python3 scripts/gcp/fix_vm_votes_unique_vm.py

echo ""
echo "[2] localhost에 없는 데이터 삭제 중..."
python3 scripts/gcp/remove_vm_votes_duplicates_vm.py

echo ""
echo "[3] 최종 확인..."
python3 scripts/gcp/check_vm_db_structure.py

echo ""
echo "=========================================="
echo "완료"
echo "=========================================="

