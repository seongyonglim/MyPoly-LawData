# VM 데이터 동기화 가이드

## 개요
localhost와 VM의 데이터를 동기화하기 위한 단계별 가이드입니다.

## 사전 준비

### 1. 데이터 수집 프로세스 중지

VM에서 실행 중인 데이터 수집 프로세스를 먼저 중지해야 합니다:

```bash
cd ~/MyPoly-LawData

# 실행 중인 프로세스 확인
ps aux | grep -E "collect_votes|collect_bills" | grep -v grep

# 프로세스 중지
pkill -f collect_votes_from_date.py
pkill -f collect_bills_from_date.py

# 재확인 (아무것도 나오지 않으면 정상)
ps aux | grep -E "collect_votes|collect_bills" | grep -v grep
```

또는 스크립트 사용:

```bash
chmod +x scripts/gcp/stop_data_collection_vm.sh
./scripts/gcp/stop_data_collection_vm.sh
```

## 동기화 단계

### 1단계: DB 구조 동기화

VM의 DB 구조를 localhost와 동일하게 맞춥니다:

```bash
cd ~/MyPoly-LawData

# localhost에서 실행 (Windows)
python scripts/gcp/fix_vm_db_structure.py
```

이 스크립트는:
- `bills` 테이블에 `headline` 컬럼 추가
- 불필요한 `member_id_mapping` 테이블 삭제

### 2단계: headline 데이터 동기화

localhost의 headline 데이터를 VM으로 동기화:

```bash
# localhost에서 실행 (Windows)
python scripts/gcp/sync_headline_data.py
```

### 3단계: 인덱스 동기화

localhost의 인덱스를 VM에 추가:

```bash
# localhost에서 실행 (Windows)
python scripts/gcp/sync_indexes.py
```

### 4단계: votes 테이블 정리

VM의 votes 테이블에서 중복 데이터를 제거하고 localhost와 동일하게 맞춥니다:

```bash
cd ~/MyPoly-LawData

# 중복 제거
python3 scripts/gcp/fix_vm_votes_unique.py

# localhost에 없는 데이터 삭제
python3 scripts/gcp/remove_vm_votes_duplicates.py

# 최종 확인
python3 scripts/utils/compare_db_structure.py
```

또는 스크립트 사용:

```bash
chmod +x scripts/gcp/clean_vm_votes_final.sh
./scripts/gcp/clean_vm_votes_final.sh
```

### 5단계: 완전 초기화 (필요한 경우)

만약 위 방법으로 해결되지 않으면, VM의 votes 테이블을 완전히 비우고 localhost 데이터만 복사:

```bash
# localhost에서 실행 (Windows)
python scripts/gcp/reset_vm_votes_exact.py
```

그 다음 VM에서:

```bash
cd ~/MyPoly-LawData

# 중복 제거
python3 scripts/gcp/fix_vm_votes_unique.py

# localhost에 없는 데이터 삭제
python3 scripts/gcp/remove_vm_votes_duplicates.py
```

## 전체 동기화 (한 번에 실행)

### localhost에서 (Windows):

```bash
# 1. DB 구조 수정
python scripts/gcp/fix_vm_db_structure.py

# 2. headline 데이터 동기화
python scripts/gcp/sync_headline_data.py

# 3. 인덱스 동기화
python scripts/gcp/sync_indexes.py
```

### VM에서:

```bash
cd ~/MyPoly-LawData

# 1. 데이터 수집 프로세스 중지
pkill -f collect_votes_from_date.py
pkill -f collect_bills_from_date.py

# 2. votes 테이블 정리
python3 scripts/gcp/fix_vm_votes_unique.py
python3 scripts/gcp/remove_vm_votes_duplicates.py

# 3. 최종 확인
python3 scripts/utils/compare_db_structure.py
```

## 예상 결과

동기화 완료 후:
- **테이블 수**: 8개 (일치)
- **bills**: 7,850건 (일치)
- **assembly_members**: 306건 (일치)
- **votes**: 130,492건 (일치)
- **headline 데이터**: 7,519건 (일치)

## 문제 해결

### 데이터가 계속 증가하는 경우

VM에서 데이터 수집 프로세스가 실행 중일 수 있습니다:

```bash
# 프로세스 확인
ps aux | grep -E "collect_votes|collect_bills" | grep -v grep

# 강제 종료
pkill -9 -f collect_votes_from_date.py
pkill -9 -f collect_bills_from_date.py
```

### votes 데이터가 여전히 다른 경우

완전 초기화를 시도하세요:

```bash
# localhost에서
python scripts/gcp/reset_vm_votes_exact.py

# VM에서
python3 scripts/gcp/fix_vm_votes_unique.py
python3 scripts/gcp/remove_vm_votes_duplicates.py
```

## 참고 문서

- `FIX_VM_VOTES.md`: votes 테이블 정리 상세 가이드
- `MIGRATION_GUIDE.md`: 전체 마이그레이션 가이드
- `RESTART_APP.md`: 앱 재시작 가이드

