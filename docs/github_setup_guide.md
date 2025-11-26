# GitHub 레포지토리 생성 및 업로드 가이드

## 1단계: GitHub에서 새 레포지토리 생성

1. **GitHub.com 접속**: https://github.com
2. **우측 상단 "+" 버튼 클릭 → "New repository"**
3. **레포지토리 설정:**
   - Repository name: `MyPoly-LawData` (또는 원하는 이름)
   - Description: `2025년 의안 표결 결과 웹 대시보드`
   - Visibility: **Public** 또는 **Private** (선택)
   - ⚠️ **"Initialize this repository with a README" 체크 해제** (이미 README가 있으므로)
   - ⚠️ **"Add .gitignore" 체크 해제** (이미 .gitignore가 있으므로)
   - ⚠️ **"Choose a license" 선택 안 함**
4. **"Create repository" 클릭**

## 2단계: 로컬 저장소와 GitHub 연결

레포지토리를 생성하면 GitHub에서 다음 명령어를 제공합니다:

```bash
git remote add origin https://github.com/YOUR_USERNAME/MyPoly-LawData.git
git branch -M main
git push -u origin main
```

**또는 SSH를 사용하는 경우:**
```bash
git remote add origin git@github.com:YOUR_USERNAME/MyPoly-LawData.git
git branch -M main
git push -u origin main
```

## 3단계: 코드 푸시

위 명령어를 실행하면 코드가 GitHub에 업로드됩니다.

## 완료!

이제 GitHub에서 코드를 확인할 수 있고, Render.com에서 이 레포지토리를 연결하여 배포할 수 있습니다.

