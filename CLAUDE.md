# auto-iros 프로젝트 정보

## 프로젝트 개요
- **이름**: auto-iros (인터넷 등기소 등기부등본 자동 발급)
- **GitHub**: https://github.com/muje2002/auto-iros
- **언어**: Python 3.11+
- **API**: CODEF 부동산등기부등본 열람/발급 API

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
- ~~`resRegisterEntriesPDF`~~ (이전 잘못된 필드명)

## 결제
- 발급(issueType < 2) 시 전자민원캐시 필요
- `ePrepayNo` (12자리) + `ePrepayPass`

## 프로젝트 구조
```
main.py              # CLI 진입점 (single/batch/template/search)
src/
├── config.py        # 설정 (.env)
├── auth.py          # OAuth2 토큰
├── crypto.py        # RSA 암호화 (TODO)
├── codef_api.py     # API 클라이언트
├── two_way.py       # 2-Way 추가인증 (TODO)
├── payment.py       # 전자민원캐시 (TODO)
├── excel_handler.py # 엑셀 입출력
└── pdf_handler.py   # PDF 저장
```

## 의존성
- requests, openpyxl, python-dotenv, pycryptodome, rich

## 주의사항
- 과도한 API 호출 시 대법원 IP 차단 가능
- 대법원 정기점검: 매월 첫째/셋째 주 목요일 21:00~06:00
- 등기사항증명서 100매 이상 시 발행 불가
- 말소사항 등기명의인 500명 초과 시 열람/발급 불가
- `realtyType` 코드: 0(토지+건물), 1(집합건물), 2(토지), 3(건물)

## 개발 명령어
```bash
pip install -r requirements.txt     # 의존성 설치
python main.py template             # 엑셀 템플릿 생성
python main.py single -a "주소"     # 단건 조회
python main.py batch -f file.xlsx   # 일괄 조회
```

## 현재 상태
- Phase 1 초기 구현 완료 (기본 구조)
- API 스펙 기반 전면 수정 필요 (RSA, 2-Way, 결제 등)
- 상세 Gap 분석: docs/PRD.md 섹션 4 참조
