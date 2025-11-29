# PostgreSQL 외부 접속 문제 해결

$env:PGPASSWORD = "maza_970816"

Write-Host "========================================"
Write-Host "PostgreSQL 외부 접속 설정 확인 및 수정"
Write-Host "========================================"

# 1. 데이터 디렉토리 확인
Write-Host "`n[1] 데이터 디렉토리 확인 중..."
$dataDir = psql -h localhost -U postgres -d mypoly_lawdata -t -c "SHOW data_directory;" 2>$null | Where-Object { $_ -match '\S' } | Select-Object -First 1
$dataDir = ($dataDir -replace '/', '\').Trim()

if (-not $dataDir) {
    Write-Host "❌ 데이터 디렉토리를 찾을 수 없습니다."
    exit 1
}

Write-Host "✅ 데이터 디렉토리: $dataDir"

# 2. postgresql.conf 확인 및 수정
Write-Host "`n[2] postgresql.conf 확인 중..."
$confPath = Join-Path $dataDir "postgresql.conf"
$content = Get-Content $confPath -Raw

if ($content -notmatch "listen_addresses\s*=\s*'?\*'?") {
    Write-Host "⚠️ listen_addresses = '*' 설정 필요"
    Copy-Item $confPath "$confPath.backup"
    if ($content -match "listen_addresses\s*=") {
        $content = $content -replace "listen_addresses\s*=\s*[^\r\n]+", "listen_addresses = '*'"
    } else {
        $content = $content + "`nlisten_addresses = '*'`n"
    }
    Set-Content -Path $confPath -Value $content -NoNewline
    Write-Host "✅ listen_addresses = '*' 설정 완료"
} else {
    Write-Host "✅ listen_addresses = '*' 이미 설정됨"
}

# 3. pg_hba.conf 확인 및 수정
Write-Host "`n[3] pg_hba.conf 확인 중..."
$hbaPath = Join-Path $dataDir "pg_hba.conf"
$hbaContent = Get-Content $hbaPath -Raw

if ($hbaContent -notmatch "0\.0\.0\.0/0") {
    Write-Host "⚠️ 외부 접속 허용 설정 필요"
    Copy-Item $hbaPath "$hbaPath.backup"
    Add-Content -Path $hbaPath -Value "`n# 외부 접속 허용`nhost    all             all             0.0.0.0/0               md5`n"
    Write-Host "✅ 외부 접속 허용 설정 완료"
} else {
    Write-Host "✅ 외부 접속 허용 이미 설정됨"
}

# 4. 방화벽 확인 및 설정
Write-Host "`n[4] Windows 방화벽 확인 중..."
$firewallRule = Get-NetFirewallRule | Where-Object { 
    $_.DisplayName -like "*PostgreSQL*" -and 
    $_.Direction -eq "Inbound" -and
    $_.Enabled -eq $true
}

if (-not $firewallRule) {
    Write-Host "⚠️ 방화벽 규칙 없음 - 추가 중..."
    try {
        New-NetFirewallRule -DisplayName "PostgreSQL" -Direction Inbound -LocalPort 5432 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue | Out-Null
        Write-Host "✅ 방화벽 규칙 추가 완료"
    } catch {
        Write-Host "❌ 방화벽 규칙 추가 실패 (관리자 권한 필요)"
    }
} else {
    Write-Host "✅ 방화벽 규칙 존재"
}

# 5. PostgreSQL 서비스 재시작
Write-Host "`n[5] PostgreSQL 서비스 재시작 중..."
$service = Get-Service | Where-Object { $_.Name -like "*postgresql*" } | Select-Object -First 1

if ($service) {
    Write-Host "서비스: $($service.Name)"
    Write-Host "현재 상태: $($service.Status)"
    
    if ($service.Status -ne 'Running') {
        Write-Host "⚠️ 서비스가 실행 중이 아닙니다. 시작 중..."
        Start-Service -Name $service.Name
    } else {
        Write-Host "서비스 재시작 중..."
        try {
            Restart-Service -Name $service.Name -Force -ErrorAction Stop
            Write-Host "✅ 서비스 재시작 완료"
        } catch {
            Write-Host "❌ 서비스 재시작 실패: $_"
            Write-Host "`n💡 관리자 권한으로 PowerShell을 실행하고 다음 명령어를 실행하세요:"
            Write-Host "   Restart-Service -Name $($service.Name)"
        }
    }
} else {
    Write-Host "❌ PostgreSQL 서비스를 찾을 수 없습니다"
}

# 6. 연결 테스트
Write-Host "`n[6] 로컬 연결 테스트 중..."
Start-Sleep -Seconds 2
$testResult = Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue
if ($testResult.TcpTestSucceeded) {
    Write-Host "✅ 로컬 포트 5432 열림"
} else {
    Write-Host "❌ 로컬 포트 5432 닫힘"
}

# 7. 공개 IP 확인
Write-Host "`n[7] 공개 IP 확인 중..."
$publicIP = (Invoke-WebRequest -Uri 'https://api.ipify.org' -UseBasicParsing).Content
Write-Host "공개 IP: $publicIP"

Write-Host "`n========================================"
Write-Host "완료!"
Write-Host "========================================"
Write-Host "`n⚠️ 중요:"
Write-Host "1. 공유기/라우터에서 포트 포워딩이 필요할 수 있습니다"
Write-Host "2. 공유기 관리 페이지에서 포트 5432를 이 PC의 내부 IP로 포워딩하세요"
Write-Host "3. 내부 IP 확인: ipconfig"
Write-Host "`nVM에서 다시 시도:"
Write-Host "export LOCAL_DB_IP='$publicIP'"
Write-Host "python scripts/gcp/migrate_direct_python.py"

