# Render PostgreSQL 연결 가이드

## 🔍 문제 해결

현재 제공된 연결 정보로는 외부에서 접속할 수 없습니다. Render PostgreSQL은 두 가지 URL을 제공합니다:

### 1. Internal Database URL (웹 서비스용)
- Render 서비스 **내부**에서만 사용 가능
- 웹 서비스 배포 시 사용
- 형식: `postgresql://user:password@host/database`

### 2. External Database URL (로컬 접속용)
- **외부**에서 접속 가능
- 로컬에서 테이블 생성 및 데이터 수집 시 사용
- 형식: `postgresql://user:password@host.region-postgres.render.com:5432/database`

## 📋 External Database URL 확인 방법

1. **Render Dashboard 접속**: https://dashboard.render.com
2. **PostgreSQL 서비스 클릭**: `mypoly-lawdata-db`
3. **"Connect" 탭** 클릭
4. **"External Connection" 섹션**에서 External Database URL 확인
   - 예시: `postgresql://mypoly_user:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/mypoly_lawdata`

## 🔧 해결 방법

### 방법 1: External URL 사용 (로컬에서 테이블 생성)

External Database URL을 확인한 후:

```bash
# 환경 변수 설정
set PGPASSWORD=<password>
psql -h <external-host>.oregon-postgres.render.com -U mypoly_user -d mypoly_lawdata -f scripts/db/create_tables_postgresql.sql
```

또는 Python 스크립트 수정:
```python
DATABASE_URL = "postgresql://mypoly_user:password@external-host.oregon-postgres.render.com:5432/mypoly_lawdata"
```

### 방법 2: 웹 서비스 배포 후 자동 생성 (추천)

로컬에서 테이블을 생성하지 않고, 웹 서비스 배포 후 자동으로 테이블을 생성하는 방법:

1. **웹 서비스 배포** (아래 가이드 참고)
2. **배포 후 첫 실행 시 테이블 자동 생성** (app.py에 추가 가능)

## 🚀 웹 서비스 배포 (Internal URL 사용)

웹 서비스 배포 시에는 **Internal Database URL**을 사용합니다:

### Render.com 웹 서비스 배포

1. **Render Dashboard → New + → Web Service**
2. **GitHub 레포지토리 연결**: `seongyonglim/MyPoly-LawData`
3. **설정:**
   - Name: `mypoly-lawdata-app`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
   - Plan: `Free`
4. **Environment Variables:**
   ```
   DB_HOST=dpg-d4jhgdfgi27c739n9m20-a
   DB_PORT=5432
   DB_NAME=mypoly_lawdata
   DB_USER=mypoly_user
   DB_PASSWORD=vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE
   FLASK_ENV=production
   ```
   또는 **DATABASE_URL** 사용:
   ```
   DATABASE_URL=postgresql://mypoly_user:vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE@dpg-d4jhgdfgi27c739n9m20-a/mypoly_lawdata
   ```

## 💡 권장 방법

**가장 쉬운 방법**: 웹 서비스 배포 후, Render Dashboard의 **Shell** 기능을 사용하여 테이블을 생성하거나, 배포된 웹 서비스에서 자동으로 테이블을 생성하도록 설정합니다.

---

**External Database URL을 확인한 후 알려주시면 테이블 생성 스크립트를 업데이트하겠습니다!**

