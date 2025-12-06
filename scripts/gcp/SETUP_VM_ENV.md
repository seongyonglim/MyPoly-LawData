# GCP VM 환경 설정 가이드

## 방법 1: 시스템 Python 사용 (추천 - VM에서)
```bash
cd ~/MyPoly-LawData

# pip 업그레이드 (필요한 경우)
python3 -m pip install --upgrade pip --user

# 의존성 설치 (사용자 레벨)
python3 -m pip install --user -r requirements.txt
```

## 방법 2: 기존 가상환경 사용
```bash
cd ~/MyPoly-LawData

# 기존 가상환경이 있다면 활성화
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip install -r requirements.txt
fi
```

## 방법 3: 새 가상환경 생성 (필요한 경우만)
```bash
cd ~/MyPoly-LawData

# Python 가상환경 패키지 설치 (필요한 경우만)
sudo apt update
sudo apt install -y python3.10-venv python3-pip

# 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate

# 의존성 설치
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

## 4. 앱 실행 테스트
```bash
# 시스템 Python 사용 시
python3 app.py

# 가상환경 사용 시
source .venv/bin/activate
python app.py

# 또는 systemd 서비스로 실행
sudo systemctl start mypoly-lawdata
sudo systemctl status mypoly-lawdata
```

## Git Pull 후 빠른 업데이트 (추천)
```bash
cd ~/MyPoly-LawData

# 최신 코드 가져오기
git pull origin main

# 의존성만 업데이트 (시스템 Python 사용)
python3 -m pip install --user --upgrade -r requirements.txt

# 또는 가상환경 사용 시
source .venv/bin/activate
pip install --upgrade -r requirements.txt

# 앱 재시작
sudo systemctl restart mypoly-lawdata
```

