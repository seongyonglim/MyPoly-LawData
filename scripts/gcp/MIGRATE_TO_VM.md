# VM으로 데이터 이관 가이드

## 전체 프로세스

### 1단계: VM에서 최신 코드 Pull

```bash
cd ~/MyPoly-LawData
git pull origin main
```

### 2단계: localhost에서 데이터 이관

**localhost에서 실행:**

```bash
cd ~/MyPoly-LawData
python scripts/gcp/migrate_direct_public_ip.py
```

이 스크립트는:
- VM의 모든 테이블을 TRUNCATE
- localhost의 데이터를 VM으로 복사
- bills, votes, assembly_members 등 모든 테이블 이관

### 3단계: VM 데이터 품질 업데이트

**localhost에서 실행:**

```bash
cd ~/MyPoly-LawData
python scripts/gcp/migrate_to_vm_complete.py
```

이 스크립트는:
- link_url 업데이트 (billId로 생성)
- proposer_name 업데이트 (의안 제목에서 추출)
- 최종 데이터 확인

### 4단계: VM 앱 재시작

**VM에서 실행:**

```bash
cd ~/MyPoly-LawData
# 실행 중인 앱 종료
pkill -f "python.*app.py"

# 새로 시작
nohup python3 app.py > app.log 2>&1 &

# 로그 확인
tail -f app.log
```

## 주의사항

1. **데이터 수집 프로세스 중지**: VM에서 데이터 수집이 실행 중이면 먼저 중지하세요
   ```bash
   pkill -f collect_votes_from_date.py
   pkill -f collect_bills_from_date.py
   ```

2. **환경 변수 확인**: `.env` 파일에 다음이 설정되어 있어야 합니다:
   - `LOCAL_DB_HOST`, `LOCAL_DB_NAME`, `LOCAL_DB_USER`, `LOCAL_DB_PASSWORD`, `LOCAL_DB_PORT`
   - `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`

3. **데이터 일치 확인**: 이관 후 데이터 개수가 일치하는지 확인하세요.

## 문제 해결

### 데이터가 일치하지 않는 경우

1. VM의 votes 테이블 정리:
   ```bash
   # VM에서 실행
   python3 scripts/gcp/fix_vm_votes_unique_vm.py
   python3 scripts/gcp/remove_vm_votes_duplicates_vm.py
   ```

2. 다시 이관:
   ```bash
   # localhost에서 실행
   python scripts/gcp/migrate_direct_public_ip.py
   ```

### Git 충돌 발생 시

VM에서:
```bash
cd ~/MyPoly-LawData
git fetch origin
git reset --hard origin/main
git clean -fd
```

