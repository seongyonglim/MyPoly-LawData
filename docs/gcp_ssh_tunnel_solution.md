# SSH 터널링을 통한 데이터 마이그레이션 (포트 포워딩 불필요)

## 문제
- 공유기/라우터에서 포트 포워딩 설정이 복잡함
- 외부에서 직접 접속이 불가능할 수 있음

## 해결책: SSH 터널링

VM에서 로컬 PC로 SSH 터널을 만들고, 그 터널을 통해 PostgreSQL에 접속합니다.

---

## 1단계: 로컬 PC에서 SSH 서버 설정 (Windows)

### Windows 10/11에 OpenSSH 서버 설치

**PowerShell (관리자 권한):**
```powershell
# OpenSSH 서버 설치
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# 서비스 시작
Start-Service sshd

# 자동 시작 설정
Set-Service -Name sshd -StartupType 'Automatic'

# 방화벽 규칙 추가
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
```

---

## 2단계: VM에서 SSH 터널 생성

**VM SSH 창에서:**

```bash
# SSH 터널 생성 (백그라운드)
# 로컬 PC의 공개 IP와 사용자명 필요
ssh -N -L 5433:localhost:5432 [로컬PC사용자명]@61.74.128.66

# 예시:
# ssh -N -L 5433:localhost:5432 Hello@61.74.128.66
```

**터널이 생성되면 이 창은 계속 열어두세요.**

---

## 3단계: 마이그레이션 스크립트 수정

VM에서 **새 터미널 창**을 열고:

```bash
cd ~/MyPoly-LawData
source venv/bin/activate

# 스크립트 수정 (SSH 터널 사용)
# LOCAL_DB를 127.0.0.1:5433으로 변경
```

또는 스크립트를 수정하여 SSH 터널 포트를 사용하도록 합니다.

---

## 더 간단한 방법: 로컬 PC에서 직접 실행

SSH 터널링이 복잡하다면, **로컬 PC에서 직접 Cloud SQL에 연결**하는 방법을 사용하세요.

