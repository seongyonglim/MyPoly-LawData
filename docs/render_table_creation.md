# Render.com 데이터베이스 테이블 생성 가이드

## 🔴 현재 오류

```
psycopg2.errors.UndefinedTable: relation "bills" does not exist
```

데이터베이스 테이블이 아직 생성되지 않았습니다.

## ✅ 해결 방법

### 방법 1: Render Shell 사용 (즉시 해결)

1. **Render Dashboard → Web Service → Shell** 클릭
2. 다음 명령어 실행:
   ```bash
   python scripts/db/setup_render_db.py
   ```

### 방법 2: 자동 생성 (다음 배포 시)

코드에 자동 테이블 생성 로직을 추가했습니다. 다음 배포 시 자동으로 테이블이 생성됩니다.

**현재 배포된 버전에서는 수동으로 생성해야 합니다.**

## 📋 Render Shell에서 테이블 생성

1. **Render Dashboard 접속**
2. **Web Service → Shell** 클릭
3. **다음 명령어 실행:**
   ```bash
   python scripts/db/setup_render_db.py
   ```

또는 직접 SQL 실행:
```bash
psql $DATABASE_URL -f scripts/db/create_tables_postgresql.sql
```

## ✅ 완료 확인

테이블 생성 후 웹 페이지를 새로고침하면 정상적으로 작동합니다.

---

**Render Shell에서 `python scripts/db/setup_render_db.py`를 실행하세요!** 🚀


