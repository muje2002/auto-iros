# PRD: auto-iros - 인터넷 등기소 등기부등본 자동 발급 프로그램

## 1. 개요

### 1.1 프로젝트 목적
인터넷 등기소(iros.go.kr)에서 부동산 등기부등본을 CODEF API를 통해 자동으로 열람/발급받아 PDF로 저장하는 Python CLI 프로그램.

### 1.2 배경
- 부동산 실무에서 다수의 등기부등본을 반복적으로 발급받아야 하는 수요 존재
- 수동 발급 시 건당 주소 입력, 결제, 다운로드 과정이 번거로움
- CODEF API를 활용하면 프로그래밍 방식으로 자동화 가능

### 1.3 대상 사용자
- 부동산 관련 업무 종사자 (중개사, 법무사, 감정평가사 등)
- 다량의 등기부등본을 정기적으로 발급받아야 하는 기업/개인

---

## 2. CODEF API 스펙 (공식 문서 기반)

### 2.1 엔드포인트
| 환경 | URL | Timeout |
|------|-----|---------|
| 데모 | `https://development.codef.io/v1/kr/public/ck/real-estate-register/status` | 300s |
| 정식 | `https://api.codef.io/v1/kr/public/ck/real-estate-register/status` | 300s |

### 2.2 인증
- CODEF OAuth2 토큰 기반 (Bearer Token)
- 비밀번호: **RSA 암호화** 필수 (CODEF 발급 publicKey 사용)

### 2.3 필수 입력 파라미터
| Key | Name | Type | Description |
|-----|------|------|-------------|
| `organization` | 기관코드 | String | 고정값 `"0002"` |
| `phoneNo` | 전화번호 | String | 허용 접두사: 010, 011, 016~019, 02, 031~033, 041~043, 051~055, 061~064, 070 |
| `password` | 비밀번호 | String | **RSA 암호화**, 4자리 숫자, 사용자 임의 설정 |
| `inquiryType` | 조회구분 | String | `0`:고유번호, `1`:간편검색, `2`:소재지번, `3`:도로명주소 |
| `issueType` | 발행구분 | String | `0`:발급, `1`:열람, `2`:고유번호조회, `3`:원문데이터 |

### 2.4 조건부 파라미터 (inquiryType별)

#### inquiryType = "0" (고유번호로 찾기)
| Key | Required | Description |
|-----|----------|-------------|
| `uniqueNo` | **필수** | 부동산 고유번호 14자리 (0000-0000-000000) |

#### inquiryType = "1" (간편검색)
| Key | Required | Description |
|-----|----------|-------------|
| `address` | **필수** | 검색어 최소 3자리 이상 |
| `realtyType` | 선택 | 미입력시 전체 |
| `addr_sido` | 선택 | 미입력시 전체 |
| `recordStatus` | 선택 | 0:현행, 1:폐쇄, 2:현행+폐쇄 (default=0) |
| `startPageNo` | 선택 | 시작페이지 (미입력시 첫페이지) |
| `pageCount` | 선택 | 조회페이지수 (0 < n <= 10, default=10) |

#### inquiryType = "2" (소재지번)
| Key | Required | Description |
|-----|----------|-------------|
| `addr_sido` | **필수** | 시/도 |
| `addr_dong` | **필수** | 읍면동/리/동 |
| `addr_lotNumber` | **필수** | 지번 |
| `inputSelect` | 조건부 | 집합건물(realtyType=1)인 경우 필수. 0:지번, 1:건물명칭 |
| `buildingName` | 조건부 | 건물명칭 (inputSelect=1) |

#### inquiryType = "3" (도로명주소)
| Key | Required | Description |
|-----|----------|-------------|
| `addr_sido` | **필수** | 시/도 |
| `addr_sigungu` | **필수** | 시군구 |
| `addr_roadName` | **필수** | 도로명 |
| `addr_buildingNumber` | **필수** | 건물번호 |

