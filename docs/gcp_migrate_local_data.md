# 로컬 데이터를 Cloud SQL로 마이그레이션

## 방법 1: pg_dump + GCP 콘솔 가져오기 (권장)

### 1단계: 로컬에서 데이터 덤프

**로컬 PC에서** (VM이 아닌):

```bash
# 로컬 PostgreSQL에서 데이터 덤프
pg_dump -h localhost -U postgres -d mypoly_lawdata > local_data.sql

# 비밀번호 입력: maza_970816
```

### 2단계: GCP 콘솔에서 가져오기

1. **GCP 콘솔** → **Cloud SQL** → 인스턴스 `mypoly-postgres` 클릭
2. **"가져오기"** 탭 클릭
3. **"파일 선택"** 클릭 → `local_data.sql` 파일 업로드
4. **데이터베이스**: `mypoly_lawdata` 선택
5. **"가져오기"** 클릭
6. 완료까지 대기 (데이터 양에 따라 5-30분)

---

## 방법 2: Python 스크립트 사용 (직접 연결)

### 1단계: Cloud SQL 공개 IP 확인

GCP 콘솔 → Cloud SQL → 인스턴스 개요 → **공개 IP 주소** 확인
- 예: `34.50.48.31`

### 2단계: 스크립트 수정

`scripts/gcp/migrate_data_to_cloud_sql.py` 파일에서:

```python
CLOUD_DB = {
    'host': '34.50.48.31',  # Cloud SQL 공개 IP
    'database': 'mypoly_lawdata',
    'user': 'postgres',
    'password': 'Mypoly!2025',  # Cloud SQL 비밀번호
    'port': 5432
}
```

### 3단계: 스크립트 실행

**로컬 PC에서**:

```bash
cd C:\polywave\MyPoly-LawData
python scripts/gcp/migrate_data_to_cloud_sql.py
```

---

## 방법 3: psql로 직접 연결 (소규모 데이터)

### 1단계: 로컬에서 덤프

```bash
pg_dump -h localhost -U postgres -d mypoly_lawdata > local_data.sql
```

### 2단계: Cloud SQL로 직접 가져오기

```bash
# Cloud SQL 공개 IP로 직접 연결
psql -h 34.50.48.31 -U postgres -d mypoly_lawdata -f local_data.sql

# 비밀번호 입력: Mypoly!2025
```

**주의**: Cloud SQL의 방화벽 규칙에서 로컬 PC의 IP를 허용해야 할 수 있습니다.

---

## 권장 방법: 방법 1 (pg_dump + GCP 콘솔)

가장 안정적이고 간단합니다:

1. ✅ 네트워크 설정 불필요
2. ✅ 대용량 데이터 처리 가능
3. ✅ 진행 상황 확인 가능
4. ✅ 오류 처리 자동

---

## 체크리스트

- [ ] 로컬 데이터 덤프 완료
- [ ] Cloud SQL 테이블 생성 완료
- [ ] 데이터 가져오기 완료
- [ ] 앱에서 데이터 확인

---

## 문제 해결

### 연결 오류
- Cloud SQL 방화벽 규칙 확인
- 공개 IP 주소 확인

### 가져오기 실패
- SQL 파일 크기 확인 (너무 크면 분할)
- Cloud SQL 인스턴스 용량 확인

