# GCP VM 환경 설정 가이드

## 1. Python 가상환경 패키지 설치
```bash
sudo apt update
sudo apt install -y python3.10-venv python3-pip
```

## 2. 가상환경 생성 및 활성화
```bash
cd ~/MyPoly-LawData

# 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate
```

## 3. 의존성 설치
```bash
# pip 업그레이드
pip install --upgrade pip

# requirements.txt 설치
pip install -r requirements.txt
```

## 4. .env 파일 확인
```bash
# .env 파일이 있는지 확인
ls -la .env

# 없으면 생성 (로컬에서 복사하거나 수동으로 생성)
# 필요한 환경 변수:
# - LOCAL_DB_HOST, LOCAL_DB_NAME, LOCAL_DB_USER, LOCAL_DB_PASSWORD, LOCAL_DB_PORT
# - DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT (Cloud SQL용)
# - BILL_SERVICE_KEY
# - ASSEMBLY_SERVICE_KEY
# - GEMINI_API_KEY
```

## 5. 앱 실행 테스트
```bash
# 가상환경 활성화 상태에서
python app.py

# 또는 systemd 서비스로 실행
sudo systemctl start mypoly-lawdata
sudo systemctl status mypoly-lawdata
```

## 전체 설정 스크립트 (한 번에 실행)
```bash
cd ~/MyPoly-LawData

# 패키지 설치
sudo apt update
sudo apt install -y python3.10-venv python3-pip

# 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate

# pip 업그레이드
pip install --upgrade pip

# 의존성 설치
pip install -r requirements.txt

# 확인
python --version
pip list
```

