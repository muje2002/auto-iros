# auto-iros

인터넷 등기소(iros.go.kr) 등기부등본을 CODEF API를 통해 자동으로 발급받아 PDF로 저장하는 Python CLI 프로그램입니다.

## 주요 기능

- **단건 조회**: 주소를 입력하여 등기부등본 1건 발급
- **일괄 조회**: 엑셀 파일로 여러 주소를 한번에 입력하여 대량 발급
- **PDF 저장**: 발급된 등기부등본을 PDF 파일로 자동 저장
- **엑셀 템플릿**: 일괄 조회용 입력 양식 자동 생성

## 사전 준비

### 1. CODEF API 키 발급

[CODEF 개발자 센터](https://developer.codef.io)에서 회원가입 후 API 키를 발급받으세요.

- Client ID
- Client Secret

### 2. 설치

```bash
git clone https://github.com/muje2002/auto-iros.git
cd auto-iros
pip install -r requirements.txt
```

### 3. 환경 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 CODEF API 키를 입력하세요:

```
CODEF_CLIENT_ID=발급받은_클라이언트_ID
CODEF_CLIENT_SECRET=발급받은_클라이언트_시크릿
CODEF_ENV=sandbox       # sandbox(테스트) 또는 production(운영)
OUTPUT_DIR=./output     # PDF 저장 경로
```

## 사용법

### 엑셀 템플릿 생성

```bash
python main.py template
```

`등기부등본_요청_템플릿.xlsx` 파일이 생성됩니다. 이 파일에 주소를 입력하세요.

### 단건 조회

```bash
# 기본 (건물, 전체등기, 발급)
python main.py single --address "서울특별시 강남구 테헤란로 123"

# 집합건물 (아파트 등)
python main.py single --address "서울특별시 서초구 서초대로 456" \
  --dong "101동" --ho "202호" --property-type 집합건물

# 토지, 갑구만 열람
python main.py single --address "경기도 성남시 분당구 판교로 789" \
  --property-type 토지 --register-type 갑구 --issue-type 열람
```

### 일괄 조회 (엑셀)

```bash
# 엑셀 파일로 여러 건 조회
python main.py batch --file 요청목록.xlsx

# 확인 프롬프트 없이 바로 실행
python main.py batch --file 요청목록.xlsx -y
```

### 엑셀 입력 형식

| 주소 | 동 | 호 | 부동산구분 | 등기유형 | 발급유형 | 고유번호 |
|------|----|----|-----------|---------|---------|---------|
| 서울특별시 강남구 테헤란로 123 | | | 건물 | 전체 | 발급 | |
| 서울특별시 서초구 서초대로 456 | 101동 | 202호 | 집합건물 | 전체 | 발급 | |

- **주소**: 필수. 부동산 소재지 전체 주소
- **부동산구분**: 토지, 건물, 집합건물 (기본: 건물)
- **등기유형**: 전체, 갑구, 을구, 표제부 (기본: 전체)
- **발급유형**: 열람, 발급 (기본: 발급)

## 프로젝트 구조

```
auto-iros/
├── main.py                 # CLI 진입점
├── src/
│   ├── config.py           # 환경 설정
│   ├── auth.py             # CODEF OAuth2 인증
│   ├── codef_api.py        # 등기부등본 API 클라이언트
│   ├── excel_handler.py    # 엑셀 입출력
│   └── pdf_handler.py      # PDF 저장
├── templates/              # 엑셀 템플릿
├── output/                 # PDF 출력 디렉토리
├── .env.example            # 환경변수 예시
├── requirements.txt        # 의존성
└── README.md
```

## 참고

- [CODEF API 개발 가이드](https://developer.codef.io)
- [CODEF 부동산 등기부등본 API](https://developer.codef.io/products/public/each/ck/real-estate-register)
- CODEF sandbox 환경에서는 테스트 데이터만 조회 가능합니다
- 실제 등기부등본 발급은 production 환경에서 가능하며 건당 요금이 발생합니다

## 라이선스

MIT
