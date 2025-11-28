# Render.com 배포 오류 수정

## 🔴 발생한 오류

```
ImportError: /opt/render/project/src/.venv/lib/python3.13/site-packages/psycopg2/_psycopg.cpython-313-x86_64-linux-gnu.so: undefined symbol: _PyInterpreterState_Get
```

## 🔍 원인

- Render.com이 Python 3.13.4를 자동으로 사용
- `psycopg2-binary==2.9.9`가 Python 3.13과 완전히 호환되지 않음
- Python 3.13은 매우 최신 버전이라 일부 패키지와 호환성 문제 발생

## ✅ 해결 방법

### 1. Python 버전 고정

`runtime.txt` 파일을 생성하여 Python 3.12로 고정:

```
python-3.12.7
```

### 2. psycopg2-binary 버전 업데이트

`requirements.txt`에서 `psycopg2-binary`를 최신 버전으로 업데이트:

```
psycopg2-binary==2.9.10
```

## 📋 수정된 파일

1. ✅ `runtime.txt` 생성 (Python 3.12.7 지정)
2. ✅ `requirements.txt` 업데이트 (psycopg2-binary 2.9.10)

## 🚀 다음 단계

1. **코드가 GitHub에 푸시됨** ✅
2. **Render.com에서 자동으로 재배포 시작됨** (또는 수동으로 재배포)
3. **배포 완료 대기** (약 5-10분)

## 🔧 Render.com에서 수동 재배포

만약 자동 재배포가 시작되지 않으면:

1. Render Dashboard → Web Service 클릭
2. "Manual Deploy" → "Deploy latest commit" 클릭

## ✅ 완료!

이제 Python 3.12를 사용하므로 `psycopg2-binary`와 호환성 문제가 해결됩니다.

---

**배포가 완료되면 알려주세요!** 🚀


