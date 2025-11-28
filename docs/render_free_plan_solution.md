# Render.com 무료 플랜 테이블 생성 해결 방법

## 🔴 문제

Render.com 무료 플랜에서는 **Shell 접근이 불가능**합니다. 따라서 Shell을 통해 테이블을 생성할 수 없습니다.

## ✅ 해결 방법

### 방법 1: 앱 자동 테이블 생성 (추천) ⭐

코드에 **앱 시작 시 자동으로 테이블을 생성하는 로직**을 추가했습니다.

**작동 방식:**
1. 앱이 시작될 때 `bills` 테이블이 있는지 확인
2. 테이블이 없으면 `create_tables_postgresql.sql` 파일을 읽어서 자동 실행
3. 테이블 생성 완료

**다음 배포 시 자동으로 테이블이 생성됩니다!**

### 방법 2: 로컬에서 External Database URL 사용

Render Dashboard → PostgreSQL → Connect → **External Database URL** 확인 후:

```bash
# 환경 변수 설정
set PGPASSWORD=<password>
psql -h <external-host>.oregon-postgres.render.com -U mypoly_user -d mypoly_lawdata -f scripts/db/create_tables_postgresql.sql
```

또는 Python 스크립트 사용:
```bash
# scripts/db/setup_render_db.py의 DATABASE_URL을 External URL로 변경 후
python scripts/db/setup_render_db.py
```

## 🚀 현재 상태

- ✅ 자동 테이블 생성 코드 추가 완료
- ✅ GitHub에 푸시 완료
- 🔄 Render.com에서 자동 재배포 대기 중

## 📋 다음 단계

1. **Render Dashboard에서 재배포 확인**
   - Events 섹션에서 새로운 배포 확인
   - 또는 "Manual Deploy" → "Deploy latest commit" 클릭

2. **배포 완료 후 확인**
   - 배포 로그에서 "데이터베이스 테이블이 없습니다. 자동 생성 중..." 메시지 확인
   - 웹 페이지 접속 테스트

3. **테이블 생성 확인**
   - 웹 페이지가 정상적으로 작동하면 테이블 생성 성공!

---

**다음 배포 시 자동으로 테이블이 생성됩니다!** 🎉


