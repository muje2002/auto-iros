"""CODEF 부동산 등기부등본 API 클라이언트"""

import json
import logging
import time
import urllib.parse
from dataclasses import dataclass, field

import requests

from .auth import CodefAuth
from .config import (
    API_TIMEOUT_FIRST,
    API_TIMEOUT_SECOND,
    Config,
    REGISTER_API_PATH,
)
from .crypto import encrypt_password
from .errors import get_error_message, is_retryable_error

logger = logging.getLogger(__name__)

# 재시도 설정
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2  # 초 (지수 백오프: 2, 4, 8)

# 배치 요청 간 딜레이 (IP 차단 방지)
BATCH_REQUEST_DELAY = 1.5  # 초

# 부동산 구분 코드 (API 스펙 기준)
REALTY_TYPES = {
    "토지+건물": "0",
    "집합건물": "1",
    "토지": "2",
    "건물": "3",
}

# 발급 유형 코드 (API 스펙 기준)
ISSUE_TYPES = {
    "발급": "0",
    "열람": "1",
    "고유번호조회": "2",
    "원문데이터": "3",
}

# 조회 구분 코드
INQUIRY_TYPES = {
    "고유번호": "0",
    "간편검색": "1",
    "소재지번": "2",
    "도로명주소": "3",
}

# 등기 유형 코드 (등기사항 선택)
REGISTER_TYPES = {
    "전체": "0",
    "갑구": "1",
    "을구": "2",
    "표제부": "3",
}


@dataclass
class RegisterRequest:
    """등기부등본 요청 데이터"""

    # 조회 방식
    inquiry_type: str = "간편검색"  # 고유번호/간편검색/소재지번/도로명주소

    # 공통
    address: str = ""  # 간편검색 시 검색어 / 기타 용도
    unique_no: str = ""  # 고유번호 (inquiryType=0)
    realty_type: str = "토지+건물"  # 부동산 구분
    issue_type: str = "열람"  # 발급/열람/고유번호조회/원문데이터
    register_type: str = "전체"  # 등기 유형

    # 집합건물
    dong: str = ""
    ho: str = ""

    # 소재지번 (inquiryType=2)
    addr_sido: str = ""
    addr_dong: str = ""
    addr_lot_number: str = ""
    input_select: str = ""  # 0:지번, 1:건물명칭
    building_name: str = ""

    # 도로명주소 (inquiryType=3)
    addr_sigungu: str = ""
    addr_road_name: str = ""
    addr_building_number: str = ""

    # 간편검색 옵션
    record_status: str = "0"  # 0:현행, 1:폐쇄, 2:현행+폐쇄
    start_page_no: str = ""
    page_count: str = ""

    # 추가 옵션
    joint_mortgage_jeonse_yn: str = "0"
    trading_yn: str = "0"
    list_number: str = ""
    electronic_closed_yn: str = "0"
    warning_skip_yn: str = "0"
    register_summary_yn: str = "0"
    application_type: str = "0"
    select_address: str = "0"
    is_identity_view_yn: str = "0"
    identity_list: list[dict] = field(default_factory=list)
    origin_data_yn: str = "1"  # 1: 원문Data(PDF) 포함 — 발급/열람 시 PDF 받기 위해 필수

    def to_api_params(self, config: Config) -> dict:
        """API 요청 파라미터로 변환"""
        inquiry_code = INQUIRY_TYPES.get(self.inquiry_type, "1")

        params: dict[str, object] = {
            "organization": "0002",
            "phoneNo": config.phone_no,
            "password": encrypt_password(config.password),
            "inquiryType": inquiry_code,
            "issueType": ISSUE_TYPES.get(self.issue_type, "1"),
            "jointMortgageJeonseYN": self.joint_mortgage_jeonse_yn,
            "tradingYN": self.trading_yn,
            "warningSkipYN": self.warning_skip_yn,
            "registerSummaryYN": self.register_summary_yn,
            "applicationType": self.application_type,
            "selectAddress": self.select_address,
            "isIdentityViewYn": self.is_identity_view_yn,
            "originDataYN": self.origin_data_yn,
        }

        # 부동산 구분 (항상 전송 — 생략 시 CF-13007 과다 검색 발생 가능)
        params["realtyType"] = REALTY_TYPES.get(self.realty_type, "0")

        # 동/호
        if self.dong:
            params["dong"] = self.dong
        if self.ho:
            params["ho"] = self.ho

        # 결제 정보 (발급/열람 시)
        issue_code = ISSUE_TYPES.get(self.issue_type, "1")
        if issue_code in ("0", "1") and config.eprepay_no:
            params["ePrepayNo"] = config.eprepay_no
            params["ePrepayPass"] = config.eprepay_pass

        # 주민등록번호 리스트
        if self.is_identity_view_yn == "1" and self.identity_list:
            params["identityList"] = self.identity_list

        # inquiryType별 파라미터
        if inquiry_code == "0":
            # 고유번호
            params["uniqueNo"] = self.unique_no
        elif inquiry_code == "1":
            # 간편검색 — dong/ho는 간편검색에서 무시되므로 address에 병합
            address = self.address
            if self.realty_type == "집합건물" and (self.dong or self.ho):
                parts = [address]
                if self.dong:
                    parts.append(self.dong)
                if self.ho:
                    parts.append(self.ho)
                address = " ".join(parts)
            params["address"] = address
            if self.addr_sido:
                params["addr_sido"] = self.addr_sido
            params["recordStatus"] = self.record_status
            if self.start_page_no:
                params["startPageNo"] = self.start_page_no
            if self.page_count:
                params["pageCount"] = self.page_count
        elif inquiry_code == "2":
            # 소재지번
            params["addr_sido"] = self.addr_sido
            params["addr_dong"] = self.addr_dong
            params["addr_lotNumber"] = self.addr_lot_number
            if self.realty_type == "집합건물":
                params["inputSelect"] = self.input_select
                if self.input_select == "1":
                    params["buildingName"] = self.building_name
            if self.electronic_closed_yn != "0":
                params["electronicClosedYN"] = self.electronic_closed_yn
        elif inquiry_code == "3":
            # 도로명주소
            params["addr_sido"] = self.addr_sido
            params["addr_sigungu"] = self.addr_sigungu
            params["addr_roadName"] = self.addr_road_name
            params["addr_buildingNumber"] = self.addr_building_number
            if self.electronic_closed_yn != "0":
                params["electronicClosedYN"] = self.electronic_closed_yn

        # 목록번호
        if self.list_number:
            params["listNumber"] = self.list_number

        return params

    @property
    def display_name(self) -> str:
        """표시용 이름 (주소 또는 고유번호)"""
        if self.address:
            return self.address
        if self.unique_no:
            return f"고유번호:{self.unique_no}"
        parts = [self.addr_sido, self.addr_dong, self.addr_lot_number]
        return " ".join(p for p in parts if p) or "(주소 없음)"


