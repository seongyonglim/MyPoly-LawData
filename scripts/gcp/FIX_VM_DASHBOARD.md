# VM 대시보드 데이터 불일치 해결

## 문제
VM 대시보드에서 원문내용이 100%로 표시되지만, 실제로는 95.8% (7,519/7,850)여야 함.

## 원인
VM의 `app.py`가 아직 업데이트되지 않았거나, Flask 캐시가 남아있을 수 있습니다.

## 해결 방법

### 1단계: VM에서 최신 코드 Pull

```bash
cd ~/MyPoly-LawData
git pull origin main
```

### 2단계: 앱 재시작 (캐시 클리어)

```bash
# 실행 중인 앱 종료
pkill -f "python.*app.py"

# 잠시 대기
sleep 2

# 새로 시작
nohup python3 app.py > app.log 2>&1 &

# 로그 확인
tail -f app.log
```

### 3단계: 브라우저 캐시 클리어

브라우저에서 `Ctrl+Shift+R` (또는 `Cmd+Shift+R`)로 강력 새로고침

### 4단계: 확인

`http://VM_IP:5000/bills/quality` 페이지에서 원문내용이 95.8% (7,519/7,850)로 표시되는지 확인

## 참고

- Flask-Caching의 기본 타임아웃은 5분입니다 (`@cache.cached(timeout=300)`)
- 앱 재시작 후에도 캐시가 남아있을 수 있으므로, 브라우저 캐시도 클리어하세요.

