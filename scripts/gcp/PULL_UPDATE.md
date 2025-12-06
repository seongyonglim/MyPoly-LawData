# GCP VM에서 최신 코드 Pull하기

## SSH 접속
```bash
gcloud compute ssh [VM_INSTANCE_NAME] --zone=[ZONE]
```

또는 직접 SSH 키를 사용하는 경우:
```bash
ssh -i ~/.ssh/[YOUR_KEY] [USERNAME]@[VM_EXTERNAL_IP]
```

## 프로젝트 디렉토리로 이동
```bash
cd ~/MyPoly-LawData
# 또는 프로젝트가 다른 위치에 있다면 해당 경로로 이동
```

## 최신 코드 Pull
```bash
git pull origin main
```

## 의존성 업데이트 (필요한 경우)
```bash
# 가상환경 활성화
source .venv/bin/activate  # 또는 python3 -m venv .venv

# requirements.txt 업데이트 확인
pip install -r requirements.txt
```

## 앱 재시작 (Flask 앱이 실행 중인 경우)
```bash
# systemd를 사용하는 경우
sudo systemctl restart mypoly-lawdata

# 또는 직접 실행 중인 경우
# 기존 프로세스 종료 후
python app.py
```

## 변경사항 확인
```bash
git log --oneline -5  # 최근 5개 커밋 확인
git status            # 현재 상태 확인
```

