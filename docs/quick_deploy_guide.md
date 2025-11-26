# 빠른 배포 가이드

## ✅ 완료된 작업

1. ✅ Git 저장소 초기화
2. ✅ .gitignore 생성
3. ✅ README.md 생성
4. ✅ requirements.txt 업데이트
5. ✅ Render.com 배포 설정 파일 생성

## 📋 다음 단계

### 1. GitHub에 레포지토리 생성 및 업로드

**GitHub에서:**
1. https://github.com 접속
2. 우측 상단 "+" → "New repository"
3. 레포지토리 이름: `MyPoly-LawData`
4. **"Initialize this repository with a README" 체크 해제**
5. **"Add .gitignore" 체크 해제**
6. "Create repository" 클릭

**터미널에서:**
```bash
# YOUR_USERNAME을 실제 GitHub 사용자명으로 변경
git remote add origin https://github.com/YOUR_USERNAME/MyPoly-LawData.git
git push -u origin main
```

### 2. Render.com에서 PostgreSQL 생성

1. **Render.com 접속**: https://render.com
2. **Dashboard → New + → PostgreSQL** 클릭
3. **설정:**
   - Name: `mypoly-lawdata-db`
   - Database: `mypoly_lawdata`
   - User: `mypoly_user`
   - Region: `Singapore` (한국과 가까움)
   - PostgreSQL Version: `16`
4. **Create Database** 클릭
5. **Database 정보 복사:**
   - Internal Database URL (웹 서비스에서 사용)
   - External Database URL (로컬에서 접속용)

### 3. Render.com에서 웹 서비스 배포

1. **Dashboard → New + → Web Service** 클릭
2. **GitHub 레포지토리 연결:**
   - "Connect GitHub" 클릭
   - 레포지토리 선택: `MyPoly-LawData`
3. **설정:**
   - Name: `mypoly-lawdata-app`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
   - Plan: `Free`
4. **Environment Variables 추가:**
   ```
   DB_HOST=<PostgreSQL Internal Host>
   DB_PORT=5432
   DB_NAME=mypoly_lawdata
   DB_USER=mypoly_user
   DB_PASSWORD=<PostgreSQL Password>
   FLASK_ENV=production
   ```
5. **Create Web Service** 클릭

### 4. 데이터베이스 마이그레이션

**로컬에서 Render PostgreSQL에 연결:**

```bash
# 환경 변수 설정 (Render에서 제공한 External Database URL 사용)
export PGHOST=<External Database Host>
export PGPORT=5432
export PGDATABASE=mypoly_lawdata
export PGUSER=mypoly_user
export PGPASSWORD=<Password>

# 테이블 생성
psql -h <External Database Host> -U mypoly_user -d mypoly_lawdata -f scripts/db/create_tables_postgresql.sql

# 데이터 수집 (선택사항)
python scripts/db/collect_22nd_members_complete.py
python scripts/db/collect_bills_from_date.py 20250801
python scripts/db/collect_votes_from_date.py 20251015
```

### 5. 완료!

Render.com에서 제공하는 URL로 접속하면 웹 앱을 사용할 수 있습니다!

**예시 URL:** `https://mypoly-lawdata-app.onrender.com`

---

## 🔧 문제 해결

### 데이터베이스 연결 오류

- 환경 변수가 올바르게 설정되었는지 확인
- Internal Database URL 사용 (웹 서비스용)
- External Database URL 사용 (로컬 접속용)

### 빌드 실패

- `requirements.txt`에 모든 의존성이 포함되어 있는지 확인
- Render 로그에서 오류 메시지 확인

### 슬리프 모드

- Render 무료 티어는 15분간 요청이 없으면 슬리프 모드로 전환
- 첫 요청 시 약간 느릴 수 있음 (정상)

---

**질문이 있으면 언제든지 물어보세요!** 🚀

