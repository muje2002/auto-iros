# auto-iros 프로젝트 정보

## 프로젝트 개요
- **이름**: auto-iros (인터넷 등기소 등기부등본 자동 발급)
- **GitHub**: https://github.com/muje2002/auto-iros
- **언어**: Python 3.11+
- **API**: CODEF 부동산등기부등본 열람/발급 API
- **인터페이스**: 웹 UI (FastAPI + Jinja2) + CLI (argparse + rich)

## 핵심 API 정보
- **데모**: `https://development.codef.io/v1/kr/public/ck/real-estate-register/status`
- **정식**: `https://api.codef.io/v1/kr/public/ck/real-estate-register/status`
- **인증**: OAuth2 Bearer Token + RSA 암호화 비밀번호
- **Timeout**: 1차 300s, 2차(추가인증) 120s
- **2-Way 인증**: 주소 검색 → 주소 선택 → 발급 (CF-03002 응답 시)

## API 필수 파라미터
- `organization`: "0002" (고정)
- `phoneNo`: 전화번호 (접두사 제한 있음)
- `password`: RSA 암호화된 4자리 비밀번호
- `inquiryType`: 0(고유번호) / 1(간편검색) / 2(소재지번) / 3(도로명주소)
- `issueType`: 0(발급) / 1(열람) / 2(고유번호조회) / 3(원문데이터)

## PDF 데이터 필드
- **출력 필드명**: `resOriGinalData` (BASE64 인코딩 PDF)

## 결제
- 발급/열람(issueType 0,1) 시 전자민원캐시 필요
- `ePrepayNo` (12자리) + `ePrepayPass`

## 프로젝트 구조
```
main.py              # CLI 진입점 (single/batch/search/template)
app.py               # FastAPI 웹 서버 진입점
src/
├── config.py        # 설정 (.env) + 상수 (RSA 공개키, 타임아웃)
├── auth.py          # OAuth2 토큰
├── crypto.py        # RSA 비밀번호 암호화
├── codef_api.py     # API 클라이언트 (inquiryType별 파라미터 분기)
├── two_way.py       # 2-Way 추가인증 (순수 로직 + CLI 어댑터)
├── payment.py       # 전자민원캐시 결제 검증
├── excel_handler.py # 엑셀 입출력 (14컬럼 확장)
├── pdf_handler.py   # PDF 저장 (resOriGinalData)
└── routes/          # FastAPI 라우트 핸들러
    ├── single.py    # 단건 조회 API + 2-Way 세션 관리
    ├── batch.py     # 일괄 조회 API (엑셀 업로드/실행/다운로드)
    ├── search.py    # 주소 검색 API
    └── template.py  # 템플릿 다운로드 API
templates/           # Jinja2 HTML (base, index, single, batch, search)
static/              # CSS (Tailwind CDN + 커스텀), JS (fetch 래퍼, 로딩 UI)
```

## 의존성
- requests, openpyxl, python-dotenv, pycryptodome, base64url, rich
- fastapi, uvicorn, jinja2, python-multipart

## 주의사항
- 과도한 API 호출 시 대법원 IP 차단 가능
- 대법원 정기점검: 매월 첫째/셋째 주 목요일 21:00~06:00
- 등기사항증명서 100매 이상 시 발행 불가
- 말소사항 등기명의인 500명 초과 시 열람/발급 불가
- `realtyType` 코드: 0(토지+건물), 1(집합건물), 2(토지), 3(건물)

## 개발 명령어
```bash
pip install -r requirements.txt     # 의존성 설치

# 웹 서버
uvicorn app:app --reload            # http://localhost:8000

# CLI
python main.py template             # 엑셀 템플릿 생성
python main.py single -a "주소"     # 단건 조회 (간편검색)
python main.py search "테헤란로"    # 주소 검색
python main.py batch -f file.xlsx   # 일괄 조회

# 검증
python -m ruff check .              # 린트
python -m mypy src/ app.py --ignore-missing-imports  # 타입 체크
```

## 환경 설정
```
CODEF_ENV=demo          # demo(development.codef.io), sandbox(sandbox.codef.io), production(api.codef.io)
```

## 현재 상태
- Sprint 1 완료: API 스펙 정합성 확보
- Sprint 1.5 완료: 웹 UI (FastAPI + HTML/JS)
- Sprint 2 완료: 안정성 & UX 보강
  - 에러 코드 한국어 매핑 (errors.py)
  - 재시도 로직 (최대 3회, 지수 백오프)
  - 대법원 점검시간 경고 (웹 배너 + CLI)
  - IP 차단 방지 rate limiting (배치 1.5초 딜레이)
  - 결과 엑셀 내보내기 (배치 결과 xlsx 다운로드)
  - 라우트 에러 핸들링 강화 (.env 미설정 시 안내)
