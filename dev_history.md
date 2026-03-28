# 개발 히스토리 - auto-iros

## 2026-03-28 (Day 1) - 프로젝트 초기 설정 및 MVP 구현

### 작업 내용

#### 1. GitHub 레포지토리 생성
- `muje2002/auto-iros` public repo 생성
- main 브랜치 초기 커밋 및 push 완료

#### 2. 프로젝트 초기 구조 작성
- **src/config.py**: CODEF API 환경설정 (sandbox/production URL, .env 기반)
- **src/auth.py**: OAuth2 토큰 발급 및 자동 갱신
- **src/codef_api.py**: 등기부등본 API 클라이언트 (단건/일괄 조회)
- **src/excel_handler.py**: 엑셀 템플릿 생성 + 주소 목록 읽기
- **src/pdf_handler.py**: base64 PDF → 파일 저장
- **main.py**: CLI 인터페이스 (single, batch, template 명령)

#### 3. CODEF API 공식 문서 분석 (PDF)
- API 스펙 전체 분석 완료
- 현재 코드와의 Gap 분석 수행 → PRD 문서화

#### 4. PRD 작성
- `docs/PRD.md` 생성
- API 스펙 전체 정리 (입력부, 출력부, 추가인증, 특이사항)
- 기능 요구사항 Phase 1/2 정의
- 현재 코드 vs API 스펙 Gap 분석
- 개발 로드맵 (Sprint 1~3) 수립

---

## 2026-03-28 (Day 1) - Sprint 1: API 스펙 정합성 확보

### 작업 내용

#### 1. config.py 확장
- `phone_no`, `password`, `eprepay_no`, `eprepay_pass` 필드 추가
- `CODEF_PUBLIC_KEY` (RSA 공개키) 상수 추가 (.env 오버라이드 가능)
- `API_TIMEOUT_FIRST` (300s), `API_TIMEOUT_SECOND` (120s) 상수 추가
- `.env.example` 업데이트

#### 2. crypto.py 신규 작성
- CODEF RSA 공개키 기반 비밀번호 암호화 (pycryptodome PKCS1_v1_5)
- Base64 패딩 자동 보정 + PEM/DER 양쪽 시도
- 암호화/복호화 라운드트립 테스트 통과

#### 3. codef_api.py 전면 재작성
- `inquiryType`별 파라미터 분기 (고유번호/간편검색/소재지번/도로명주소)
- `realtyType` 코드 수정: 0(토지+건물), 1(집합건물), 2(토지), 3(건물)
- `issueType` 코드 수정: 0(발급), 1(열람), 2(고유번호조회), 3(원문데이터)
- `phoneNo`, `password` (RSA 암호화) 자동 포함
- PDF 필드명 `resOriGinalData`로 수정
- 2-Way 추가인증 감지 및 응답 파싱 (CF-03002)
- 결제 정보 (ePrepayNo/Pass) 자동 포함
- 타임아웃 300s(1차)/120s(2차)
- JSON body 전송으로 변경 (`requests.post(..., json=params)`)

#### 4. two_way.py 신규 작성
- CF-03002 응답 → 주소 목록 표시 (rich Table)
- 사용자 선택 UI (번호 입력, 0으로 취소)
- 2차 요청 자동 전송 (is2Way, uniqueNo, twoWayInfo)

#### 5. payment.py 신규 작성
- `requires_payment()`: issueType별 결제 필요 여부 판단
- `validate_payment_config()`: ePrepayNo 12자리 검증

#### 6. pdf_handler.py 수정
- `result.address` → `result.request.display_name` 으로 변경

#### 7. excel_handler.py 확장
- 14컬럼으로 확장 (조회구분, 시도, 읍면동, 지번, 시군구, 도로명, 건물번호 추가)
- inquiryType별 최소 검증 로직

