# VM에서 git pull 오류 해결

## 문제
```
error: Your local changes to the following files would be overwritten by merge:
        scripts/gcp/start_cloud_sql_proxy.sh
```

## 해결 방법

VM SSH 창에서:

```bash
cd ~/MyPoly-LawData

# 로컬 변경사항 임시 저장
git stash

# GitHub에서 최신 코드 가져오기
git pull origin main

# CSV 파일 확인
ls -lh *.csv

# 가져오기 실행
chmod +x scripts/gcp/import_csv_to_cloud_sql.sh
./scripts/gcp/import_csv_to_cloud_sql.sh
```

---

## 또는 변경사항 버리기 (로컬 수정이 중요하지 않다면)

```bash
cd ~/MyPoly-LawData

# 로컬 변경사항 버리기
git checkout -- scripts/gcp/start_cloud_sql_proxy.sh

# GitHub에서 최신 코드 가져오기
git pull origin main

# CSV 파일 확인 및 가져오기
ls -lh *.csv
chmod +x scripts/gcp/import_csv_to_cloud_sql.sh
./scripts/gcp/import_csv_to_cloud_sql.sh
```

