# VM을 통해 데이터 마이그레이션 (가장 확실한 방법)

## 문제
- pg_dump 파일 인코딩 오류
- Cloud SQL 공개 IP 직접 연결 방화벽 문제

## 해결: VM에서 Python 스크립트 실행

VM은 이미 Cloud SQL Proxy로 연결되어 있으므로, VM에서 스크립트를 실행하면 됩니다.

---

## 단계별 가이드

### 1단계: 스크립트를 VM으로 복사

**로컬 PC에서**:

```bash
# VM의 공개 IP 확인 (GCP 콘솔에서)
# 예: 34.64.212.103

# 스크립트 복사
scp scripts/gcp/migrate_direct.py seongyonglim3@34.64.212.103:~/MyPoly-LawData/scripts/gcp/
```

또는 **VM SSH 창에서**:

```bash
cd ~/MyPoly-LawData
git pull origin main  # 최신 코드 가져오기
```

### 2단계: VM에서 스크립트 실행

**VM SSH 창에서**:

```bash
cd ~/MyPoly-LawData
source venv/bin/activate

# Cloud SQL Proxy가 실행 중인지 확인
ps aux | grep cloud_sql_proxy

# 스크립트 실행
python scripts/gcp/migrate_direct.py
```

---

## 스크립트 수정 필요

VM에서 실행할 때는 `migrate_direct.py`의 `LOCAL_DB`를 수정해야 합니다:

```python
# 로컬 DB에 직접 접속할 수 없다면,
# 로컬에서 먼저 데이터를 CSV로 내보내고 VM으로 전송하는 방법 사용
```

또는 **더 간단한 방법**: 로컬에서 CSV로 내보내기

---

## 가장 간단한 방법: CSV 내보내기

### 로컬에서:

```bash
# bills 테이블
psql -h localhost -U postgres -d mypoly_lawdata -c "COPY bills TO STDOUT WITH CSV HEADER" > bills.csv

# assembly_members 테이블
psql -h localhost -U postgres -d mypoly_lawdata -c "COPY assembly_members TO STDOUT WITH CSV HEADER" > assembly_members.csv

# votes 테이블
psql -h localhost -U postgres -d mypoly_lawdata -c "COPY votes TO STDOUT WITH CSV HEADER" > votes.csv
```

### VM으로 전송:

```bash
scp *.csv seongyonglim3@34.64.212.103:~/MyPoly-LawData/
```

### VM에서 가져오기:

```bash
psql -h 127.0.0.1 -U postgres -d mypoly_lawdata -c "COPY bills FROM STDIN WITH CSV HEADER" < bills.csv
```

---

## 추천: Python 스크립트 사용 (VM에서)

가장 확실한 방법입니다. VM에서 실행하면 모든 연결 문제가 해결됩니다.