#### 8. main.py 업데이트
- `search` 명령 추가 (주소 검색, 발급 없이 목록만 조회)
- `--inquiry-type`, `--unique-no` 옵션 추가
- 2-Way 추가인증 자동 처리 (단건 조회 시)
- 결제 검증 (발급/열람 시 ePrepay 필수)

### Gap 해소 현황
| 항목 | 이전 | 현재 |
|------|------|------|
| phoneNo (필수 파라미터) | ❌ | ✅ config + API 파라미터 |
| RSA 비밀번호 암호화 | ❌ | ✅ crypto.py |
| inquiryType 기반 조회 분기 | ❌ | ✅ 4가지 타입 전부 지원 |
| 2-Way 추가인증 전체 흐름 | ❌ 감지만 | ✅ 선택 UI + 2차 요청 |
| 전자민원캐시 결제 | ❌ | ✅ payment.py 검증 |
| PDF 필드명 (resOriGinalData) | ❌ 잘못됨 | ✅ 수정 완료 |
| realtyType 코드 매핑 | ❌ 불일치 | ✅ API 스펙 일치 |

---

## 2026-03-28 (Day 1) - Sprint 1.5: 웹 UI 구현

### 작업 내용

#### 1. PRD 업데이트
- Phase 1.5: 웹 UI 섹션 추가 (F12~F16)
- 기술 아키텍처 업데이트 (프로젝트 구조, 기술 스택)
- Sprint 1.5 로드맵 추가

#### 2. two_way.py 리팩토링
- `build_two_way_params()`: 순수 로직 함수 (I/O 없음, 웹에서 재사용)
- `handle_two_way_cli()`: CLI 전용 어댑터 (기존 handle_two_way 역할)
- `_select_address_cli()`: CLI 전용 주소 선택

#### 3. FastAPI 웹 서버 (app.py)
- Jinja2 템플릿 + Tailwind CSS CDN
- `/static` 마운트, Config 로드
- 페이지 라우트: `/`, `/single`, `/batch`, `/search`

#### 4. API 라우트 (src/routes/)
- **template.py**: `GET /api/template/download` - 엑셀 템플릿 다운로드
- **search.py**: `POST /api/search` - 주소 검색 (결제 불필요)
- **single.py**: 단건 조회
  - `POST /api/single` - 1차 요청 (성공/2-Way/에러 분기)
  - `POST /api/single/two-way` - 2-Way 2차 요청
  - `GET /api/single/pdf/{id}` - PDF 다운로드
  - 인메모리 2-Way 세션 관리 (120초 만료)
- **batch.py**: 일괄 조회
  - `POST /api/batch/upload` - 엑셀 업로드 → 미리보기
  - `POST /api/batch/execute` - 일괄 실행
  - `GET /api/batch/download/{filename}` - 결과 PDF 다운로드

#### 5. HTML 프론트엔드
- **base.html**: 레이아웃 (네비게이션, Tailwind CDN)
- **index.html**: 4기능 카드 대시보드
- **single.html**: 조회구분별 동적 폼, 2-Way 주소 선택 테이블, PDF 다운로드
- **batch.html**: 드래그앤드롭 엑셀 업로드, 미리보기/실행/결과 테이블
- **search.html**: 검색 → 결과 테이블 → "조회" 버튼으로 single 연동
- **app.js**: fetch 래퍼, 로딩 오버레이, 주소 테이블 렌더러

#### 6. 비동기 처리
- `asyncio.to_thread()`로 동기 requests 라이브러리 호출 감싸서 이벤트 루프 블로킹 방지

### 검증
- ruff check: All checks passed
- mypy: Success (14 source files + app.py)
- FastAPI TestClient: 모든 페이지 200 OK
- 템플릿 다운로드: xlsx 정상 생성

### 다음 작업 (Sprint 2)
1. CODEF 에러 코드별 한국어 안내 메시지
2. 재시도 로직 (네트워크 오류, 일시적 장애)
3. 대법원 점검시간 경고
4. 결과 엑셀 내보내기
5. IP 차단 방지 rate limiting

---

*최종 업데이트: 2026-03-28*
