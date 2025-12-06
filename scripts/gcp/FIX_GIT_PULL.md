# GCP VM Git Pull 충돌 해결

## 문제
로컬에서 삭제된 파일들이 VM에 남아있어서 git pull이 실패하는 경우

## 해결 방법

### 방법 1: 삭제된 파일들을 강제로 제거하고 Pull (추천)
```bash
cd ~/MyPoly-LawData

# 삭제된 파일들 제거
rm -f scripts/db/update_member_ids_vm.sh
rm -f scripts/gcp/check_and_fix_env.sh
rm -f scripts/gcp/create_systemd_services.sh
rm -f scripts/gcp/create_tables_in_cloud_sql.sh
rm -f scripts/gcp/fix_vm_git_and_setup.sh
rm -f scripts/gcp/manage_services.sh
rm -f scripts/gcp/setup_cloud_sql_complete.sh
rm -f scripts/gcp/setup_cloud_sql_proxy.sh
rm -f scripts/gcp/setup_env.sh
rm -f scripts/gcp/setup_vm.sh
rm -f scripts/gcp/setup_vm_complete.sh
rm -f scripts/gcp/start_app.sh
rm -f scripts/gcp/start_cloud_sql_proxy.sh

# 변경사항 커밋
git add -A
git commit -m "Remove deleted files before pull"

# Pull
git pull origin main
```

### 방법 2: Stash 후 Pull
```bash
cd ~/MyPoly-LawData

# 로컬 변경사항 임시 저장
git stash

# Pull
git pull origin main

# Stash된 변경사항 확인 (필요한 경우)
git stash list
```

### 방법 3: 강제로 원격 상태로 리셋 (주의: 로컬 변경사항 모두 삭제)
```bash
cd ~/MyPoly-LawData

# 원격 저장소 상태로 완전히 리셋
git fetch origin
git reset --hard origin/main

# 또는
git clean -fd
git pull origin main
```

## 가상환경 설정 (없는 경우)
```bash
cd ~/MyPoly-LawData

# 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

