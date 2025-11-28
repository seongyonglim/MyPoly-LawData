#!/bin/bash
# Cloud SQL에 테이블 생성 스크립트

set -e

echo "=========================================="
echo "Cloud SQL 테이블 생성"
echo "=========================================="

cd ~/MyPoly-LawData

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "❌ .env 파일이 없습니다."
    exit 1
fi

# 환경 변수 로드
export $(cat .env | xargs)

# SQL 파일 경로
SQL_FILE="scripts/db/create_tables_postgresql.sql"

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ SQL 파일을 찾을 수 없습니다: $SQL_FILE"
    exit 1
fi

echo "SQL 파일: $SQL_FILE"
echo "데이터베이스: $DB_NAME"
echo ""

# PostgreSQL 클라이언트로 SQL 실행
echo "테이블 생성 중..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f $SQL_FILE

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 테이블 생성 완료!"
else
    echo ""
    echo "❌ 테이블 생성 실패"
    exit 1
fi

