# Cloud SQL Proxy 권한 오류 해결

## 문제
```
"reason": "ACCESS_TOKEN_SCOPE_INSUFFICIENT"
"Reason: insufficientPermissions, Message: Insufficient Permission"
```

## 해결 방법

### 방법 1: VM에 Cloud SQL Client 역할 부여 (권장)

1. **GCP 콘솔에서 VM 인스턴스 페이지로 이동**
   - Compute Engine → VM 인스턴스

2. **VM 인스턴스 클릭**
   - `mypoly-app-server` 클릭

3. **서비스 계정 섹션 확인**
   - "편집" 버튼 클릭
   - 또는 VM 생성 시 설정한 서비스 계정 확인

4. **IAM 및 관리자로 이동**
   - 상단 검색창에 "IAM 및 관리자" 검색
   - 또는 왼쪽 메뉴에서 "IAM 및 관리자" 클릭

5. **서비스 계정에 역할 부여**
   - VM이 사용하는 서비스 계정 찾기 (예: `프로젝트번호-compute@developer.gserviceaccount.com`)
   - "역할" 열에서 "역할 수정" 클릭
   - 다음 역할 추가:
     - **Cloud SQL Client** (`roles/cloudsql.client`)
   - "저장" 클릭

### 방법 2: gcloud 명령어로 역할 부여

VM SSH 창에서:

```bash
# 프로젝트 ID 확인
gcloud config get-value project

# VM의 서비스 계정 확인
gcloud compute instances describe mypoly-app-server --zone=asia-northeast3-a --format="get(serviceAccounts[].email)"

# 서비스 계정에 역할 부여
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="serviceAccount:[SERVICE_ACCOUNT_EMAIL]" \
    --role="roles/cloudsql.client"
```

### 방법 3: 서비스 계정 키 사용 (대안)

권한 부여가 어려운 경우:

1. **서비스 계정 키 생성**
   - GCP 콘솔 → IAM 및 관리자 → 서비스 계정
   - 서비스 계정 선택 → 키 → 키 추가 → JSON

2. **VM에 키 업로드**
   ```bash
   # 로컬에서
   gcloud compute scp service-account-key.json mypoly-app-server:~/
   
   # VM에서
   export GOOGLE_APPLICATION_CREDENTIALS=~/service-account-key.json
   ```

---

## 권한 부여 후 다시 시도

권한을 부여한 후:

```bash
# Cloud SQL Proxy 재시작
pkill -f cloud_sql_proxy
nohup cloud_sql_proxy -instances=fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres=tcp:5432 > /tmp/cloud_sql_proxy.log 2>&1 &

# 확인
sleep 3
ps aux | grep cloud_sql_proxy
tail -f /tmp/cloud_sql_proxy.log
```

---

## 빠른 해결 (GCP 콘솔)

1. **IAM 및 관리자** → **IAM** 메뉴로 이동
2. VM의 서비스 계정 찾기 (이메일 형식)
3. **역할 수정** 클릭
4. **Cloud SQL Client** 역할 추가
5. **저장**

이후 Cloud SQL Proxy를 다시 시작하세요.

