# Cloud SQL 연결 정보 확인 및 기록 방법

## 1단계: 연결 정보 확인

### Cloud SQL 인스턴스 페이지에서

1. **현재 페이지에서** (데이터베이스 탭)
   - 왼쪽 메뉴에서 **"개요"** 또는 **"연결"** 클릭

2. **연결 정보 확인**
   - **"연결 이름"**: 복사 버튼 클릭
     - 예: `fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres`
   - **"공개 IP 주소"**: 복사 버튼 클릭
     - 예: `34.50.48.31`
   - **비밀번호**: `Mypoly!2025` (이미 설정한 비밀번호)

---

## 2단계: 연결 정보 기록할 곳

### 옵션 1: 메모장/텍스트 파일에 임시 저장 (권장)

로컬 PC에서 메모장 열고 다음 정보 저장:

```
=== Cloud SQL 연결 정보 ===
연결 이름: fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres
공개 IP: 34.50.48.31
데이터베이스 이름: mypoly_lawdata
사용자: postgres
비밀번호: Mypoly!2025
포트: 5432
```

### 옵션 2: VM의 .env 파일에 저장 (나중에)

VM 생성 후 SSH 접속해서:
```bash
cd /home/app/MyPoly-LawData
cat > .env << EOF
DB_HOST=127.0.0.1
DB_NAME=mypoly_lawdata
DB_USER=postgres
DB_PASSWORD=Mypoly!2025
DB_PORT=5432
EOF
```

### 옵션 3: 로컬 마이그레이션 스크립트에 저장

`scripts/gcp/migrate_data_to_cloud_sql.py` 파일 수정:
```python
CLOUD_DB = {
    'host': '34.50.48.31',  # 공개 IP
    'database': 'mypoly_lawdata',
    'user': 'postgres',
    'password': 'Mypoly!2025',
    'port': 5432
}
```

---

## 3단계: 연결 정보 확인 위치

### Cloud SQL 인스턴스 페이지에서

1. **"연결"** 탭 클릭
   - 또는 인스턴스 개요 페이지에서 "→ 이 인스턴스에 연결" 섹션 확인

2. **확인할 정보:**
   - 연결 이름 (Connection name)
   - 공개 IP 주소 (Public IP address)
   - 포트 번호 (기본값: 5432)

---

## 빠른 확인 방법

현재 화면에서:
1. 왼쪽 메뉴에서 **"연결"** 또는 **"개요"** 클릭
2. **"→ 이 인스턴스에 연결"** 섹션 찾기
3. 연결 이름과 공개 IP 복사

---

## 다음 단계

연결 정보를 확인한 후:
1. 메모장에 저장 (나중에 사용)
2. VM 생성 진행
3. VM에서 Cloud SQL Proxy 설정 시 연결 이름 사용
4. 데이터 마이그레이션 시 공개 IP 사용

