# Render PostgreSQL 연결 정보

## 데이터베이스 정보

- **Service ID**: `dpg-d4jhgdfgi27c739n9m20-a`
- **Connection URL**: `postgresql://mypoly_user:vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE@dpg-d4jhgdfgi27c739n9m20-a/mypoly_lawdata`

## 연결 정보 파싱

- **Host**: `dpg-d4jhgdfgi27c739n9m20-a`
- **Port**: `5432` (기본값)
- **Database**: `mypoly_lawdata`
- **User**: `mypoly_user`
- **Password**: `vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE`

## 웹 서비스 환경 변수 설정

Render.com 웹 서비스 배포 시 다음 환경 변수를 설정하세요:

```
DB_HOST=dpg-d4jhgdfgi27c739n9m20-a
DB_PORT=5432
DB_NAME=mypoly_lawdata
DB_USER=mypoly_user
DB_PASSWORD=vvqeu5p1pty5ZhxsbbqFGAiufGeBYuIE
FLASK_ENV=production
```

⚠️ **주의**: 이 파일은 민감한 정보를 포함하므로 `.gitignore`에 추가되어 있습니다.

