# GCP 콘솔에서 SQL 파일 가져오기 (최종 방법)

## 생성된 파일

- 파일명: `local_data_final_clean.sql`
- 크기: 약 35MB
- 위치: `C:\polywave\MyPoly-LawData\local_data_final_clean.sql`
- 특징: 확장 관련 부분 제거, 올바른 옵션 사용

---

## GCP 콘솔에서 가져오기

### 1단계: GCP 콘솔 접속

1. **GCP 콘솔** → **Cloud SQL** → 인스턴스 `mypoly-postgres` 클릭
2. **"가져오기"** 탭 클릭

### 2단계: 파일 업로드

1. **"컴퓨터에서 파일 업로드"** 선택
2. **"로컬 파일 선택"** 클릭
3. 파일 선택: `C:\polywave\MyPoly-LawData\local_data_final_clean.sql`

### 3단계: Cloud Storage 위치 선택

1. **"Cloud Storage 위치 선택"** 클릭
2. 기존 버킷 선택 (예: `mypoly-lawdata-import`)
   - 또는 새 버킷 생성

### 4단계: 데이터베이스 선택

1. **데이터베이스**: `mypoly_lawdata` 선택
2. **"가져오기"** 클릭

### 5단계: 완료 대기

- 파일 크기: 약 35MB
- 예상 시간: 5-10분

---

## 완료 후 확인

1. 브라우저에서 `http://34.64.212.103:5000` 접속
2. 데이터가 정상적으로 표시되는지 확인

---

## 문제 해결

### 여전히 확장 오류 발생 시

SQL 파일에서 확장 관련 부분을 수동으로 제거:
- `CREATE EXTENSION` 줄 삭제
- `COMMENT ON EXTENSION` 줄 삭제

