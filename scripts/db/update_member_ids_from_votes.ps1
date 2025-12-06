# PowerShell 스크립트: 표결정보에서 의원 ID 업데이트
# Cloud SQL에 직접 연결하여 업데이트 실행

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "표결정보에서 의원 식별자 매핑 업데이트 (Cloud SQL)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Cloud SQL 연결 정보
$CLOUD_DB_HOST = "34.50.48.31"  # Cloud SQL 공개 IP
$CLOUD_DB_NAME = "mypoly_lawdata"
$CLOUD_DB_USER = "postgres"
$CLOUD_DB_PASSWORD = "Mypoly!2025"
$CLOUD_DB_PORT = 5432

# Python 스크립트 실행
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

# Python 스크립트 실행
$scriptPath = Join-Path $PSScriptRoot "update_member_ids_from_votes.py"
Write-Host "Python 스크립트 실행 중..." -ForegroundColor Yellow
Write-Host ""

python $scriptPath

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "업데이트 완료!" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Red
    Write-Host "업데이트 실패!" -ForegroundColor Red
    Write-Host "================================================================================" -ForegroundColor Red
    exit 1
}

