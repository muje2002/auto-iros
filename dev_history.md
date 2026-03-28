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

### 발견된 주요 Gap (API 스펙 vs 현재 코드)
| 항목 | 상태 |
|------|------|
| phoneNo (필수 파라미터) | ❌ 미구현 |
| RSA 비밀번호 암호화 | ❌ 미구현 |
| inquiryType 기반 조회 분기 | ❌ 미구현 |
| 2-Way 추가인증 전체 흐름 | ❌ 감지만 구현 |
| 전자민원캐시 결제 | ❌ 미구현 |
| PDF 필드명 (resOriGinalData) | ❌ 잘못된 필드명 사용 |
| realtyType 코드 매핑 | ❌ 코드 불일치 |

### 다음 작업 (Sprint 1)
1. `src/crypto.py` - RSA 암호화 모듈 신규 작성
2. `src/codef_api.py` - API 스펙 기반 전면 재작성
3. `src/two_way.py` - 2-Way 추가인증 구현
4. `src/payment.py` - 전자민원캐시 결제 연동
5. GitHub Actions CI 워크플로우 설정

---

*최종 업데이트: 2026-03-28*
