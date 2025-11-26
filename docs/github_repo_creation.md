# GitHub 레포지토리 생성 가이드

## 1단계: GitHub에서 레포지토리 생성

1. **GitHub.com 접속**: https://github.com/seongyonglim
2. **우측 상단 "+" 버튼 클릭 → "New repository"**
3. **레포지토리 설정:**
   - Repository name: `MyPoly-LawData`
   - Description: `2025년 의안 표결 결과 웹 대시보드`
   - Visibility: **Public** 또는 **Private** (선택)
   - ⚠️ **"Initialize this repository with a README" 체크 해제** (이미 README가 있으므로)
   - ⚠️ **"Add .gitignore" 체크 해제** (이미 .gitignore가 있으므로)
   - ⚠️ **"Choose a license" 선택 안 함**
4. **"Create repository" 클릭**

## 2단계: 코드 푸시

레포지토리를 생성한 후 아래 명령어를 실행하세요:

```bash
git push -u origin main
```

또는 레포지토리가 아직 생성되지 않았다면, 먼저 위의 1단계를 완료하세요.

## 완료!

레포지토리 생성 후 푸시가 완료되면, Render.com에서 이 레포지토리를 연결하여 배포할 수 있습니다.

