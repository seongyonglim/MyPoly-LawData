# GitHub에서 CSV 파일 다운로드 (VM에서)

## 빠른 방법: GitHub에서 직접 다운로드

VM SSH 창에서 다음 명령어를 실행하세요:

```bash
cd ~/MyPoly-LawData

# GitHub에서 최신 코드 가져오기 (CSV 파일 포함)
git pull origin main

# CSV 파일 확인
ls -lh *.csv

# 파일이 있으면 바로 가져오기 실행
chmod +x scripts/gcp/import_csv_to_cloud_sql.sh
./scripts/gcp/import_csv_to_cloud_sql.sh
```

---

## 또는 직접 다운로드

```bash
cd ~/MyPoly-LawData

# GitHub에서 CSV 파일 직접 다운로드
wget https://raw.githubusercontent.com/seongyonglim/MyPoly-LawData/main/bills.csv
wget https://raw.githubusercontent.com/seongyonglim/MyPoly-LawData/main/assembly_members.csv
wget https://raw.githubusercontent.com/seongyonglim/MyPoly-LawData/main/votes.csv
wget https://raw.githubusercontent.com/seongyonglim/MyPoly-LawData/main/proc_stage_mapping.csv

# 가져오기 실행
chmod +x scripts/gcp/import_csv_to_cloud_sql.sh
./scripts/gcp/import_csv_to_cloud_sql.sh
```

---

## 가장 빠른 방법 (한 번에)

```bash
cd ~/MyPoly-LawData && git pull origin main && chmod +x scripts/gcp/import_csv_to_cloud_sql.sh && ./scripts/gcp/import_csv_to_cloud_sql.sh
```

