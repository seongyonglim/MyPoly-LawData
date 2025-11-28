# GCP 콘솔에서 Cloud SQL 권한 부여 (단계별)

## 문제
VM의 서비스 계정에 Cloud SQL 연결 권한이 없습니다.

## 해결 방법 (GCP 콘솔)

### 1단계: IAM 및 관리자 페이지로 이동

1. **GCP 콘솔 상단 검색창**에 "IAM 및 관리자" 검색
2. **"IAM 및 관리자"** 클릭
3. 왼쪽 메뉴에서 **"IAM"** 클릭

---

### 2단계: 서비스 계정 찾기

1. **필터** 입력창에 다음 중 하나 입력:
   - `929081401130-compute@developer.gserviceaccount.com`
   - 또는 `compute@developer` 검색

2. 서비스 계정 목록에서 찾기:
   - 형식: `프로젝트번호-compute@developer.gserviceaccount.com`
   - 예: `929081401130-compute@developer.gserviceaccount.com`

---

### 3단계: 역할 추가

1. 찾은 서비스 계정의 **"역할"** 열에서 **연필 아이콘(편집)** 클릭
2. **"역할 추가"** 클릭
3. 검색창에 **"Cloud SQL Client"** 입력
4. **"Cloud SQL Client"** 선택
5. **"저장"** 클릭

---

### 4단계: 확인

역할이 추가되면:
- 서비스 계정의 역할 목록에 **"Cloud SQL Client"** 표시됨

---

## 대안: VM 접근 범위 변경

만약 위 방법이 작동하지 않으면:

1. **Compute Engine** → **VM 인스턴스**
2. `mypoly-app-server` 클릭
3. **"편집"** 버튼 클릭
4. **"액세스 범위"** 섹션 찾기
5. **"모든 Cloud API에 대한 전체 액세스 허용"** 선택
6. **"저장"** 클릭
7. VM 재시작 (선택사항)

---

## 권한 부여 후 테스트

VM SSH 창에서:

```bash
# Cloud SQL Proxy 재시작
pkill -f cloud_sql_proxy
nohup cloud_sql_proxy -instances=fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres=tcp:5432 > /tmp/cloud_sql_proxy.log 2>&1 &

# 확인
sleep 5
tail -20 /tmp/cloud_sql_proxy.log
```

성공하면 로그에 오류가 없고 연결이 성공합니다.

