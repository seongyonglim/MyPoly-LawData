#!/bin/bash
# Cloud SQL 완전 설정 스크립트 (테이블 생성 + 데이터 마이그레이션)

set -e

echo "=========================================="
echo "Cloud SQL 완전 설정"
echo "=========================================="

cd ~/MyPoly-LawData

# 1. 테이블 생성
echo "[1/2] 테이블 생성 중..."
chmod +x scripts/gcp/create_tables_in_cloud_sql.sh
./scripts/gcp/create_tables_in_cloud_sql.sh

# 2. 데이터 마이그레이션 안내
echo ""
echo "[2/2] 데이터 마이그레이션"
echo "로컬 데이터를 Cloud SQL로 마이그레이션하려면:"
echo "로컬 PC에서 다음 스크립트 실행:"
echo "  python scripts/gcp/migrate_direct_public_ip.py"
echo ""
echo "자세한 내용은 docs/gcp_migration_summary.md 참고"

echo ""
echo "=========================================="
echo "설정 완료!"
echo "=========================================="

