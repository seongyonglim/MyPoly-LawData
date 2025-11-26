# Render.com 배포 완료 가이드

## ✅ 완료된 작업

1. ✅ GitHub 레포지토리 생성 및 코드 업로드
2. ✅ Render.com PostgreSQL 생성
   - Service ID: `dpg-d4jhgdfgi27c739n9m20-a`
   - Database: `mypoly_lawdata`

## 📋 다음 단계

### 1. 데이터베이스 테이블 생성

로컬에서 Render PostgreSQL에 연결하여 테이블을 생성합니다:

**방법 1: Python 스크립트 사용 (추천)**
```bash
python scripts/db/setup_render_db.py
```

**방법 2: psql 직접 사용**
```bash
set PGPASSWORD=vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE
psql -h dpg-d4jhgdfgi27c739n9m20-a -U mypoly_user -d mypoly_lawdata -f scripts/db/create_tables_postgresql.sql
```

### 2. 데이터 수집 (선택사항)

테이블 생성 후 데이터를 수집할 수 있습니다:

```bash
# 데이터 수집 스크립트의 DB 연결 정보를 Render PostgreSQL로 변경 필요
# 또는 환경 변수로 설정
```

**주의**: 데이터 수집 스크립트는 현재 로컬 PostgreSQL에 연결하도록 설정되어 있습니다.
Render PostgreSQL에 연결하려면 스크립트를 수정하거나 환경 변수를 설정해야 합니다.

### 3. Render.com 웹 서비스 배포

1. **Render Dashboard 접속**: https://dashboard.render.com
2. **New + → Web Service** 클릭
3. **GitHub 레포지토리 연결:**
   - "Connect GitHub" 클릭
   - 레포지토리 선택: `seongyonglim/MyPoly-LawData`
4. **설정:**
   - Name: `mypoly-lawdata-app`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
   - Plan: `Free`
5. **Environment Variables 추가:**
   ```
   DB_HOST=dpg-d4jhgdfgi27c739n9m20-a
   DB_PORT=5432
   DB_NAME=mypoly_lawdata
   DB_USER=mypoly_user
   DB_PASSWORD=vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE
   FLASK_ENV=production
   ```
6. **Create Web Service** 클릭

### 4. 배포 완료 확인

배포가 완료되면 Render.com에서 제공하는 URL로 접속할 수 있습니다:
- 예시: `https://mypoly-lawdata-app.onrender.com`

---

## 🔧 문제 해결

### 데이터베이스 연결 오류

- 환경 변수가 올바르게 설정되었는지 확인
- Render Dashboard → Web Service → Environment에서 확인

### 빌드 실패

- `requirements.txt`에 모든 의존성이 포함되어 있는지 확인
- Render 로그에서 오류 메시지 확인

### 슬리프 모드

- Render 무료 티어는 15분간 요청이 없으면 슬리프 모드로 전환
- 첫 요청 시 약간 느릴 수 있음 (정상)

---

**질문이 있으면 언제든지 물어보세요!** 🚀

