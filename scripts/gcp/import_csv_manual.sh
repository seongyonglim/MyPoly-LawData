#!/bin/bash
# CSV 파일을 수동으로 가져오기 (인코딩 문제 해결)

set -e

cd ~/MyPoly-LawData

export PGPASSWORD="Mypoly!2025"
DB_HOST="127.0.0.1"
DB_USER="postgres"
DB_NAME="mypoly_lawdata"

echo "=========================================="
echo "CSV 파일 수동 가져오기"
echo "=========================================="

# proc_stage_mapping (작은 테이블 먼저 테스트)
echo ""
echo "[proc_stage_mapping] 가져오기 중..."
echo "파일 내용 확인:"
head -3 proc_stage_mapping.csv

# 인코딩 변환 시도
iconv -f UTF-8 -t UTF-8 proc_stage_mapping.csv > proc_stage_mapping_utf8.csv 2>/dev/null || \
sed 's/\r$//' proc_stage_mapping.csv > proc_stage_mapping_utf8.csv

# BOM 제거
sed -i '1s/^\xEF\xBB\xBF//' proc_stage_mapping_utf8.csv 2>/dev/null || true

# 가져오기
psql -h $DB_HOST -U $DB_USER -d $DB_NAME << EOF
TRUNCATE TABLE proc_stage_mapping CASCADE;
\COPY proc_stage_mapping FROM 'proc_stage_mapping_utf8.csv' WITH CSV HEADER;
SELECT COUNT(*) as count FROM proc_stage_mapping;
EOF

echo ""
echo "[assembly_members] 가져오기 중..."
sed 's/\r$//' assembly_members.csv > assembly_members_utf8.csv
sed -i '1s/^\xEF\xBB\xBF//' assembly_members_utf8.csv 2>/dev/null || true
psql -h $DB_HOST -U $DB_USER -d $DB_NAME << EOF
TRUNCATE TABLE assembly_members CASCADE;
\COPY assembly_members FROM 'assembly_members_utf8.csv' WITH CSV HEADER;
SELECT COUNT(*) as count FROM assembly_members;
EOF

echo ""
echo "[bills] 가져오기 중..."
sed 's/\r$//' bills.csv > bills_utf8.csv
sed -i '1s/^\xEF\xBB\xBF//' bills_utf8.csv 2>/dev/null || true
psql -h $DB_HOST -U $DB_USER -d $DB_NAME << EOF
TRUNCATE TABLE bills CASCADE;
\COPY bills FROM 'bills_utf8.csv' WITH CSV HEADER;
SELECT COUNT(*) as count FROM bills;
EOF

echo ""
echo "[votes] 가져오기 중... (시간이 걸릴 수 있음)"
sed 's/\r$//' votes.csv > votes_utf8.csv
sed -i '1s/^\xEF\xBB\xBF//' votes_utf8.csv 2>/dev/null || true
psql -h $DB_HOST -U $DB_USER -d $DB_NAME << EOF
TRUNCATE TABLE votes CASCADE;
\COPY votes FROM 'votes_utf8.csv' WITH CSV HEADER;
SELECT COUNT(*) as count FROM votes;
EOF

echo ""
echo "=========================================="
echo "모든 데이터 가져오기 완료!"
echo "=========================================="

