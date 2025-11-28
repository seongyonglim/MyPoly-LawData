# SSH 터널링을 통한 데이터 마이그레이션 (가장 확실한 방법)

## 문제
- CSV 파일 인코딩 문제
- 컬럼 순서 불일치
- 데이터 타입 불일치

## 해결: SSH 터널링 + Python 직접 연결

로컬에서 직접 Python으로 데이터를 읽어서, VM의 Cloud SQL Proxy를 통해 삽입합니다.

---

## 단계별 가이드

### 1단계: SSH 터널링 설정

**새 PowerShell 창에서** (기존 SSH 연결과 별도):

```powershell
# VM 공개 IP: 34.64.212.103
ssh -L 5433:127.0.0.1:5432 seongyonglim3@34.64.212.103
```

이 명령어는:
- 로컬 포트 5433을 VM의 127.0.0.1:5432 (Cloud SQL Proxy)로 연결
- 이 창은 계속 열어두어야 함

---

### 2단계: 로컬에서 마이그레이션 실행

**다른 PowerShell 창에서**:

```powershell
cd C:\polywave\MyPoly-LawData
python scripts/gcp/migrate_via_ssh_tunnel.py
```

---

## 장점

- ✅ CSV 인코딩 문제 없음
- ✅ 컬럼 순서 자동 처리
- ✅ 데이터 타입 자동 변환
- ✅ 외래키 순서 자동 처리
- ✅ 빠르고 안정적

---

## 빠른 시작

1. **새 PowerShell 창**: `ssh -L 5433:127.0.0.1:5432 seongyonglim3@34.64.212.103`
2. **다른 PowerShell 창**: `cd C:\polywave\MyPoly-LawData && python scripts/gcp/migrate_via_ssh_tunnel.py`

---

## 문제 해결

### SSH 연결 실패
- VM의 공개 IP 확인
- SSH 키 설정 확인

### 포트 5433 이미 사용 중
- 다른 포트 사용: `ssh -L 5434:127.0.0.1:5432 ...`
- 스크립트의 `CLOUD_DB['port']`도 변경

