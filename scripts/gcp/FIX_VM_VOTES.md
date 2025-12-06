# VM votes 테이블 정리 가이드

## 문제 상황
VM의 votes 테이블이 localhost보다 많은 데이터를 가지고 있으며, 데이터 수집 프로세스가 계속 실행 중일 수 있습니다.

## 해결 방법

### 1단계: 데이터 수집 프로세스 중지

VM에서 다음 명령어를 실행하세요:

```bash
cd ~/MyPoly-LawData

# 실행 중인 프로세스 확인
ps aux | grep -E "collect_votes|collect_bills" | grep -v grep

# 프로세스 중지
pkill -f collect_votes_from_date.py
pkill -f collect_bills_from_date.py

# 재확인
ps aux | grep -E "collect_votes|collect_bills" | grep -v grep
```

또는 스크립트 실행:

```bash
chmod +x scripts/gcp/stop_data_collection_vm.sh
./scripts/gcp/stop_data_collection_vm.sh
```

### 2단계: votes 테이블 정리

VM에서 다음 명령어를 실행하세요:

```bash
cd ~/MyPoly-LawData

# 중복 제거
python3 scripts/gcp/fix_vm_votes_unique.py

# localhost에 없는 데이터 삭제
python3 scripts/gcp/remove_vm_votes_duplicates.py

# 최종 확인
python3 scripts/utils/compare_db_structure.py
```

또는 스크립트 실행:

```bash
chmod +x scripts/gcp/clean_vm_votes_final.sh
./scripts/gcp/clean_vm_votes_final.sh
```

### 3단계: 완전 초기화 (필요한 경우)

만약 위 방법으로 해결되지 않으면, VM의 votes 테이블을 완전히 비우고 localhost 데이터만 복사:

```bash
cd ~/MyPoly-LawData

# localhost에서 실행 (Windows)
python scripts/gcp/reset_vm_votes_exact.py
```

## 예상 결과

정리 후:
- localhost votes: 130,492건
- VM votes: 130,492건
- 차이: 0건

## 주의사항

- 데이터 수집 프로세스를 중지한 후 정리 작업을 진행하세요.
- 정리 중에는 데이터 수집을 시작하지 마세요.
- 정리 완료 후 필요시 데이터 수집을 다시 시작할 수 있습니다.

