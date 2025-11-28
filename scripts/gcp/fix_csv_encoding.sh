#!/bin/bash
# CSV 파일 인코딩을 UTF-8로 변환

set -e

echo "=========================================="
echo "CSV 파일 인코딩 변환 (UTF-8)"
echo "=========================================="

cd ~/MyPoly-LawData

# CSV 파일 목록
CSV_FILES=(
    "proc_stage_mapping.csv"
    "assembly_members.csv"
    "bills.csv"
    "votes.csv"
)

for csv_file in "${CSV_FILES[@]}"; do
    if [ ! -f "$csv_file" ]; then
        echo "⚠️ 파일 없음: $csv_file"
        continue
    fi
    
    echo ""
    echo "[$csv_file] 변환 중..."
    
    # 백업
    cp "$csv_file" "${csv_file}.bak"
    
    # UTF-8로 변환 (BOM 제거, Windows 줄바꿈 처리)
    iconv -f UTF-16LE -t UTF-8 "$csv_file" > "${csv_file}.tmp" 2>/dev/null || \
    iconv -f UTF-16BE -t UTF-8 "$csv_file" > "${csv_file}.tmp" 2>/dev/null || \
    iconv -f CP949 -t UTF-8 "$csv_file" > "${csv_file}.tmp" 2>/dev/null || \
    sed 's/\r$//' "$csv_file" > "${csv_file}.tmp"
    
    # BOM 제거
    sed -i '1s/^\xEF\xBB\xBF//' "${csv_file}.tmp" 2>/dev/null || \
    sed -i '1s/^\xFF\xFE//' "${csv_file}.tmp" 2>/dev/null || true
    
    # Windows 줄바꿈 제거
    dos2unix "${csv_file}.tmp" 2>/dev/null || \
    sed -i 's/\r$//' "${csv_file}.tmp"
    
    mv "${csv_file}.tmp" "$csv_file"
    
    echo "  ✅ 변환 완료"
done

echo ""
echo "=========================================="
echo "인코딩 변환 완료!"
echo "=========================================="

