# VM votes 테이블 최종 동기화 가이드

## 문제 상황
VM의 votes 테이블이 localhost(130,492건)보다 많은 데이터를 가지고 있습니다.

## 해결 방법

### localhost에서 실행 (Windows):

```bash
cd C:\polywave\MyPoly-LawData

# VM의 votes 테이블을 완전히 비우고 localhost 데이터만 복사
python scripts/gcp/reset_vm_votes_exact.py
```

### VM에서 실행:

```bash
cd ~/MyPoly-LawData

# 1. 데이터 수집 프로세스 중지
pkill -f collect_votes_from_date.py
pkill -f collect_bills_from_date.py

# 2. 중복 제거
python3 scripts/gcp/fix_vm_votes_unique_vm.py

# 3. 최종 확인
python3 scripts/gcp/check_vm_db_structure.py
```

## 예상 결과

동기화 완료 후:
- **votes**: 130,492건 (localhost와 동일)

## 주의사항

- `reset_vm_votes_exact.py` 실행 후에도 약간의 차이가 있을 수 있습니다 (중복 삽입 등)
- VM에서 `fix_vm_votes_unique_vm.py`를 실행하여 중복을 제거하세요
- 데이터 수집 프로세스가 실행 중이면 먼저 중지하세요