### 2.5 공통 선택 파라미터
| Key | Name | Default | Description |
|-----|------|---------|-------------|
| `realtyType` | 부동산구분 | 전체 | 0:토지+건물, 1:집합건물, 2:토지, 3:건물 |
| `dong` | 동 | - | 집합건물 동 |
| `ho` | 호 | - | 집합건물 호 |
| `jointMortgageJeonseYN` | 공동담보/전세목록 포함 | "0" | 0:미포함, 1:포함 |
| `tradingYN` | 매매목록 포함 | "0" | 0:미포함, 1:포함 |
| `listNumber` | 목록번호 | 전체 | 다건 선택시 `\|` 구분 |
| `electronicClosedYN` | 전산폐쇄조회 | "0" | inquiryType 2,3 전용 |
| `ePrepayNo` | 선불전자지급수단 번호 | - | issueType < 2 일 때 필수, 12자리 |
| `ePrepayPass` | 선불전자지급수단 비밀번호 | - | issueType < 2 일 때 필수 |
| `warningSkipYN` | 경고 무시 | "0" | 0:실행취소, 1:무시(진행) |
| `registerSummaryYN` | 등기사항요약 출력 | "0" | 0:미출력, 1:출력 |
| `applicationType` | 신청구분 | "0" | 집합건물: 0:전유제외, 1:전유포함 |
| `selectAddress` | 주소 리스트 선택 | "0" | 0:미선택, 1:선택 |
| `isIdentityViewYn` | 주민등록번호 공개 | "0" | 0:미공개, 1:특정인공개 |
| `identityList` | 주민등록번호 List | - | isIdentityViewYn=1일 때 필수 |
| `originDataYN` | 원문Data 포함 | "0" | 0:미포함, 1:포함 |

### 2.6 2-Way 추가인증 흐름
```
[1차 요청] ──→ API 응답 (CF-03002, continue2Way=true)
                  ├── extraInfo.resAddrList: 주소 목록 반환
                  ├── jobIndex, threadIndex, jti, twoWayTimestamp
                  │
[2차 요청] ──→ 1차 입력부 + is2Way=true + uniqueNo + twoWayInfo
                  └── 응답: 최종 출력부 (PDF 포함)
```

**추가인증 Timeout: 120초**

### 2.7 출력부 (Output)
| Key | Name | Description |
|-----|------|-------------|
| `resIssueYN` | 발행여부 | 0:발행실패(100매초과), 1:성공, 2:고유번호조회, 3:결과처리성공(발급성공), 4:발급성공후처리실패 |
| `resOriGinalData` | 원문 DATA | **PDF BASE64** |
| `resAddrList` | 주소 List | 다수 부동산 검색 결과 목록 |
| `resSearchList` | 검색 List | 매매목록 or 공동담보/전세목록 |
| `resRegisterEntriesList` | 등기사항 List | 등기부등본 문서 내용 |
| `resRegistrationSumList` | 주요등기사항 요약 | registerSummaryYN=1일 때 |
| `resRegistrationHisList` | 등기이력 List | 등기 변경 이력 |
| `resWarningMessage` | 경고 메시지 | warningSkipYN=1일 때 |

### 2.8 주요 제약사항 / 특이사항
- 과도한 API 호출 시 대법원에서 IP 차단 가능
- 배치형 서비스/비정상 호출 시 서비스 이용 제한
- 대법원 정기점검: 매월 첫째주, 셋째주 목요일 21:00~06:00
- 등기사항증명서 100매 이상 시 발행 불가 → `resSearchList` > 목록List 반환
- 말소사항 등기명의인 500명 초과 시 열람/발급 불가 (CF-12100)
- 간편검색(inquiryType=1)은 100페이지 단위(1000건) 조회, `pageCount` <= 100
- 선불전자지급수단은 **전자민원캐시** 사용
- `issueType="1"(열람)`인 경우에만 재열람 가능
- 전화번호 접두사 제한 위반 시 CF-13002 오류

---

## 3. 기능 요구사항

### 3.1 Phase 1: 핵심 기능 (MVP)

#### F1. CODEF 인증
- [ ] OAuth2 토큰 발급 및 자동 갱신
- [ ] RSA 공개키 기반 비밀번호 암호화
- [ ] .env 기반 설정 관리 (client_id, client_secret, phoneNo)

