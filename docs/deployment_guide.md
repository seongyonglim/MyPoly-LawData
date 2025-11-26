# 배포 가이드 - 팀원 공유용 웹 앱 배포

**생성일**: 2025-11-26

---

## 🎯 목표

로컬호스트가 아닌 인터넷을 통해 팀원들이 접속할 수 있도록 웹 앱을 배포합니다.
데이터베이스(PostgreSQL)도 함께 배포해야 합니다.

---

## 📋 추천 무료 배포 플랫폼

### 1. **Render.com** (가장 추천 ⭐)

**장점:**
- ✅ 무료 티어 제공 (제한적이지만 충분)
- ✅ PostgreSQL 무료 제공 (90일 무료, 이후 유료)
- ✅ GitHub 연동으로 자동 배포
- ✅ SSL 인증서 자동 제공 (HTTPS)
- ✅ 설정이 간단함
- ✅ 한국어 지원 없지만 사용하기 쉬움

**단점:**
- ⚠️ 무료 티어는 15분간 요청이 없으면 슬리프 모드 (첫 요청 시 느림)
- ⚠️ PostgreSQL 무료는 90일 후 유료 전환 필요

**비용:**
- 웹 서비스: 무료 (슬리프 모드)
- PostgreSQL: 90일 무료 → 이후 $7/월

**추천 이유:** 가장 간단하고 안정적이며, PostgreSQL을 쉽게 연결할 수 있습니다.

---

### 2. **Railway.app** (두 번째 추천 ⭐)

**장점:**
- ✅ 무료 크레딧 제공 ($5/월 크레딧)
- ✅ PostgreSQL 지원
- ✅ GitHub 연동
- ✅ 자동 배포
- ✅ 슬리프 모드 없음 (무료 크레딧 사용)

**단점:**
- ⚠️ 무료 크레딧이 소진되면 유료 전환 필요
- ⚠️ 초기 설정이 Render보다 약간 복잡

**비용:**
- 웹 서비스: 무료 크레딧 ($5/월)
- PostgreSQL: 무료 크레딧 포함

**추천 이유:** 슬리프 모드가 없어서 항상 빠르게 응답합니다.

---

### 3. **Fly.io** (고급 사용자용)

**장점:**
- ✅ 무료 티어 제공
- ✅ PostgreSQL 지원
- ✅ 전 세계 CDN
- ✅ 매우 빠름

**단점:**
- ⚠️ 설정이 복잡함
- ⚠️ CLI 도구 필요

**비용:**
- 웹 서비스: 무료 (제한적)
- PostgreSQL: 무료 (제한적)

---

## 🚀 Render.com 배포 가이드 (추천)

### 1단계: GitHub에 코드 업로드

```bash
# Git 초기화 (아직 안 했다면)
git init
git add .
git commit -m "Initial commit"

# GitHub에 새 레포지토리 생성 후
git remote add origin https://github.com/your-username/MyPoly-LawData.git
git push -u origin main
```

### 2단계: Render.com 가입 및 설정

1. **Render.com 가입**: https://render.com
2. **New + → PostgreSQL** 클릭
   - Name: `mypoly-lawdata-db`
   - Database: `mypoly_lawdata`
   - User: `mypoly_user`
   - Region: `Singapore` (한국과 가까움)
   - PostgreSQL Version: `16` (또는 최신)
   - **Create Database** 클릭

3. **Database 정보 확인**
   - Internal Database URL 복사 (나중에 사용)
   - External Database URL 복사 (로컬에서 접속용)

### 3단계: 환경 변수 설정

**Render Dashboard → PostgreSQL → Connect → Environment Variables**에서:
- `PGPASSWORD`: 데이터베이스 비밀번호
- `PGHOST`: 호스트 주소
- `PGPORT`: 포트 (보통 5432)
- `PGDATABASE`: 데이터베이스 이름
- `PGUSER`: 사용자 이름

### 4단계: 웹 서비스 배포

1. **New + → Web Service** 클릭
2. **GitHub 레포지토리 연결**
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

### 5단계: app.py 수정 (환경 변수 사용)

```python
import os

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'maza_970816'),
    'port': int(os.environ.get('DB_PORT', 5432))
}
```

### 6단계: 데이터베이스 마이그레이션

**로컬에서:**
```bash
# Render PostgreSQL에 연결
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

---

## 🚀 Railway.app 배포 가이드 (대안)

### 1단계: Railway 가입

1. **Railway.app 가입**: https://railway.app
2. **GitHub 연동**

### 2단계: 프로젝트 생성

1. **New Project → Deploy from GitHub repo**
2. **레포지토리 선택**

### 3단계: PostgreSQL 추가

1. **New → Database → PostgreSQL**
2. **자동으로 생성됨**

### 4단계: 환경 변수 설정

Railway는 자동으로 PostgreSQL 연결 정보를 환경 변수로 제공:
- `DATABASE_URL`: 자동 생성됨

**app.py 수정:**
```python
import os
from urllib.parse import urlparse