@dataclass
class RegisterResult:
    """등기부등본 조회 결과"""

    request: RegisterRequest
    success: bool
    code: str = ""
    message: str = ""
    data: dict | None = None
    pdf_base64: str | None = None
    error_message: str | None = None
    # 2-Way 추가인증용
    need_two_way: bool = False
    two_way_info: dict | None = None
    addr_list: list[dict] | None = None


class CodefRegisterClient:
    """CODEF 등기부등본 API 클라이언트"""

    def __init__(self, config: Config):
        self.config = config
        self.auth = CodefAuth(config)
        self.api_url = config.base_url + REGISTER_API_PATH

    def _parse_response(self, response_json: dict) -> dict:
        """CODEF 응답 파싱 (URL 디코딩 처리)"""
        data = response_json.get("data", {})
        if isinstance(data, str):
            data = json.loads(urllib.parse.unquote_plus(data))
        return data

    def request_register(
        self,
        req: RegisterRequest,
        *,
        is_two_way: bool = False,
        two_way_info: dict | None = None,
    ) -> RegisterResult:
        """등기부등본 조회 요청 (네트워크 오류 시 자동 재시도)

        Args:
            req: 등기부등본 요청 데이터
            is_two_way: 2-Way 추가인증 2차 요청 여부
            two_way_info: 2-Way 추가인증 정보 (jobIndex, threadIndex 등)
        """
        last_result: RegisterResult | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            result = self._do_request(req, is_two_way=is_two_way, two_way_info=two_way_info)

            # 성공 또는 2-Way → 즉시 반환
            if result.success or result.need_two_way:
                return result

            # API 에러 중 재시도 가능한 경우만 재시도
            if result.code and is_retryable_error(result.code) and attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY ** attempt
                logger.info(
                    "재시도 %d/%d (코드: %s, %d초 후)",
                    attempt, MAX_RETRIES, result.code, delay,
                )
                time.sleep(delay)
                last_result = result
                continue

            # 네트워크 오류 (code 없음) → 재시도
            if not result.code and attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY ** attempt
                logger.info(
                    "네트워크 오류 재시도 %d/%d (%d초 후): %s",
                    attempt, MAX_RETRIES, delay, result.error_message,
                )
                time.sleep(delay)
                last_result = result
                continue

            return result

        return last_result or RegisterResult(
            request=req, success=False, error_message="최대 재시도 횟수 초과",
        )

    def _do_request(
        self,
        req: RegisterRequest,
        *,
        is_two_way: bool = False,
        two_way_info: dict | None = None,
    ) -> RegisterResult:
        """실제 API 호출 수행 (1회)"""
        try:
            params = req.to_api_params(self.config)

            if is_two_way and two_way_info:
                params["is2Way"] = True
                params["uniqueNo"] = two_way_info.get("uniqueNo", "")
                params["twoWayInfo"] = {
                    "jobIndex": two_way_info.get("jobIndex", ""),
                    "threadIndex": two_way_info.get("threadIndex", ""),
                    "jti": two_way_info.get("jti", ""),
                    "twoWayTimestamp": two_way_info.get("twoWayTimestamp", ""),
                }

            logger.info("API 요청 파라미터: %s", {k: v for k, v in params.items() if k != "password"})

            timeout = API_TIMEOUT_SECOND if is_two_way else API_TIMEOUT_FIRST

            response = requests.post(
                self.api_url,
                headers=self.auth.get_headers(),
                json=params,
                timeout=timeout,
            )
            response.raise_for_status()

            # CODEF 응답: JSON 또는 URL 인코딩된 JSON (text/plain)
            # unquote_plus: %XX 디코딩 + '+'를 공백으로 변환
            body = response.text
            decoded = urllib.parse.unquote_plus(body)
            result_json = json.loads(decoded)
            result_data = self._parse_response(result_json)

            code = result_json.get("result", {}).get("code", "")
            message = result_json.get("result", {}).get("message", "")

            if code == "CF-00000":
                pdf_data = result_data.get("resOriGinalData", "")
                return RegisterResult(
                    request=req,
                    success=True,
                    code=code,
                    message=message,
                    data=result_data,
                    pdf_base64=pdf_data if pdf_data else None,
                )
            elif code == "CF-03002":
                # resAddrList는 extraInfo 내부에 위치
                extra_info = result_data.get("extraInfo", {})
                raw_addr_list = extra_info.get("resAddrList", result_data.get("resAddrList", []))
                # API 필드명 → 내부 필드명 정규화 (commUniqueNo → uniqueNo 등)
                addr_list = []
                for item in raw_addr_list:
                    addr_list.append({
                        "uniqueNo": item.get("commUniqueNo", item.get("uniqueNo", "")),
                        "address": item.get("commAddrLotNumber", item.get("address", item.get("resAddr", ""))),
                        "owner": item.get("resUserNm", ""),
                        "state": item.get("resState", ""),
                        "realtyType": item.get("resType", item.get("realtyType", "")),
                    })
                # twoWayInfo는 data 최상위에 위치
                ti = {
                    "jobIndex": result_data.get("jobIndex", ""),
                    "threadIndex": result_data.get("threadIndex", ""),
                    "jti": result_data.get("jti", ""),
                    "twoWayTimestamp": result_data.get("twoWayTimestamp", ""),
                }
                return RegisterResult(
                    request=req,
                    success=False,
                    code=code,
                    message=message,
                    data=result_data,
                    need_two_way=True,
                    two_way_info=ti,
                    addr_list=addr_list,
                )
            else:
                return RegisterResult(
                    request=req,
                    success=False,
                    code=code,
                    message=message,
                    data=result_data,
                    error_message=get_error_message(code, message),
                )

        except requests.exceptions.Timeout:
            timeout_sec = API_TIMEOUT_SECOND if is_two_way else API_TIMEOUT_FIRST
            return RegisterResult(
                request=req,
                success=False,
                error_message=f"API 요청 시간 초과 ({timeout_sec}초)",
            )
        except requests.exceptions.RequestException as e:
            return RegisterResult(
                request=req,
                success=False,
                error_message=f"네트워크 오류: {e}",
            )
        except (json.JSONDecodeError, KeyError) as e:
            return RegisterResult(
                request=req,
                success=False,
                error_message=f"응답 파싱 오류: {e}",
            )

    def request_batch(
        self, requests_list: list[RegisterRequest]
    ) -> list[RegisterResult]:
        """여러 건의 등기부등본을 순차 조회 (요청 간 딜레이 적용)"""
        results = []
        for i, req in enumerate(requests_list):
            if i > 0:
                time.sleep(BATCH_REQUEST_DELAY)
            result = self.request_register(req)
            results.append(result)
        return results
