# Render.com 데이터 수집 가이드

## 📋 개요

Render.com에 배포된 애플리케이션에 데이터를 수집하는 방법입니다.

## 🔧 사전 준비

### 1. 환경 변수 확인

Render Dashboard → **Web Service → Environment**에서 다음 환경 변수가 설정되어 있는지 확인:

```
DB_HOST=dpg-d4jhgdfgi27c739n9m20-a
DB_PORT=5432
DB_NAME=mypoly_lawdata
DB_USER=mypoly_user
DB_PASSWORD=vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE
ASSEMBLY_SERVICE_KEY=5e85053066dd409b81ed7de0f47bbcab
BILL_SERVICE_KEY=MiXjfqnyhsYErA%2FKEzOyLNFwxzbd%2B7VE0k2%2FeVml32gs8WjdeVCOQb06tgG5UaQ7u5bb74Hibe8WkwopNsXceA%3D%3D
```

## 📊 데이터 수집 순서

### 방법 1: 로컬에서 실행 (권장)

로컬 PC에서 스크립트를 실행하되, Render DB에 연결:

#### 1단계: 환경 변수 설정

**Windows (PowerShell):**
```powershell
$env:DB_HOST="dpg-d4jhgdfgi27c739n9m20-a"
$env:DB_PORT="5432"
$env:DB_NAME="mypoly_lawdata"
$env:DB_USER="mypoly_user"
$env:DB_PASSWORD="vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE"
$env:ASSEMBLY_SERVICE_KEY="5e85053066dd409b81ed7de0f47bbcab"
```

**Windows (CMD):**
```cmd
set DB_HOST=dpg-d4jhgdfgi27c739n9m20-a
set DB_PORT=5432
set DB_NAME=mypoly_lawdata
set DB_USER=mypoly_user
set DB_PASSWORD=vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE
set ASSEMBLY_SERVICE_KEY=5e85053066dd409b81ed7de0f47bbcab
```

#### 2단계: 데이터 수집 실행

**1. 국회의원 정보 수집 (22대 전체)**
```bash
python scripts/db/collect_22nd_members_complete.py
```

**2. 의안 정보 수집 (2025-08-01 이후)**
```bash
python scripts/db/collect_bills_from_date.py 20250801
```

**3. 표결 정보 수집 (2025-10-15 이후)**
```bash
python scripts/db/collect_votes_from_date.py 20251015
```

### 방법 2: Render Shell 사용 (무료 플랜 제한)

Render 무료 플랜에서는 Shell이 제한될 수 있습니다. 유료 플랜 사용 시:

1. **Render Dashboard → Web Service → Shell** 클릭
2. 환경 변수는 자동으로 설정됨
3. 위의 스크립트 실행

## ✅ 데이터 확인

### 웹 대시보드에서 확인

1. **의안 대시보드**: https://mypoly-lawdata-app.onrender.com
2. **DB 구조 페이지**: https://mypoly-lawdata-app.onrender.com/db-structure

### PostgreSQL에서 직접 확인

Render Dashboard → **PostgreSQL → Connect → psql** 클릭 후:

```sql
-- 의안 개수
SELECT COUNT(*) FROM bills;

-- 국회의원 개수
SELECT COUNT(*) FROM assembly_members;

-- 표결 정보 개수
SELECT COUNT(*) FROM votes;

-- 샘플 데이터 확인
SELECT * FROM bills LIMIT 5;
SELECT * FROM assembly_members LIMIT 5;
SELECT * FROM votes LIMIT 5;
```

## ⚠️ 주의사항

1. **API 호출 제한**: 각 스크립트는 API 호출 제한을 고려하여 0.5-1초씩 대기합니다.
2. **수집 시간**: 
   - 국회의원: 약 5-10분 (300명)
   - 의안: 약 30-60분 (수천 건)
   - 표결: 약 1-2시간 (수만 건)
3. **중복 처리**: `ON CONFLICT`를 사용하여 중복 데이터는 자동으로 업데이트됩니다.
4. **에러 처리**: 일부 데이터 오류는 건너뛰고 계속 진행합니다.

## 🔄 데이터 업데이트

### 일일 업데이트

```bash
# 최근 의안만 수집 (예: 어제부터)
python scripts/db/collect_bills_from_date.py 20251125

# 최근 표결만 수집 (예: 어제부터)
python scripts/db/collect_votes_from_date.py 20251125
```

---

**데이터 수집이 완료되면 웹 대시보드에서 데이터를 확인할 수 있습니다!** 🎉


