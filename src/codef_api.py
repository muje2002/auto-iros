"""CODEF 부동산 등기부등본 API 클라이언트"""

import json
import urllib.parse
import requests
from dataclasses import dataclass

from .config import Config, REGISTER_API_PATH
from .auth import CodefAuth


# 등기 유형 코드
REGISTER_TYPES = {
    "전체": "0",
    "갑구": "1",
    "을구": "2",
    "표제부": "3",
}

# 부동산 구분 코드
PROPERTY_TYPES = {
    "토지": "0",
    "건물": "1",
    "집합건물": "2",
}

# 발급 유형
ISSUE_TYPES = {
    "열람": "0",
    "발급": "1",
}


@dataclass
class RegisterRequest:
    """등기부등본 요청 데이터"""

    address: str  # 부동산 소재지 주소
    dong: str = ""  # 동 (집합건물의 경우)
    ho: str = ""  # 호 (집합건물의 경우)
    property_type: str = "건물"  # 부동산 구분
    register_type: str = "전체"  # 등기 유형
    issue_type: str = "발급"  # 발급/열람
    unique_no: str = ""  # 부동산 고유번호 (알고 있는 경우)

    def to_api_params(self) -> dict:
        """API 요청 파라미터로 변환"""
        params = {
            "organization": "0002",  # 대법원 인터넷등기소
            "loginType": "5",  # 비회원
            "address": self.address,
            "realEstateType": PROPERTY_TYPES.get(self.property_type, "1"),
            "registerType": REGISTER_TYPES.get(self.register_type, "0"),
            "issueType": ISSUE_TYPES.get(self.issue_type, "1"),
        }
        if self.dong:
            params["dong"] = self.dong
        if self.ho:
            params["ho"] = self.ho
        if self.unique_no:
            params["uniqueNo"] = self.unique_no
        return params


@dataclass
class RegisterResult:
    """등기부등본 조회 결과"""

    address: str
    success: bool
    data: dict | None = None
    pdf_base64: str | None = None
    error_message: str | None = None


class CodefRegisterClient:
    """CODEF 등기부등본 API 클라이언트"""

    def __init__(self, config: Config):
        self.config = config
        self.auth = CodefAuth(config)
        self.api_url = config.base_url + REGISTER_API_PATH

    def request_register(self, req: RegisterRequest) -> RegisterResult:
        """등기부등본 조회 요청"""
        try:
            params = req.to_api_params()
            encoded_params = urllib.parse.urlencode(params)

            response = requests.post(
                self.api_url,
                headers=self.auth.get_headers(),
                data=encoded_params,
                timeout=120,
            )
            response.raise_for_status()

            result = response.json()
            result_data = result.get("data", {})

            # URL 디코딩 (CODEF 응답은 URL 인코딩되어 있음)
            if isinstance(result_data, str):
                result_data = json.loads(urllib.parse.unquote(result_data))

            code = result.get("result", {}).get("code", "")

            if code == "CF-00000":
                # 성공
                pdf_data = result_data.get("resRegisterEntriesPDF", "")
                return RegisterResult(
                    address=req.address,
                    success=True,
                    data=result_data,
                    pdf_base64=pdf_data if pdf_data else None,
                )
            elif code == "CF-03002":
                # 추가 인증 필요 (2-way)
                return RegisterResult(
                    address=req.address,
                    success=False,
                    data=result_data,
                    error_message=f"추가 인증이 필요합니다 (code: {code}). "
                    "2-way 인증을 처리해주세요.",
                )
            else:
                msg = result.get("result", {}).get("message", "알 수 없는 오류")
                return RegisterResult(
                    address=req.address,
                    success=False,
                    error_message=f"API 오류 [{code}]: {msg}",
                )

        except requests.exceptions.Timeout:
            return RegisterResult(
                address=req.address,
                success=False,
                error_message="API 요청 시간 초과 (120초)",
            )
        except requests.exceptions.RequestException as e:
            return RegisterResult(
                address=req.address,
                success=False,
                error_message=f"네트워크 오류: {e}",
            )
        except (json.JSONDecodeError, KeyError) as e:
            return RegisterResult(
                address=req.address,
                success=False,
                error_message=f"응답 파싱 오류: {e}",
            )

    def request_batch(
        self, requests_list: list[RegisterRequest]
    ) -> list[RegisterResult]:
        """여러 건의 등기부등본을 순차 조회"""
        results = []
        for req in requests_list:
            result = self.request_register(req)
            results.append(result)
        return results
