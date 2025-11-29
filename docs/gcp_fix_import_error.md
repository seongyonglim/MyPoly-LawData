# 데이터 가져오기 오류 해결

## 문제
```
ERROR: must be owner of extension uuid-ossp
```

## 원인
pg_dump로 덤프할 때 확장(extension) 정보가 포함되어 있고, Cloud SQL의 postgres 사용자가 해당 확장의 소유자가 아니어서 발생합니다.

## 해결 방법

### 방법 1: --no-owner 옵션으로 다시 덤프 (권장)

로컬 PC에서:

```bash
cd C:\polywave\MyPoly-LawData

# 기존 파일 삭제
del local_data.sql

# --no-owner 옵션으로 다시 덤프
$env:PGPASSWORD="maza_970816"; pg_dump -h localhost -U postgres -d mypoly_lawdata --no-owner --no-acl -f local_data.sql
```

### 방법 2: SQL 파일에서 확장 관련 부분 제거

덤프 파일을 열어서 다음 줄들을 찾아 삭제:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;
COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';
```

---

## 권장: --no-owner 옵션 사용

`--no-owner` 옵션을 사용하면:
- 소유자 정보가 제외되어 Cloud SQL에서 문제없이 가져올 수 있습니다
- 확장 관련 권한 문제가 발생하지 않습니다

