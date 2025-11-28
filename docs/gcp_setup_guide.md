# GCP 설정 가이드

**목표**: 로컬에서 개발 → GitHub 푸시 → GCP 자동 배포

---

## 1단계: GCP 프로젝트 생성 및 무료 크레딧 활성화

### 1.1 GCP 콘솔 접속
1. https://console.cloud.google.com 접속
2. 구글 계정으로 로그인

### 1.2 프로젝트 생성
1. 상단 프로젝트 선택 드롭다운 클릭
2. "새 프로젝트" 클릭
3. 프로젝트 이름: `mypoly-lawdata` (또는 원하는 이름)
4. "만들기" 클릭

### 1.3 무료 크레딧 활성화
1. 상단 검색창에서 "결제" 검색
2. "결제 계정 만들기" 클릭
3. 무료 체험 시작 (신용카드 등록 필요, 실제 과금 안 됨)
4. $300 무료 크레딧 받기 (90일간 사용 가능)

---

## 2단계: 필요한 API 활성화

### 2.1 API 라이브러리 접속
1. 상단 검색창에서 "API 및 서비스" → "라이브러리" 검색
2. 다음 API들을 활성화:
   - **Compute Engine API** (VM 인스턴스용)
   - **Cloud SQL Admin API** (PostgreSQL용)
   - **Cloud Build API** (자동 빌드/배포용)
   - **Cloud Source Repositories API** (GitHub 연동용, 선택사항)

---

## 3단계: Cloud SQL (PostgreSQL) 생성

### 3.1 Cloud SQL 인스턴스 생성
1. 상단 검색창에서 "Cloud SQL" 검색
2. "인스턴스 만들기" 클릭
3. **PostgreSQL** 선택
4. 인스턴스 ID: `mypoly-postgres`
5. 비밀번호 설정 (나중에 사용)
6. 지역: `asia-northeast3` (서울)
7. 머신 유형: **db-f1-micro** (무료 티어)
8. "만들기" 클릭

### 3.2 데이터베이스 생성
1. 생성된 인스턴스 클릭
2. "데이터베이스" 탭 → "데이터베이스 만들기"
3. 데이터베이스 이름: `mypoly_lawdata`
4. "만들기" 클릭

### 3.3 연결 정보 확인
1. 인스턴스 개요 페이지에서:
   - **연결 이름**: `프로젝트ID:지역:인스턴스ID` 형식
   - **공개 IP 주소**: 확인 (나중에 사용)

---

## 4단계: Compute Engine VM 생성

### 4.1 VM 인스턴스 생성
1. 상단 검색창에서 "Compute Engine" → "VM 인스턴스" 검색
2. "인스턴스 만들기" 클릭
3. 인스턴스 이름: `mypoly-app-server`
4. 지역: `asia-northeast3-a` (서울)
5. 머신 유형: **e2-micro** (무료 티어, 1개월 720시간 무료)
6. 부팅 디스크: **Ubuntu 22.04 LTS**
7. 방화벽: **HTTP 트래픽 허용**, **HTTPS 트래픽 허용** 체크
8. "만들기" 클릭

### 4.2 방화벽 규칙 추가 (필요시)
1. "VPC 네트워크" → "방화벽" 검색
2. "방화벽 규칙 만들기" 클릭
3. 이름: `allow-flask-5000`
4. 대상: `모든 인스턴스`
5. 소스 IP 범위: `0.0.0.0/0`
6. 프로토콜 및 포트: **TCP**, 포트 `5000`
7. "만들기" 클릭

---

## 5단계: GitHub 연동 및 자동 배포 설정

### 5.1 Cloud Build 트리거 생성
1. 상단 검색창에서 "Cloud Build" → "트리거" 검색
2. "트리거 만들기" 클릭
3. 이름: `github-deploy`
4. 이벤트: **푸시할 때**
5. 소스: **GitHub (첫 번째 빌드)** 선택
6. GitHub 인증 및 저장소 연결
7. 저장소: `seongyonglim/MyPoly-LawData` 선택
8. 분기: `main` (또는 `master`)
9. 구성: **Cloud Build 구성 파일 (yaml 또는 json)** 선택
10. 위치: `cloudbuild.yaml` (나중에 생성)
11. "만들기" 클릭

---

## 6단계: 로컬 데이터를 Cloud SQL로 마이그레이션

### 6.1 데이터 내보내기 (로컬)
```bash
# 로컬 PostgreSQL에서 데이터 덤프
pg_dump -h localhost -U postgres -d mypoly_lawdata > local_data.sql
```

### 6.2 Cloud SQL로 데이터 가져오기
1. Cloud SQL 인스턴스 페이지에서 "가져오기" 클릭
2. SQL 덤프 파일 업로드
3. 데이터베이스: `mypoly_lawdata` 선택
4. "가져오기" 클릭

---

## 7단계: 환경 변수 설정

### 7.1 Secret Manager 사용 (권장)
1. 상단 검색창에서 "Secret Manager" 검색
2. "비밀 만들기" 클릭
3. 다음 비밀들을 생성:
   - `db-password`: Cloud SQL 비밀번호
   - `db-connection-name`: Cloud SQL 연결 이름

---

## 다음 단계

1. `cloudbuild.yaml` 파일 생성 (자동 배포 스크립트)
2. VM 초기 설정 스크립트 생성
3. GitHub Actions 또는 Cloud Build 설정

