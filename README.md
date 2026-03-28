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

이 프로그램을 실행하려면 Python이라는 프로그램이 필요합니다.

1. 웹 브라우저에서 [python.org/downloads](https://www.python.org/downloads/) 접속
2. **"Download Python 3.11"** (또는 최신 버전) 노란 버튼 클릭
3. 다운로드된 설치 파일을 더블클릭하여 실행
4. **중요!** 설치 화면 맨 아래 **"Add Python to PATH"** 체크박스를 반드시 체크!
5. **"Install Now"** 클릭 → 설치 완료까지 기다리기

**설치 확인하기:**
1. 키보드에서 `윈도우키 + R` 을 동시에 누르기
2. 나타난 창에 `cmd` 입력 후 Enter
3. 검은 창(명령 프롬프트)이 열리면 아래를 그대로 입력하고 Enter:
```
python --version
```
4. `Python 3.11.x` 같은 글자가 나오면 성공!

### 2단계: 프로그램 다운로드

1. [github.com/muje2002/auto-iros](https://github.com/muje2002/auto-iros) 접속
2. 초록색 **"<> Code"** 버튼 클릭
3. **"Download ZIP"** 클릭
4. 다운로드된 `auto-iros-main.zip` 파일을 바탕화면에 압축 해제
   - ZIP 파일 우클릭 → **"모두 압축 풀기"** → 바탕화면 선택 → 압축 풀기

### 3단계: 필요한 패키지 설치

1. 명령 프롬프트를 열기 (`윈도우키 + R` → `cmd` → Enter)
2. 아래 명령어를 한 줄씩 입력하고 Enter:

```
cd %USERPROFILE%\Desktop\auto-iros-main
```
```
pip install -r requirements.txt
```

여러 줄의 설치 진행 메시지가 나옵니다. `Successfully installed ...` 메시지가 나오면 완료!

> **에러가 나면?** `pip` 대신 `python -m pip install -r requirements.txt` 로 시도하세요.

### 4단계: 환경 설정 (.env 파일 만들기)

프로그램이 CODEF API에 접속하려면 설정 파일이 필요합니다.

**명령 프롬프트에서** (3단계에서 이어서):
```
copy .env.example .env
```

이러면 `.env` 파일이 생성됩니다. 이 파일을 메모장으로 편집합니다:
```
notepad .env
```

메모장이 열리면 아래 **두 가지 방법** 중 하나를 선택하세요:

---

#### 방법 A: 빠른 체험 (회원가입 없이 바로 시작)

CODEF에서 공개한 테스트용 키로 바로 사용할 수 있습니다.
실제 등기부등본은 발급되지 않지만, 프로그램의 모든 기능을 체험해볼 수 있습니다.

`.env` 파일을 아래 내용으로 통째로 바꾸세요:

```
CODEF_CLIENT_ID=ef27cfaa-10c1-4470-adac-60ba476273f9
CODEF_CLIENT_SECRET=83160c33-9045-4915-86d8-809473cdf5c3
CODEF_ENV=sandbox
CODEF_PUBLIC_KEY=여기에_CODEF_개발자센터에서_발급받은_공개키_입력
CODEF_PHONE_NO=01012345678
CODEF_PASSWORD=1234
OUTPUT_DIR=./output
```

> **주의:** `CODEF_PUBLIC_KEY`는 [CODEF 개발자센터](https://developer.codef.io)에 가입 후 발급받아야 합니다. 가입은 무료입니다.

저장(`Ctrl + S`) 후 메모장 닫기.

---

#### 방법 B: 실제 등기부등본 발급 (CODEF 가입 필요)

1. [developer.codef.io](https://developer.codef.io) 접속 → 회원가입 (무료)
2. 로그인 후 **마이페이지** → **API 키 관리**에서 아래 3가지 확인:
   - **Client ID** (예: `d88c85f7-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
   - **Client Secret** (예: `d7fe4279-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
   - **RSA 공개키** (긴 영문+숫자 문자열)

3. `.env` 파일을 아래처럼 수정:

```
CODEF_CLIENT_ID=발급받은_Client_ID
CODEF_CLIENT_SECRET=발급받은_Client_Secret
CODEF_ENV=demo
CODEF_PUBLIC_KEY=발급받은_RSA_공개키
CODEF_PHONE_NO=본인_전화번호(하이픈없이)
CODEF_PASSWORD=1234
OUTPUT_DIR=./output
```

저장(`Ctrl + S`) 후 메모장 닫기.

> **참고:** 실제 등기부등본 PDF를 받으려면 `CODEF_ENV=production`으로 변경하고, 전자민원캐시 설정이 추가로 필요합니다. (아래 "결제 안내" 참고)

---

### 5단계: 프로그램 실행

명령 프롬프트에서 (3단계에서 이어서):
```
python -m uvicorn app:app --reload
```

아래와 비슷한 메시지가 나오면 성공:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
```

> 이 창은 프로그램이 실행되는 동안 열어두어야 합니다. 닫으면 프로그램이 종료됩니다.

### 6단계: 웹 브라우저에서 사용

1. 웹 브라우저(크롬, 엣지 등) 주소창에 입력:
```
http://localhost:8000
```

2. 아래와 같은 메인 화면이 나타나면 성공!

| 메뉴 | 기능 | 설명 |
|------|------|------|
| **단건 조회** | 등기부등본 1건 조회 | 주소 입력 → 조회 → PDF 다운로드 |
| **일괄 조회** | 엑셀로 여러 건 조회 | 엑셀 업로드 → 한번에 처리 |
| **주소 검색** | 부동산 검색 | 주소로 검색하여 고유번호 확인 |
| **템플릿 다운로드** | 엑셀 양식 받기 | 일괄 조회용 입력 양식 |

### 프로그램 종료

명령 프롬프트에서 `Ctrl + C` 를 누르면 종료됩니다.

---

## 사용 예시

### 단건 조회
1. 메인 화면에서 **"단건 조회"** 클릭
2. **"조회구분"** 에서 "간편검색" 선택
3. **"검색어"** 에 주소 입력 (예: `서울특별시 강남구 테헤란로 152`)
4. **"발급유형"** 선택:
   - `고유번호조회` - 무료, 부동산 정보만 확인
   - `열람` - 유료, 등기부등본 열람용 PDF
   - `발급` - 유료, 등기부등본 원본 PDF
5. **"조회하기"** 클릭
6. 조회 성공 시 **"PDF 다운로드"** 클릭

### 일괄 조회
1. 메인 화면에서 **"템플릿 다운로드"** 클릭 → 엑셀 양식 받기
2. 엑셀 파일을 열고 조회할 주소들을 입력 → 저장
3. **"일괄 조회"** 페이지에서 엑셀 파일을 드래그하여 업로드
4. 미리보기 테이블 확인 후 **"전체 실행"** 클릭
5. 진행률 바가 완료되면 결과에서 개별 PDF 다운로드 또는 **"결과 엑셀 다운로드"**

---

## 환경(모드) 설명

이 프로그램은 3가지 환경(모드)으로 사용할 수 있습니다.
`.env` 파일의 `CODEF_ENV` 값을 변경하면 됩니다.

| 환경 | `.env` 설정 | 비용 | PDF 발급 | 용도 |
|------|-------------|------|---------|------|
| **샌드박스** | `CODEF_ENV=sandbox` | 무료 | X (테스트 데이터) | 프로그램 기능 체험 |
| **데모** | `CODEF_ENV=demo` | 무료* | O (결제 필요) | 개발/테스트 |
| **운영** | `CODEF_ENV=production` | 유료 | O (결제 필요) | 실제 등기부등본 발급 |

> *데모 환경에서도 PDF를 받으려면 전자민원캐시(결제)가 필요합니다.

---

## 결제 안내 (전자민원캐시)

등기부등본 **열람** 또는 **발급** 시에는 대법원 전자민원캐시로 결제가 필요합니다.

### 전자민원캐시란?
인터넷등기소(iros.go.kr)에서 사용하는 **선불 결제 수단**입니다.

### 설정 방법
1. [인터넷등기소](https://www.iros.go.kr) 접속 → 전자민원캐시 구매
2. 구매 후 발급받은 번호와 비밀번호를 `.env` 파일에 추가:

```
EPREPAY_NO=123456789012
EPREPAY_PASS=비밀번호
```

3. 프로그램 재시작 (명령 프롬프트에서 `Ctrl + C` → 다시 `python -m uvicorn app:app --reload`)

### 결제 없이 사용하는 방법
- **발급유형을 "고유번호조회"로 선택** → 무료로 부동산 정보 조회 가능 (PDF 없음)
- **샌드박스 환경 사용** (`CODEF_ENV=sandbox`) → 테스트 데이터로 기능 체험

---

## 문제 해결

### "python을 찾을 수 없습니다"
→ 1단계에서 **"Add Python to PATH"** 를 체크하지 않은 경우입니다.
→ Python을 삭제 후 다시 설치하면서 반드시 체크해주세요.

### "pip를 찾을 수 없습니다"
→ `python -m pip install -r requirements.txt` 로 시도해보세요.

### ".env 파일이 안 보입니다"
→ 윈도우 탐색기에서 "파일 확장명"이 숨겨져 있을 수 있습니다.
→ 탐색기 상단 → **보기** → **"파일 확장명"** 체크

### "CODEF_CLIENT_ID 환경변수를 설정하세요"
→ 4단계의 `.env` 파일이 올바르게 작성되었는지 확인하세요.
→ `.env` 파일이 프로그램 폴더 최상위(`app.py`와 같은 위치)에 있어야 합니다.

### "CODEF_PUBLIC_KEY가 설정되지 않았습니다"
→ `.env` 파일에 CODEF 개발자센터에서 발급받은 RSA 공개키를 입력하세요.
→ CODEF 개발자센터 가입(무료) 후 마이페이지에서 확인할 수 있습니다.

### "선불전자지급수단 번호를 입력하지 않았습니다" (CF-13320)
→ 열람/발급에는 전자민원캐시가 필요합니다. 위의 "결제 안내" 섹션을 참고하세요.
→ 결제 없이 테스트하려면 발급유형을 **"고유번호조회"** 로 선택하세요.

### 웹 페이지가 열리지 않습니다
→ 명령 프롬프트 창이 열려있는지 확인하세요 (닫으면 서버 종료).
→ `http://localhost:8000` 을 정확히 입력했는지 확인하세요.
→ 다른 프로그램이 8000번 포트를 사용 중이면: `python -m uvicorn app:app --port 8080` 으로 실행 후 `http://localhost:8080` 접속.

### .env 파일 수정 후 반영이 안 됩니다
→ `.env` 파일 변경 시 프로그램을 재시작해야 합니다.
→ 명령 프롬프트에서 `Ctrl + C` → 다시 `python -m uvicorn app:app --reload`

---

## 주의사항

- **대법원 점검시간**: 매월 1째/3째 목요일 21:00 ~ 금요일 06:00 에는 조회가 안 됩니다
- **과도한 조회 금지**: 짧은 시간에 너무 많이 조회하면 IP가 차단될 수 있습니다
- **발급 비용**: 실제 등기부등본 발급(production)은 건당 요금이 발생합니다

---

## 개발자 정보

<details>
<summary>CLI 사용법, 테스트, Docker (클릭하여 펼치기)</summary>

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
python -m mypy src/ --ignore-missing-imports              # 타입 체크
python -m pytest tests/ -v                                # 테스트 (88개)
```

### Docker

```bash
docker compose up
```

</details>

## 참고

- [CODEF 개발자 가이드](https://developer.codef.io)
- [easycodefpy](https://github.com/codef-io/easycodefpy) - CODEF 공식 Python SDK
- [인터넷등기소](https://www.iros.go.kr) - 전자민원캐시 구매

## 라이선스

MIT
