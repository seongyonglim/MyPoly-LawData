# 최종 데이터 마이그레이션 가이드 (가장 확실한 방법)

## 문제
- CSV 파일 컬럼 순서 불일치
- 인코딩 문제
- 데이터 타입 불일치

## 해결: SSH 터널링 + Python 직접 연결

로컬에서 Python으로 데이터를 읽어서, VM의 Cloud SQL Proxy를 통해 직접 삽입합니다.

---

## 단계별 가이드

### 1단계: SSH 터널링 설정

**새 PowerShell 창을 열고** (기존 SSH 연결과 별도로):

```powershell
ssh -L 5433:127.0.0.1:5432 seongyonglim3@34.64.212.103
```

**이 창은 계속 열어두세요!** (터널이 유지되어야 함)

---

### 2단계: 로컬에서 마이그레이션 실행

**다른 PowerShell 창에서**:

```powershell
cd C:\polywave\MyPoly-LawData
python scripts/gcp/migrate_via_ssh_tunnel.py
```

---

## 간단 설명

1. **첫 번째 창**: SSH 터널 (로컬 5433 포트 → VM의 Cloud SQL Proxy)
2. **두 번째 창**: Python 스크립트 실행 (로컬 DB → 로컬 5433 포트 → Cloud SQL)

---

## 실행 순서

1. PowerShell 창 1: `ssh -L 5433:127.0.0.1:5432 seongyonglim3@34.64.212.103` 실행
2. PowerShell 창 2: `cd C:\polywave\MyPoly-LawData && python scripts/gcp/migrate_via_ssh_tunnel.py` 실행

---

## 완료 확인

스크립트가 완료되면:
- 각 테이블의 삽입 건수 표시
- 브라우저에서 `http://34.64.212.103:5000` 접속하여 데이터 확인

