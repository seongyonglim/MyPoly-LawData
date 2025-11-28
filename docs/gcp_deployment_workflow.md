# GCP 배포 워크플로우

## 목표
로컬에서 개발 → GitHub 푸시 → GCP 자동 배포

---

## 워크플로우

```
로컬 개발 환경
    ↓
데이터 정제 및 코드 수정
    ↓
GitHub에 푸시
    ↓
Cloud Build 트리거 (자동)
    ↓
GCP VM에 배포
    ↓
서비스 재시작
    ↓
로컬에서 정제한 데이터 그대로 표시
```

---

## 1. 로컬 개발

### 데이터 정제
```bash
# 로컬 PostgreSQL에서 데이터 정제
python scripts/db/fix_data.py
python scripts/db/validate_data_quality.py
```

### 코드 수정
- `app.py` 수정
- 템플릿 수정
- 기타 코드 수정

---

## 2. GitHub에 푸시

```bash
git add .
git commit -m "데이터 정제 및 코드 수정"
git push origin main
```

---

## 3. 자동 배포 (Cloud Build)

GitHub에 푸시하면 자동으로:
1. Cloud Build가 코드를 VM에 복사
2. 의존성 설치
3. 서비스 재시작

---

## 4. 데이터 동기화

### 옵션 1: Cloud SQL에 직접 연결 (권장)
- 로컬에서 데이터 정제 후 Cloud SQL에 직접 업데이트
- VM은 Cloud SQL을 읽기만 함

### 옵션 2: 데이터 덤프/복원
- 로컬에서 데이터 덤프
- Cloud SQL로 가져오기

---

## 환경 변수 설정

### 로컬 (.env)
```
DB_HOST=localhost
DB_NAME=mypoly_lawdata
DB_USER=postgres
DB_PASSWORD=로컬비밀번호
```

### GCP VM (.env)
```
DB_HOST=127.0.0.1  # Cloud SQL Proxy를 통해 연결
DB_NAME=mypoly_lawdata
DB_USER=postgres
DB_PASSWORD=CloudSQL비밀번호
DB_INSTANCE_CONNECTION_NAME=프로젝트ID:지역:인스턴스ID
```

---

## 배포 확인

1. VM SSH 접속
2. 서비스 상태 확인: `sudo systemctl status mypoly-app`
3. 로그 확인: `sudo journalctl -u mypoly-app -f`
4. 브라우저에서 접속: `http://VM외부IP:5000`

