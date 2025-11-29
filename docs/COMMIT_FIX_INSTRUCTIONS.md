# Commit Message Fix Instructions

## 문제

PowerShell에서 한글로 커밋 메시지를 작성할 때 인코딩 문제로 깨진 메시지가 Git 히스토리에 남아있습니다.

## 해결 방법

`git rebase -i`를 사용하여 각 커밋의 메시지를 영어로 수정해야 합니다.

## 단계별 가이드

### 1단계: Rebase 시작

```bash
git rebase -i HEAD~35
```

이 명령어는 최근 35개 커밋을 편집할 수 있는 대화형 모드를 엽니다.

### 2단계: 커밋 메시지 수정

편집기가 열리면, 각 깨진 커밋에 대해:

1. `pick`을 `reword` (또는 `r`)로 변경
2. 파일 저장 후 닫기
3. 각 커밋에 대해 편집기가 다시 열리면, `COMMIT_MESSAGE_FIXES.md`에서 해당 커밋의 영어 메시지를 찾아서 붙여넣기
4. 저장 후 닫기
5. 다음 커밋으로 진행

### 3단계: Force Push

모든 커밋 메시지 수정이 완료되면:

```bash
git push --force-with-lease origin main
```

**⚠️ 주의사항**:
- 히스토리를 다시 작성하므로 다른 사람이 작업 중이면 문제가 될 수 있습니다
- 백업을 권장합니다
- `--force-with-lease`는 안전한 force push 방법입니다

## 빠른 참조

`COMMIT_MESSAGE_FIXES.md` 파일에 모든 커밋 해시와 영어 메시지가 매핑되어 있습니다.

## 예시

예를 들어, `8dd146d` 커밋을 수정하려면:

1. Rebase 편집기에서: `reword 8dd146d Add final cleanup verification report`
2. 커밋 메시지 편집기에서: `Add final cleanup verification report` 입력

이 과정을 모든 깨진 커밋에 대해 반복합니다.

