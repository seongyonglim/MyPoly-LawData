#!/bin/bash
# CSV 파일을 Cloud SQL로 가져오기

set -e

echo "=========================================="
echo "CSV 파일을 Cloud SQL로 가져오기"
echo "=========================================="

cd ~/MyPoly-LawData

# 환경 변수 설정
export PGPASSWORD="Mypoly!2025"
DB_HOST="127.0.0.1"
DB_USER="postgres"
DB_NAME="mypoly_lawdata"

# CSV 파일 목록
CSV_FILES=(
    "proc_stage_mapping.csv"
    "assembly_members.csv"
    "bills.csv"
    "votes.csv"
)

for csv_file in "${CSV_FILES[@]}"; do
    if [ ! -f "$csv_file" ]; then
        echo "⚠️ 파일 없음: $csv_file (건너뜀)"
        continue
    fi
    
    # 테이블 이름 추출 (파일명에서 .csv 제거)
    table_name=$(basename "$csv_file" .csv)
    
    echo ""
    echo "[$table_name] 가져오기 중..."
    
    # 파일 크기 확인
    file_size=$(du -h "$csv_file" | cut -f1)
    echo "  파일 크기: $file_size"
    
    # 기존 데이터 삭제 (선택사항)
    echo "  기존 데이터 삭제 중..."
    psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "TRUNCATE TABLE $table_name CASCADE" 2>/dev/null || echo "  (테이블이 없거나 이미 비어있음)"
    
    # CSV 가져오기
    echo "  데이터 가져오기 중..."
    psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\COPY $table_name FROM '$csv_file' WITH CSV HEADER"
    
    if [ $? -eq 0 ]; then
        # 레코드 수 확인
        count=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM $table_name")
        echo "  ✅ 완료: $count 건"
    else
        echo "  ❌ 실패"
    fi
done

echo ""
echo "=========================================="
echo "모든 CSV 파일 가져오기 완료!"
echo "=========================================="

