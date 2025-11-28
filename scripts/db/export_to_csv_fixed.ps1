# CSV 내보내기 (컬럼 명시)

$env:PGPASSWORD = "maza_970816"

Write-Host "CSV 파일 생성 중..."

# proc_stage_mapping
Write-Host "proc_stage_mapping.csv 생성 중..."
$output = psql -h localhost -U postgres -d mypoly_lawdata -c "COPY (SELECT stage_code, stage_name, stage_order, description FROM proc_stage_mapping ORDER BY stage_order) TO STDOUT WITH CSV HEADER"
$output | Out-File -Encoding UTF8 proc_stage_mapping_fixed.csv

# assembly_members
Write-Host "assembly_members.csv 생성 중..."
$output = psql -h localhost -U postgres -d mypoly_lawdata -c "COPY (SELECT * FROM assembly_members) TO STDOUT WITH CSV HEADER"
$output | Out-File -Encoding UTF8 assembly_members_fixed.csv

# bills
Write-Host "bills.csv 생성 중..."
$output = psql -h localhost -U postgres -d mypoly_lawdata -c "COPY (SELECT * FROM bills) TO STDOUT WITH CSV HEADER"
$output | Out-File -Encoding UTF8 bills_fixed.csv

# votes
Write-Host "votes.csv 생성 중..."
$output = psql -h localhost -U postgres -d mypoly_lawdata -c "COPY (SELECT * FROM votes) TO STDOUT WITH CSV HEADER"
$output | Out-File -Encoding UTF8 votes_fixed.csv

Write-Host "완료!"
Get-ChildItem *_fixed.csv | Format-Table Name, @{Name="Size(MB)";Expression={[math]::Round($_.Length/1MB, 2)}}