#### F2. 조회 방식 지원
- [ ] 고유번호 조회 (inquiryType=0)
- [ ] 간편검색 (inquiryType=1)
- [ ] 소재지번 조회 (inquiryType=2)
- [ ] 도로명주소 조회 (inquiryType=3)

#### F3. 2-Way 추가인증 처리
- [ ] 1차 요청 → 주소 목록 반환 감지 (CF-03002)
- [ ] 사용자에게 주소 목록 표시 및 선택 UI
- [ ] 2차 요청 자동 전송 (is2Way, uniqueNo, twoWayInfo)
- [ ] 120초 타임아웃 처리

#### F4. 결제 (선불전자지급수단)
- [ ] 전자민원캐시 번호/비밀번호 입력 지원
- [ ] issueType별 결제 필요 여부 자동 판단
- [ ] 결제 정보 .env 또는 실행 시 입력

#### F5. PDF 출력
- [ ] `resOriGinalData` (BASE64) → PDF 파일 저장
- [ ] 주소 기반 파일명 자동 생성
- [ ] 출력 디렉토리 설정

#### F6. 엑셀 일괄 입력
- [ ] 입력 템플릿 생성 (주소, 동/호, 조회구분, 부동산구분 등)
- [ ] 엑셀 파일 읽기 → RegisterRequest 리스트 변환
- [ ] 일괄 처리 진행률 표시
- [ ] 결과 요약 테이블 출력

#### F7. CLI 인터페이스
- [ ] `single` - 단건 조회
- [ ] `batch` - 엑셀 일괄 조회
- [ ] `template` - 엑셀 템플릿 생성
- [ ] `search` - 주소 검색 (간편검색, 발급 없이 주소 목록만)
- [ ] rich 기반 터미널 UI

### 3.2 Phase 2: 고급 기능

#### F8. 조회 결과 구조화
- [ ] 등기사항 요약 (resRegistrationSumList) 파싱 및 출력
- [ ] 등기 이력 (resRegistrationHisList) 조회
- [ ] 소유자/권리관계 요약 리포트

#### F9. 결과 엑셀 내보내기
- [ ] 일괄 조회 결과를 엑셀로 저장 (성공/실패, 파일경로, 소유자 등)
- [ ] 등기사항 요약을 엑셀 시트로 정리

#### F10. 스케줄링 / 반복 조회
- [ ] 특정 시간대 대법원 점검 자동 회피
- [ ] 대량 건수 처리 시 요청 간격 조절 (IP 차단 방지)

#### F11. 에러 핸들링 고도화
- [ ] CODEF 에러 코드별 한국어 안내 메시지
- [ ] 재시도 로직 (네트워크 오류, 일시적 장애)
- [ ] 실패 건 별도 리포트 및 재처리 기능

---

## 4. 현재 코드 vs API 스펙 Gap 분석

### 4.1 수정 필요 사항 (Critical)

| 항목 | 현재 | API 스펙 | 영향도 |
|------|------|---------|--------|
| `phoneNo` | **미구현** | 필수 파라미터 | 🔴 API 호출 불가 |
| `password` (RSA) | **미구현** | RSA 암호화 필수 | 🔴 API 호출 불가 |
| `inquiryType` | 미구현 | 조회방식 결정 핵심 | 🔴 잘못된 요청 |
| 2-Way 인증 | 감지만 | 전체 플로우 필요 | 🔴 실제 발급 불가 |
| `ePrepayNo/Pass` | **미구현** | 발급 시 결제 필수 | 🔴 발급 불가 |
| `issueType` 코드 | 0:발급,1:열람 | 반대 (0:발급,1:열람) | 🟡 확인 필요 |
| `realtyType` 코드 | 자체 매핑 | 0:토지+건물,1:집합,2:토지,3:건물 | 🟡 코드 불일치 |
| PDF 필드명 | `resRegisterEntriesPDF` | `resOriGinalData` | 🔴 PDF 추출 실패 |
| timeout | 120s | 300s (1차), 120s (2차) | 🟡 |

### 4.2 수정 불필요 (현재 올바른 부분)
- OAuth2 토큰 발급 흐름
- 엑셀 입출력 기본 구조
- PDF base64 → 파일 저장 로직
- CLI 구조 (argparse + rich)
- 기본 프로젝트 구조

