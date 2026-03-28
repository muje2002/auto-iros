# auto-iros - 등기부등본 자동 발급 프로그램

인터넷 등기소(iros.go.kr) 등기부등본을 자동으로 발급받아 PDF로 저장하는 프로그램입니다.
웹 브라우저에서 쉽게 사용할 수 있습니다.

## 주요 기능

- **단건 조회** - 주소 또는 고유번호로 등기부등본 1건 조회
- **일괄 조회** - 엑셀 파일로 여러 건 한번에 조회 (실시간 진행률)
- **주소 검색** - 주소로 부동산 검색하여 고유번호 확인
- **PDF 다운로드** - 등기부등본 PDF 자동 저장
- **결과 엑셀** - 조회 결과를 엑셀로 내보내기
- **다크모드** - 밝은/어두운 화면 전환 지원

---

## Windows 설치 가이드 (처음부터 따라하기)

### 1단계: Python 설치

이 프로그램은 Python이 필요합니다.

1. 웹 브라우저에서 [python.org/downloads](https://www.python.org/downloads/) 접속
2. **"Download Python 3.11"** (또는 최신 버전) 버튼 클릭
3. 다운로드된 설치 파일 실행
4. **중요!** 설치 화면 하단의 **"Add Python to PATH"** 체크박스를 반드시 체크
5. "Install Now" 클릭하여 설치 완료

설치 확인:
- `Win + R` 키를 누르고 `cmd` 입력 후 Enter
- 열린 검은 창(명령 프롬프트)에 다음을 입력:
```
python --version
```
- `Python 3.11.x` 같은 버전이 표시되면 성공

### 2단계: 프로그램 다운로드

**방법 A: ZIP 다운로드 (간단)**

1. 웹 브라우저에서 [github.com/muje2002/auto-iros](https://github.com/muje2002/auto-iros) 접속
2. 초록색 **"Code"** 버튼 클릭
3. **"Download ZIP"** 클릭
4. 다운로드된 ZIP 파일을 원하는 폴더에 압축 해제
   - 예: `C:\auto-iros`

**방법 B: Git 사용 (개발자)**

```
git clone https://github.com/muje2002/auto-iros.git
cd auto-iros
```

### 3단계: 프로그램 폴더로 이동

명령 프롬프트(`Win + R` → `cmd` → Enter)에서:
```
cd C:\auto-iros
```
> 압축 해제한 폴더 경로에 맞게 변경하세요.
> ZIP 다운로드 시 `C:\auto-iros-main` 일 수 있습니다.

### 4단계: 필요한 패키지 설치

같은 명령 프롬프트에서 다음을 입력:
```
pip install -r requirements.txt
```
- 여러 줄의 설치 진행 메시지가 나옵니다
- `Successfully installed ...` 메시지가 나오면 완료

### 5단계: CODEF API 키 발급

이 프로그램은 CODEF API를 사용합니다. API 키가 필요합니다.

1. [developer.codef.io](https://developer.codef.io) 접속하여 회원가입
2. 로그인 후 **"마이페이지"** → **"API 키 관리"**
3. 다음 3가지를 메모:
   - **Client ID** (예: `d88c85f7-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
   - **Client Secret** (예: `d7fe4279-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
   - **RSA 공개키** (긴 영문+숫자 문자열)

### 6단계: 환경 설정 파일 만들기

1. 프로그램 폴더에서 `.env.example` 파일을 찾아 복사
2. 복사한 파일 이름을 `.env` 로 변경
   - 윈도우 탐색기에서 `.env.example` 파일 → 우클릭 → 복사 → 붙여넣기 → 이름 변경
   - 명령 프롬프트에서: `copy .env.example .env`
3. `.env` 파일을 메모장으로 열기 (우클릭 → 연결 프로그램 → 메모장)
4. 아래 내용을 수정:

```
# 5단계에서 발급받은 정보 입력
CODEF_CLIENT_ID=여기에_Client_ID_붙여넣기
CODEF_CLIENT_SECRET=여기에_Client_Secret_붙여넣기
CODEF_PUBLIC_KEY=여기에_RSA_공개키_붙여넣기

# 환경 설정 (테스트: demo, 실제 사용: production)
CODEF_ENV=demo

# 본인 전화번호 (하이픈 없이)
CODEF_PHONE_NO=01012345678

# 4자리 비밀번호 (자유롭게 설정)
CODEF_PASSWORD=1234

# PDF 저장 폴더
OUTPUT_DIR=./output
```

5. 저장 후 메모장 닫기

### 7단계: 프로그램 실행

명령 프롬프트에서:
```
python -m uvicorn app:app --reload
```

아래와 비슷한 메시지가 나오면 성공:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
```

### 8단계: 웹 브라우저에서 사용

1. 웹 브라우저(크롬, 엣지 등)를 열고 주소창에 입력:
```
http://localhost:8000
```

2. 메인 화면이 나타나면 성공!

| 메뉴 | 기능 |
|------|------|
| **단건 조회** | 주소 입력 → 등기부등본 1건 조회 → PDF 다운로드 |
| **일괄 조회** | 엑셀 파일 업로드 → 여러 건 한번에 조회 |
| **주소 검색** | 주소로 부동산 검색 (고유번호 확인용) |
| **템플릿** | 일괄 조회용 엑셀 양식 다운로드 |

### 프로그램 종료

명령 프롬프트에서 `Ctrl + C` 를 누르면 종료됩니다.

---

## 사용 예시

### 단건 조회
1. 메인 화면에서 "단건 조회" 클릭
2. "조회구분"에서 "간편검색" 선택
3. "검색어" 에 주소 입력 (예: `서울특별시 강남구 테헤란로 152`)
4. "발급유형" 선택
5. "조회하기" 클릭
6. 결과가 나오면 "PDF 다운로드" 클릭

### 일괄 조회
1. 메인 화면에서 "템플릿 다운로드" 클릭하여 엑셀 양식 받기
2. 엑셀 파일에 조회할 주소들을 입력하고 저장
3. "일괄 조회" 페이지에서 엑셀 파일 업로드
4. 미리보기 확인 후 "전체 실행" 클릭
5. 진행률 바가 완료되면 결과에서 개별 PDF 다운로드

---

## 문제 해결

### "python을 찾을 수 없습니다"
→ 1단계에서 **"Add Python to PATH"** 를 체크하지 않은 경우입니다.
→ Python을 삭제 후 다시 설치하면서 체크해주세요.

### "pip를 찾을 수 없습니다"
→ `python -m pip install -r requirements.txt` 로 시도해보세요.

### ".env 파일을 만들 수 없습니다"
→ 윈도우 탐색기에서 "파일 확장명 표시"를 켜야 합니다.
→ 탐색기 → 보기 → "파일 확장명" 체크

### "CODEF_CLIENT_ID 환경변수를 설정하세요"
→ 6단계의 `.env` 파일이 올바르게 작성되었는지 확인하세요.
→ `.env` 파일이 프로그램 폴더 최상위에 있어야 합니다.

### "CODEF_PUBLIC_KEY가 설정되지 않았습니다"
→ `.env` 파일에 CODEF 개발자센터에서 발급받은 RSA 공개키를 입력하세요.

### "전자민원캐시가 필요합니다"
→ 발급/열람 시 결제가 필요합니다. `.env` 파일에 `EPREPAY_NO`와 `EPREPAY_PASS`를 설정하세요.
→ 결제 없이 테스트하려면 발급유형을 "고유번호조회"로 선택하세요.

### 웹 페이지가 열리지 않습니다
→ 명령 프롬프트에 에러 메시지가 없는지 확인하세요.
→ `http://localhost:8000` 을 정확히 입력했는지 확인하세요.
→ 다른 프로그램이 8000번 포트를 사용 중일 수 있습니다: `python -m uvicorn app:app --port 8080` 으로 포트를 변경해보세요.

---

## 주의사항

- **대법원 점검시간**: 매월 1째/3째 목요일 21:00 ~ 금요일 06:00 에는 조회가 안 됩니다
- **과도한 조회 금지**: 짧은 시간에 너무 많이 조회하면 IP가 차단될 수 있습니다
- **발급 비용**: 실제 등기부등본 발급(production 환경)은 건당 요금이 발생합니다

## API 환경 설명

| 환경 | `.env` 설정 | 설명 |
|------|-------------|------|
| 데모 | `CODEF_ENV=demo` | 개발/테스트용 (무료, 테스트 데이터) |
| 샌드박스 | `CODEF_ENV=sandbox` | 고정 응답 테스트 (무료) |
| 운영 | `CODEF_ENV=production` | 실제 등기부등본 발급 (**유료**) |

---

## 개발자 정보

### CLI 사용법

웹 UI 외에 명령줄에서도 사용 가능합니다:

```bash
python main.py template                    # 엑셀 템플릿 생성
python main.py single -a "테헤란로 123"     # 단건 조회
python main.py search "테헤란로"            # 주소 검색
python main.py batch -f 요청목록.xlsx -y    # 일괄 조회
```

### 테스트 실행

```bash
python -m ruff check .                                    # 린트
python -m mypy src/ app.py --ignore-missing-imports       # 타입 체크
python -m pytest tests/ -v                                # 테스트 (86개)
```

### Docker

```bash
docker compose up
```

## 참고

- [CODEF 개발자 가이드](https://developer.codef.io)
- [easycodefpy](https://github.com/codef-io/easycodefpy) - CODEF 공식 Python SDK

## 라이선스

MIT
