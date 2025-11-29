# 연결 시간 초과 오류 해결

## 문제
`ERR_CONNECTION_TIMED_OUT` - VM의 포트 5000에 접속할 수 없음

## 가능한 원인

1. **앱이 실행되지 않음**
2. **방화벽 규칙이 포트 5000을 허용하지 않음**
3. **앱이 localhost에만 바인딩됨**

---

## 해결 방법

### 1단계: 앱 실행 확인

VM SSH 창에서:

```bash
# 앱이 실행 중인지 확인
ps aux | grep "python app.py"

# 실행 중이 아니면 시작
cd ~/MyPoly-LawData
source venv/bin/activate
export $(cat .env | xargs)
python app.py
```

**중요**: 앱이 `0.0.0.0:5000`에서 리스닝하는지 확인해야 합니다.

---

### 2단계: 방화벽 규칙 확인 및 추가

#### GCP 콘솔에서:

1. **VPC 네트워크** → **방화벽** 검색
2. **"방화벽 규칙 만들기"** 클릭
3. 설정:
   - **이름**: `allow-flask-5000`
   - **대상**: `모든 인스턴스`
   - **소스 IP 범위**: `0.0.0.0/0`
   - **프로토콜 및 포트**: 
     - **TCP** 선택
     - **포트**: `5000` 입력
4. **"만들기"** 클릭

---

### 3단계: app.py 확인

앱이 `0.0.0.0`에서 리스닝하는지 확인:

```python
# app.py 마지막 부분
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

`host='0.0.0.0'`이어야 외부에서 접속 가능합니다.

---

### 4단계: 앱 재시작

방화벽 규칙을 추가한 후:

```bash
# 앱 재시작
cd ~/MyPoly-LawData
source venv/bin/activate
export $(cat .env | xargs)
python app.py
```

출력에서 다음을 확인:
```
* Running on all addresses (0.0.0.0)
* Running on http://0.0.0.0:5000
```

---

## 빠른 확인 명령어

VM SSH 창에서:

```bash
# 1. 앱 실행 확인
ps aux | grep "python app.py"

# 2. 포트 5000 리스닝 확인
sudo netstat -tlnp | grep 5000
# 또는
sudo ss -tlnp | grep 5000

# 3. 방화벽 규칙 확인 (GCP 콘솔에서)
```

---

## 체크리스트

- [ ] 앱이 실행 중인가?
- [ ] 앱이 `0.0.0.0:5000`에서 리스닝하는가?
- [ ] 방화벽 규칙이 포트 5000을 허용하는가?
- [ ] VM의 공개 IP가 올바른가?

