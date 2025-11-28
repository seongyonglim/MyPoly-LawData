@echo off
REM 로컬 DB를 Render DB로 이전 (pg_dump + psql 사용)
REM Render Dashboard에서 External Database URL을 확인하세요

echo ============================================================
echo 로컬 DB → Render DB 데이터 이전
echo ============================================================
echo.

REM Render External Database URL 설정
REM Render Dashboard → PostgreSQL → Connect → External Database URL 복사
set RENDER_DB_URL=postgresql://mypoly_user:vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE@dpg-d4jhgdfgi27c739n9m20-a.oregon-postgres.render.com:5432/mypoly_lawdata

echo 1. 로컬 DB 덤프 생성 중...
pg_dump -h localhost -U postgres -d mypoly_lawdata -F c -f local_db_dump.backup

if %ERRORLEVEL% NEQ 0 (
    echo ❌ 덤프 생성 실패
    pause
    exit /b 1
)

echo.
echo 2. Render DB로 복원 중...
echo    (비밀번호 입력 필요: maza_970816)
pg_restore -d "%RENDER_DB_URL%" -c -v local_db_dump.backup

if %ERRORLEVEL% NEQ 0 (
    echo ❌ 복원 실패
    pause
    exit /b 1
)

echo.
echo ✅ 데이터 이전 완료!
echo.
del local_db_dump.backup
pause


