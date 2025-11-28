# Render.com 테이블 생성 디버깅 가이드

## 🔴 현재 문제

여전히 "relation 'bills' does not exist" 오류가 발생합니다.

## 🔍 가능한 원인

1. **환경 변수 미설정**: Render Dashboard에서 DB 연결 정보가 설정되지 않음
2. **SQL 파일 경로 문제**: 배포 환경에서 SQL 파일을 찾을 수 없음
3. **초기화 함수 미실행**: `init_database_if_needed()`가 실행되지 않음
4. **데이터베이스 연결 오류**: 다른 데이터베이스에 연결됨

## ✅ 확인 사항

### 1. Render Dashboard에서 환경 변수 확인

**Web Service → Environment**에서 다음 환경 변수가 설정되어 있는지 확인:

```
DB_HOST=dpg-d4jhgdfgi27c739n9m20-a
DB_PORT=5432
DB_NAME=mypoly_lawdata
DB_USER=mypoly_user
DB_PASSWORD=vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE
FLASK_ENV=production
```

### 2. Render Logs 확인

**Web Service → Logs**에서 다음 메시지를 확인:

- ✅ "데이터베이스 테이블이 없습니다. 자동 생성 중..."
- ✅ "SQL 파일 경로: ..."
- ✅ "✅ X개 SQL 문장 실행 완료"
- ✅ "생성된 테이블: bills, assembly_members, votes, ..."

이 메시지가 없다면:
- 환경 변수가 설정되지 않았거나
- 초기화 함수가 실행되지 않았을 수 있습니다

### 3. 데이터베이스 연결 확인

**PostgreSQL → Connect**에서:
- Internal Database URL 확인
- 환경 변수와 일치하는지 확인

## 🔧 해결 방법

### 방법 1: 환경 변수 재설정

1. **Render Dashboard → Web Service → Environment**
2. **모든 환경 변수 삭제 후 다시 추가**
3. **재배포**

### 방법 2: 로컬에서 External URL 사용

Render Dashboard → PostgreSQL → Connect → **External Database URL** 확인 후:

```bash
# 환경 변수 설정
set PGPASSWORD=vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE

# External URL 형식: postgresql://user:password@host:port/database
# 예시: postgresql://mypoly_user:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/mypoly_lawdata

psql -h <external-host> -U mypoly_user -d mypoly_lawdata -f scripts/db/create_tables_postgresql.sql
```

### 방법 3: 수동 SQL 실행

Render Dashboard → PostgreSQL → **Connect** → **psql** 클릭 후:

```sql
-- SQL 파일 내용을 복사해서 직접 실행
\i scripts/db/create_tables_postgresql.sql
```

또는 SQL 파일의 내용을 직접 복사해서 실행

---

**Render Logs를 확인해서 어떤 메시지가 나오는지 알려주세요!** 🔍