---

## 5. 기술 아키텍처

### 5.1 프로젝트 구조
```
auto-iros/
├── main.py                     # CLI 진입점
├── src/
│   ├── config.py               # 환경설정 + 상수
│   ├── auth.py                 # CODEF OAuth2 인증
│   ├── crypto.py               # RSA 비밀번호 암호화 (신규)
│   ├── codef_api.py            # API 클라이언트 (전면 수정)
│   ├── two_way.py              # 2-Way 추가인증 처리 (신규)
│   ├── payment.py              # 전자민원캐시 결제 (신규)
│   ├── excel_handler.py        # 엑셀 입출력
│   └── pdf_handler.py          # PDF 저장
├── docs/
│   ├── PRD.md                  # 이 문서
│   └── API_SPEC.md             # API 스펙 정리
├── templates/                  # 엑셀 템플릿
├── output/                     # PDF 출력
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD
├── .env.example
├── requirements.txt
├── CLAUDE.md
├── dev_history.md
└── README.md
```

### 5.2 기술 스택
- Python 3.11+
- `requests` - HTTP 클라이언트
- `pycryptodome` - RSA 암호화
- `openpyxl` - 엑셀 처리
- `python-dotenv` - 환경변수
- `rich` - 터미널 UI
- GitHub Actions - CI (lint, type check)

### 5.3 설정 파일 (.env)
```
CODEF_CLIENT_ID=xxx
CODEF_CLIENT_SECRET=xxx
CODEF_ENV=sandbox
CODEF_PHONE_NO=01000000000
CODEF_PASSWORD=1234
EPREPAY_NO=              # 선불전자지급수단 번호 (선택)
EPREPAY_PASS=            # 선불전자지급수단 비밀번호 (선택)
OUTPUT_DIR=./output
```

---

## 6. 개발 로드맵

### Sprint 1: API 스펙 정합성 확보 (핵심 수정)
1. `crypto.py` - RSA 암호화 모듈 신규 작성
2. `config.py` - phoneNo, password, ePrepay 설정 추가
3. `codef_api.py` - 전면 재작성 (inquiryType별 파라미터, 정확한 필드명)
4. `two_way.py` - 2-Way 추가인증 전체 흐름 구현
5. `payment.py` - 전자민원캐시 결제 연동
6. `pdf_handler.py` - `resOriGinalData` 필드명 수정

### Sprint 2: 엑셀 & CLI 보강
1. `excel_handler.py` - inquiryType별 엑셀 컬럼 확장
2. `main.py` - `search` 명령 추가, 2-Way 인터랙션 UI
3. 에러 코드 한국어 매핑
4. 대법원 점검시간 경고

### Sprint 3: CI/CD & 안정성
1. GitHub Actions 워크플로우 (lint, mypy, pytest)
2. 재시도 로직
3. IP 차단 방지 rate limiting
4. 결과 엑셀 내보내기

---

## 7. CI/CD 계획

### GitHub Actions 워크플로우
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install ruff mypy pytest
      - run: ruff check .
      - run: mypy src/ --ignore-missing-imports
      - run: pytest tests/ -v
```

### 현재 상태
- GitHub Actions: **미설정** (워크플로우 파일 없음)
- Sprint 3에서 추가 예정

---

## 8. 리스크 및 제약사항

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 대법원 IP 차단 | 서비스 중단 | 요청 간격 조절, 배치 크기 제한 |
| RSA 공개키 변경 | 암호화 실패 | CODEF에서 최신 키 동적 조회 |
| 전자민원캐시 잔액 부족 | 발급 실패 | 잔액 확인 API (있을 경우) 연동 |
| CODEF API 스펙 변경 | 호출 실패 | API 버전 관리, 에러 로깅 |
| 대법원 점검 시간 | 일시적 불가 | 점검 스케줄 자동 체크 |

---

## 9. 성공 지표

- 단건 등기부등본 발급 성공률 > 95%
- 50건 일괄 발급 소요 시간 < 30분
- 2-Way 인증 자동 처리 성공률 > 90%
- PDF 파일 정상 생성률 100%