# Railway는 DATABASE_URL을 제공
if 'DATABASE_URL' in os.environ:
    db_url = urlparse(os.environ['DATABASE_URL'])
    DB_CONFIG = {
        'host': db_url.hostname,
        'database': db_url.path[1:],  # / 제거
        'user': db_url.username,
        'password': db_url.password,
        'port': db_url.port or 5432
    }
else:
    # 로컬 개발용
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'mypoly_lawdata',
        'user': 'postgres',
        'password': 'maza_970816',
        'port': 5432
    }
```

### 5단계: 배포 설정

**railway.json** (프로젝트 루트에 생성):
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python app.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## 📝 배포 전 체크리스트

### 필수 수정 사항

1. **app.py 환경 변수 지원**
   - ✅ 로컬과 프로덕션 환경 구분
   - ✅ 데이터베이스 연결 정보를 환경 변수로 받기

2. **requirements.txt 확인**
   - ✅ 모든 의존성 포함
   - ✅ 버전 명시

3. **보안 설정**
   - ✅ 데이터베이스 비밀번호 하드코딩 제거
   - ✅ API 키 환경 변수로 관리
   - ✅ `debug=False` (프로덕션)

4. **포트 설정**
   - ✅ Render/Railway는 자동으로 PORT 환경 변수 제공
   - ✅ `app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))`

---

## 🔧 app.py 수정 예시

```python
import os
from flask import Flask, render_template, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# 환경 변수에서 데이터베이스 설정 가져오기
def get_db_config():
    # Railway는 DATABASE_URL 제공
    if 'DATABASE_URL' in os.environ:
        from urllib.parse import urlparse
        db_url = urlparse(os.environ['DATABASE_URL'])
        return {
            'host': db_url.hostname,
            'database': db_url.path[1:],
            'user': db_url.username,
            'password': db_url.password,
            'port': db_url.port or 5432
        }
    # Render는 개별 환경 변수 제공
    elif 'DB_HOST' in os.environ:
        return {
            'host': os.environ.get('DB_HOST'),
            'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': os.environ.get('DB_PASSWORD'),
            'port': int(os.environ.get('DB_PORT', 5432))
        }
    # 로컬 개발용
    else:
        return {
            'host': 'localhost',
            'database': 'mypoly_lawdata',
            'user': 'postgres',
            'password': 'maza_970816',
            'port': 5432
        }

def get_db_connection():
    """데이터베이스 연결"""
    return psycopg2.connect(**get_db_config())

# ... (나머지 코드)

if __name__ == '__main__':
    # 프로덕션 환경에서는 PORT 환경 변수 사용
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print("=" * 60)
    print("2025년 의안 표결 결과 웹 대시보드 시작")
    print("=" * 60)
    print(f"서버 주소: http://0.0.0.0:{port}")
    print(f"의안 대시보드: http://0.0.0.0:{port}")
    print(f"DB 구조 페이지: http://0.0.0.0:{port}/db-structure")
    print(f"ERD 페이지: http://0.0.0.0:{port}/erd")
    print("=" * 60)
    
    app.run(debug=debug, host='0.0.0.0', port=port)
```

---

## 📊 비교표

| 플랫폼 | 무료 티어 | PostgreSQL | 슬리프 모드 | 설정 난이도 | 추천도 |
|--------|----------|------------|------------|------------|--------|
| **Render.com** | ✅ | ✅ (90일) | ⚠️ 있음 | ⭐⭐ 쉬움 | ⭐⭐⭐⭐⭐ |
| **Railway.app** | ✅ ($5 크레딧) | ✅ | ❌ 없음 | ⭐⭐⭐ 보통 | ⭐⭐⭐⭐ |
| **Fly.io** | ✅ | ✅ | ❌ 없음 | ⭐⭐⭐⭐ 어려움 | ⭐⭐⭐ |

---

## 🎯 최종 추천

**Render.com을 추천합니다:**
1. 설정이 가장 간단함
2. PostgreSQL 무료 제공 (90일)
3. GitHub 연동으로 자동 배포
4. SSL 자동 제공 (HTTPS)
5. 한국어 문서는 없지만 사용하기 쉬움

---

## 📞 다음 단계

1. **Render.com 가입 및 PostgreSQL 생성**
2. **app.py 수정** (환경 변수 지원)
3. **GitHub에 코드 업로드**
4. **Render에서 웹 서비스 배포**
5. **데이터베이스 마이그레이션**
6. **팀원들에게 URL 공유**

---

## ⚠️ 주의사항

1. **무료 티어 제한:**
   - Render: 15분간 요청 없으면 슬리프 모드 (첫 요청 시 느림)
   - Railway: 무료 크레딧 소진 시 유료 전환 필요

2. **데이터베이스 백업:**
   - 정기적으로 데이터 백업 권장
   - Render/Railway는 자동 백업 제공 (유료 플랜)

3. **보안:**
   - 환경 변수에 민감한 정보 저장
   - API 키는 절대 코드에 하드코딩하지 않기

---

**질문이나 문제가 있으면 언제든지 물어보세요!** 🚀

