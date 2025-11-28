# PostgreSQL 덤프 생성 (올바른 옵션 사용)

$env:PGPASSWORD = "maza_970816"

Write-Host "PostgreSQL 덤프 생성 중..."

# --no-owner: 소유자 정보 제외
# --no-acl: 권한 정보 제외  
# --no-privileges: 권한 정보 제외
# --clean: DROP 명령 포함 (하지만 --no-owner와 함께 사용하면 문제 없음)
# --if-exists: DROP IF EXISTS 사용

pg_dump -h localhost -U postgres -d mypoly_lawdata `
    --no-owner `
    --no-acl `
    --no-privileges `
    --clean `
    --if-exists `
    --exclude-table=user_votes `
    --exclude-table=user_political_profile `
    --exclude-table=member_political_profile `
    --exclude-table=bill_similarity `
    -f local_data_final.sql

Write-Host "완료!"
$size = (Get-Item local_data_final.sql).Length / 1MB
Write-Host "파일 크기: $([math]::Round($size, 2)) MB"

