# Cloud SQL Admin API 활성화 가이드

## 문제
```
"reason": "SERVICE_DISABLED"
"Cloud SQL Admin API has not been used in project 929081401130 before or it is disabled."
```

## 해결 방법

### 방법 1: 직접 링크로 활성화 (가장 빠름)

다음 링크를 클릭하여 API를 활성화하세요:

**https://console.developers.google.com/apis/api/sqladmin.googleapis.com/overview?project=929081401130**

1. 링크 클릭
2. **"사용 설정"** 버튼 클릭
3. 활성화 완료까지 1-2분 대기

---

### 방법 2: GCP 콘솔에서 활성화

1. **GCP 콘솔 상단 검색창**에 "API 및 서비스" 검색
2. **"API 및 서비스"** → **"라이브러리"** 클릭
3. 검색창에 **"Cloud SQL Admin API"** 입력
4. **"Cloud SQL Admin API"** 클릭
5. **"사용 설정"** 버튼 클릭
6. 활성화 완료까지 1-2분 대기

---

### 방법 3: 필요한 모든 API 활성화

다음 API들도 함께 활성화하는 것을 권장합니다:

1. **Cloud SQL Admin API** (필수)
2. **Cloud SQL API** (필수)
3. **Compute Engine API** (이미 활성화됨)
4. **Cloud Build API** (자동 배포용, 선택사항)

---

## API 활성화 후

API가 활성화되면 (1-2분 후):

```bash
# Cloud SQL Proxy 재시작
pkill -f cloud_sql_proxy
nohup cloud_sql_proxy -instances=fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres=tcp:5432 > /tmp/cloud_sql_proxy.log 2>&1 &

# 확인
sleep 5
tail -20 /tmp/cloud_sql_proxy.log
```

성공하면 로그에 오류가 없고 연결이 성공합니다.

---

## 빠른 링크

**Cloud SQL Admin API 활성화:**
https://console.developers.google.com/apis/api/sqladmin.googleapis.com/overview?project=929081401130

