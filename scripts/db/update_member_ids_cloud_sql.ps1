# PowerShell 스크립트: 표결정보에서 의원 ID 업데이트 (Cloud SQL 직접 연결)
# 로컬 PC에서 Cloud SQL 공개 IP로 직접 연결하여 업데이트

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "표결정보에서 의원 식별자 매핑 업데이트 (Cloud SQL 직접 연결)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Cloud SQL 연결 정보
$CLOUD_DB_HOST = "34.50.48.31"  # Cloud SQL 공개 IP
$CLOUD_DB_NAME = "mypoly_lawdata"
$CLOUD_DB_USER = "postgres"
$CLOUD_DB_PASSWORD = "Mypoly!2025"
$CLOUD_DB_PORT = 5432

# 환경 변수 설정
$env:DB_HOST = $CLOUD_DB_HOST
$env:DB_NAME = $CLOUD_DB_NAME
$env:DB_USER = $CLOUD_DB_USER
$env:DB_PASSWORD = $CLOUD_DB_PASSWORD
$env:DB_PORT = $CLOUD_DB_PORT

Write-Host "Cloud SQL 연결 정보:" -ForegroundColor Yellow
Write-Host "  Host: $CLOUD_DB_HOST" -ForegroundColor Gray
Write-Host "  Database: $CLOUD_DB_NAME" -ForegroundColor Gray
Write-Host "  User: $CLOUD_DB_USER" -ForegroundColor Gray
Write-Host "  Port: $CLOUD_DB_PORT" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  사전 준비:" -ForegroundColor Yellow
Write-Host "  1. GCP 콘솔 → Cloud SQL → 인스턴스 → 연결" -ForegroundColor Gray
Write-Host "  2. '승인된 네트워크'에 로컬 PC의 공개 IP 추가" -ForegroundColor Gray
Write-Host ""

# Python 스크립트 경로
$scriptPath = Join-Path $PSScriptRoot "update_member_ids_from_votes.py"

if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ 오류: 스크립트 파일을 찾을 수 없습니다: $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "Python 스크립트 실행 중..." -ForegroundColor Yellow
Write-Host ""

# Python 스크립트 실행
python $scriptPath

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "✅ 업데이트 완료!" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Red
    Write-Host "❌ 업데이트 실패!" -ForegroundColor Red
    Write-Host "================================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "확인 사항:" -ForegroundColor Yellow
    Write-Host "  1. GCP 방화벽 규칙에 로컬 PC IP가 추가되었는지 확인" -ForegroundColor Gray
    Write-Host "  2. Cloud SQL 인스턴스가 실행 중인지 확인" -ForegroundColor Gray
    Write-Host "  3. 연결 정보(IP, 비밀번호)가 올바른지 확인" -ForegroundColor Gray
    exit 1
}

