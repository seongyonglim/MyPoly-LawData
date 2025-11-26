# Render.com 웹 서비스 배포 가이드

## ✅ 현재 상태

- ✅ GitHub 레포지토리: https://github.com/seongyonglim/MyPoly-LawData
- ✅ Render PostgreSQL 생성 완료
  - Service ID: `dpg-d4jhgdfgi27c739n9m20-a`
  - Internal URL: `postgresql://mypoly_user:vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE@dpg-d4jhgdfgi27c739n9m20-a/mypoly_lawdata`

## 🚀 웹 서비스 배포 단계

### 1. Render Dashboard에서 웹 서비스 생성

1. **Render Dashboard 접속**: https://dashboard.render.com
2. **New + → Web Service** 클릭
3. **GitHub 레포지토리 연결:**
   - "Connect GitHub" 클릭
   - 레포지토리 선택: `seongyonglim/MyPoly-LawData`
   - "Connect" 클릭

### 2. 웹 서비스 설정

**기본 설정:**
- **Name**: `mypoly-lawdata-app` (또는 원하는 이름)
- **Environment**: `Python 3`
- **Region**: `Singapore` (한국과 가까움)
- **Branch**: `main`
- **Root Directory**: (비워두기)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`
- **Plan**: `Free`

### 3. Environment Variables 설정

**"Advanced" 섹션 → "Add Environment Variable" 클릭:**

다음 환경 변수를 추가하세요:

| Key | Value |
|-----|-------|
| `DB_HOST` | `dpg-d4jhgdfgi27c739n9m20-a` |
| `DB_PORT` | `5432` |
| `DB_NAME` | `mypoly_lawdata` |
| `DB_USER` | `mypoly_user` |
| `DB_PASSWORD` | `vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE` |
| `FLASK_ENV` | `production` |

또는 **DATABASE_URL** 하나만 사용:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql://mypoly_user:vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE@dpg-d4jhgdfgi27c739n9m20-a/mypoly_lawdata` |

### 4. 웹 서비스 생성

**"Create Web Service"** 클릭

### 5. 배포 완료 대기

- 빌드 및 배포가 자동으로 시작됩니다
- 약 5-10분 소요될 수 있습니다
- 배포가 완료되면 URL이 제공됩니다 (예: `https://mypoly-lawdata-app.onrender.com`)

## 📊 배포 후 작업

### 테이블 생성

배포가 완료되면, Render Dashboard의 **Shell** 기능을 사용하여 테이블을 생성할 수 있습니다:

1. **Web Service → Shell** 클릭
2. 다음 명령어 실행:
   ```bash
   python scripts/db/setup_render_db.py
   ```

또는 **로컬에서 External Database URL 사용** (External URL 확인 필요)

## ✅ 완료!

배포가 완료되면 팀원들이 제공된 URL로 접속할 수 있습니다!

---

**배포 중 문제가 있으면 Render Dashboard의 Logs를 확인하세요!**

