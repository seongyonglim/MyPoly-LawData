# GCP Cloud SQL 방화벽 규칙 추가 (가장 간단한 방법)

## 문제
- SSH 터널링은 키 인증 설정이 복잡함
- 공유기 포트 포워딩도 복잡함

## 해결책: GCP 콘솔에서 방화벽 규칙 추가

Cloud SQL의 공개 IP를 직접 사용하고, GCP 콘솔에서 로컬 PC의 공개 IP를 승인된 네트워크에 추가합니다.

---

## 1단계: GCP 콘솔에서 방화벽 규칙 추가

### 1-1. Cloud SQL 인스턴스 페이지 접속

1. **GCP 콘솔** → **Cloud SQL** → 인스턴스 `mypoly-postgres` 클릭
2. **"연결"** 탭 클릭

### 1-2. 승인된 네트워크 추가

1. **"승인된 네트워크"** 섹션 찾기
2. **"네트워크 추가"** 클릭
3. 다음 정보 입력:
   - **이름**: `로컬PC`
   - **네트워크**: `61.74.128.66/32` (로컬 PC의 공개 IP)
4. **"저장"** 클릭

---

## 2단계: 로컬 PC에서 마이그레이션 실행

**PowerShell:**
```powershell
cd C:\polywave\MyPoly-LawData
git pull origin main
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install psycopg2-binary
python scripts/gcp/migrate_direct_public_ip.py
```

---

## 이 방법의 장점

1. ✅ **SSH 키 설정 불필요**
2. ✅ **공유기 설정 불필요**
3. ✅ **GCP 콘솔에서 클릭 몇 번으로 완료**
4. ✅ **가장 간단하고 확실함**

---

## Cloud SQL 공개 IP 확인

GCP 콘솔 → Cloud SQL → 인스턴스 → 연결 탭에서:
- **공개 IP 주소**: `34.50.48.31` (예시, 실제 IP 확인 필요)

스크립트의 `CLOUD_DB['host']`를 실제 공개 IP로 수정하세요.

