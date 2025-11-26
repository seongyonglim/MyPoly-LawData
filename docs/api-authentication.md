# API 인증키 관리

## 인증키 목록

### 1. 공공데이터포털 인증키 (의안정보 API)
- **용도**: 의안정보 통합 API 호출
- **API**: `https://apis.data.go.kr/9710000/BillInfoService2/getBillInfoList`
- **환경변수**: `BILL_SERVICE_KEY`
- **기본값**: `MiXjfqnyhsYErA%2FKEzOyLNFwxzbd%2B7VE0k2%2FeVml32gs8WjdeVCOQb06tgG5UaQ7u5bb74Hibe8WkwopNsXceA%3D%3D`
- **인코딩**: URL 인코딩된 형태 (디코딩 필요)

### 2. 열린국회정보 인증키 (표결정보, 의원정보 API)
- **용도**: 국회의원 본회의 표결정보 API, 국회의원 정보 통합 API 호출
- **API들**:
  - `https://open.assembly.go.kr/portal/openapi/nojepdqqaweusdfbi` (표결정보)
  - `https://open.assembly.go.kr/portal/openapi/ALLNAMEMBER` (의원정보)
- **환경변수**: `ASSEMBLY_SERVICE_KEY`
- **값**: `5e85053066dd409b81ed7de0f47bbcab`
- **활용용도**: 공익·투표·통계 앱(사이드 프로젝트) 개발
- **발급일**: 2025-07-21
- **호출건수**: 58건 (2025-01-XX 기준)
- **상태**: 정상

## 인증키 사용 방법

### 환경변수 설정 (권장)

#### Windows (PowerShell)
```powershell
$env:BILL_SERVICE_KEY="MiXjfqnyhsYErA%2FKEzOyLNFwxzbd%2B7VE0k2%2FeVml32gs8WjdeVCOQb06tgG5UaQ7u5bb74Hibe8WkwopNsXceA%3D%3D"
$env:ASSEMBLY_SERVICE_KEY="5e85053066dd409b81ed7de0f47bbcab"
```

#### Linux/Mac
```bash
export BILL_SERVICE_KEY="MiXjfqnyhsYErA%2FKEzOyLNFwxzbd%2B7VE0k2%2FeVml32gs8WjdeVCOQb06tgG5UaQ7u5bb74Hibe8WkwopNsXceA%3D%3D"
export ASSEMBLY_SERVICE_KEY="5e85053066dd409b81ed7de0f47bbcab"
```

### 코드에서 사용

```python
import os
from urllib.parse import unquote

# 공공데이터포털 인증키 (URL 디코딩 필요)
ENCODED_SERVICE_KEY = os.environ.get(
    "BILL_SERVICE_KEY",
    "MiXjfqnyhsYErA%2FKEzOyLNFwxzbd%2B7VE0k2%2FeVml32gs8WjdeVCOQb06tgG5UaQ7u5bb74Hibe8WkwopNsXceA%3D%3D"
)
SERVICE_KEY = unquote(ENCODED_SERVICE_KEY)

# 열린국회정보 인증키
ASSEMBLY_KEY = os.environ.get(
    "ASSEMBLY_SERVICE_KEY",
    "5e85053066dd409b81ed7de0f47bbcab"
)
```

## 보안 주의사항

1. **환경변수 사용 권장**: 코드에 직접 하드코딩하지 않기
2. **Git에 커밋 금지**: `.gitignore`에 인증키 파일 추가
3. **설정 파일 사용 시**: `.env` 파일 사용 (python-dotenv 등)
4. **프로덕션 환경**: 환경변수 또는 시크릿 관리 시스템 사용

## 인증키 발급 내역

### 열린국회정보 인증키
- **인증키**: `5e85053066dd409b81ed7de0f47bbcab`
- **활용용도**: 공익·투표·통계 앱(사이드 프로젝트) 개발
- **발급일**: 2025-07-21
- **호출건수**: 58건 (2025-01-XX 기준)
- **상태**: 정상
- **요청 제한**: 제한없음

## API 호출 제한

### 공공데이터포털 API
- **요청 제한**: 문서에 명시되지 않음 (기본적으로 일일 제한 있음)
- **주의**: 과도한 호출 시 일시적 제한 가능

### 열린국회정보 API
- **요청 제한**: 제한없음 (문서 기준)
- **주의**: 과도한 호출 시 서버 부하 고려

## 에러 코드

### 열린국회정보 API 에러 코드
- `ERROR-300`: 필수 값이 누락되어 있습니다
- `ERROR-290`: 인증키가 유효하지 않습니다
- `ERROR-337`: 일별 트래픽 제한을 넘은 호출입니다
- `ERROR-500`: 서버 오류입니다
- `INFO-000`: 정상 처리되었습니다
- `INFO-200`: 해당하는 데이터가 없습니다

## 참고
- 공공데이터포털: https://www.data.go.kr/
- 열린국회정보: https://open.assembly.go.kr/

