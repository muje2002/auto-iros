"""codef_api.py 단위테스트"""

import json
import urllib.parse
from unittest.mock import MagicMock, patch

import requests as http_requests

from src.codef_api import (
    CodefRegisterClient,
    RegisterRequest,
    REALTY_TYPES,
    ISSUE_TYPES,
    INQUIRY_TYPES,
)


# to_api_params는 encrypt_password를 호출하므로 mock
_encrypt_mock = patch("src.codef_api.encrypt_password", return_value="ENCRYPTED")


class TestRegisterRequest:
    def test_default_values(self):
        req = RegisterRequest()
        assert req.inquiry_type == "간편검색"
        assert req.issue_type == "열람"
        assert req.realty_type == "토지+건물"

    def test_display_name_address(self):
        req = RegisterRequest(address="테헤란로 123")
        assert req.display_name == "테헤란로 123"

    def test_display_name_unique_no(self):
        req = RegisterRequest(unique_no="1101-2024-123456")
        assert "고유번호" in req.display_name

    def test_display_name_lot(self):
        req = RegisterRequest(addr_sido="서울", addr_dong="강남동", addr_lot_number="123")
        assert "서울" in req.display_name

    @_encrypt_mock
    def test_to_api_params_simple_search(self, _mock, mock_config):
        req = RegisterRequest(
            inquiry_type="간편검색",
            address="테헤란로",
            issue_type="열람",
        )
        params = req.to_api_params(mock_config)
        assert params["organization"] == "0002"
        assert params["inquiryType"] == "1"
        assert params["issueType"] == "1"
        assert params["address"] == "테헤란로"
        assert params["phoneNo"] == mock_config.phone_no
        assert "password" in params

    @_encrypt_mock
    def test_simple_search_jiphap_merges_dong_ho(self, _mock, mock_config):
        """간편검색 + 집합건물 → dong/ho가 address에 병합"""
        req = RegisterRequest(
            inquiry_type="간편검색",
            address="테헤란로 152",
            realty_type="집합건물",
            dong="101동",
            ho="202호",
        )
        params = req.to_api_params(mock_config)
        assert params["address"] == "테헤란로 152 101동 202호"

    @_encrypt_mock
    def test_simple_search_jiphap_no_dong(self, _mock, mock_config):
        """간편검색 + 집합건물 + dong 없음 → address 그대로"""
        req = RegisterRequest(
            inquiry_type="간편검색",
            address="테헤란로 152",
            realty_type="집합건물",
        )
        params = req.to_api_params(mock_config)
        assert params["address"] == "테헤란로 152"

    @_encrypt_mock
    def test_simple_search_non_jiphap_ignores_dong(self, _mock, mock_config):
        """간편검색 + 토지+건물 → dong/ho 입력되어도 address에 병합 안 함"""
        req = RegisterRequest(
            inquiry_type="간편검색",
            address="테헤란로 152",
            realty_type="토지+건물",
            dong="101동",
            ho="202호",
        )
        params = req.to_api_params(mock_config)
        assert params["address"] == "테헤란로 152"

    @_encrypt_mock
    def test_to_api_params_unique_no(self, _mock, mock_config):
        req = RegisterRequest(
            inquiry_type="고유번호",
            unique_no="1101-2024-123456",
        )
        params = req.to_api_params(mock_config)
        assert params["inquiryType"] == "0"
        assert params["uniqueNo"] == "1101-2024-123456"

    @_encrypt_mock
    def test_to_api_params_lot_address(self, _mock, mock_config):
        req = RegisterRequest(
            inquiry_type="소재지번",
            addr_sido="서울",
            addr_dong="강남동",
            addr_lot_number="123-45",
        )
        params = req.to_api_params(mock_config)
        assert params["inquiryType"] == "2"
        assert params["addr_sido"] == "서울"
        assert params["addr_dong"] == "강남동"
        assert params["addr_lotNumber"] == "123-45"

    @_encrypt_mock
    def test_to_api_params_road_address(self, _mock, mock_config):
        req = RegisterRequest(
            inquiry_type="도로명주소",
            addr_sido="서울",
            addr_sigungu="강남구",
            addr_road_name="테헤란로",
            addr_building_number="123",
        )
        params = req.to_api_params(mock_config)
        assert params["inquiryType"] == "3"
        assert params["addr_roadName"] == "테헤란로"
        assert params["addr_buildingNumber"] == "123"

    @_encrypt_mock
    def test_realty_type_default_included(self, _mock, mock_config):
        """토지+건물(기본값)도 realtyType=0으로 전송 (CF-13007 수정)"""
        req = RegisterRequest(address="테헤란로", realty_type="토지+건물")
        params = req.to_api_params(mock_config)
        assert params["realtyType"] == "0"

    @_encrypt_mock
    def test_realty_type_jiphap(self, _mock, mock_config):
        req = RegisterRequest(address="테헤란로", realty_type="집합건물")
        params = req.to_api_params(mock_config)
        assert params["realtyType"] == "1"

    @_encrypt_mock
    def test_realty_type_toji(self, _mock, mock_config):
        req = RegisterRequest(address="테헤란로", realty_type="토지")
        params = req.to_api_params(mock_config)
        assert params["realtyType"] == "2"

    @_encrypt_mock
    def test_realty_type_building(self, _mock, mock_config):
        req = RegisterRequest(address="테헤란로", realty_type="건물")
        params = req.to_api_params(mock_config)
        assert params["realtyType"] == "3"

    @_encrypt_mock
    def test_to_api_params_with_payment(self, _mock, mock_config_with_payment):
        req = RegisterRequest(issue_type="발급")
        params = req.to_api_params(mock_config_with_payment)
        assert params["ePrepayNo"] == "123456789012"

    @_encrypt_mock
    def test_to_api_params_no_payment_for_query(self, _mock, mock_config_with_payment):
        req = RegisterRequest(issue_type="고유번호조회")
        params = req.to_api_params(mock_config_with_payment)
        assert "ePrepayNo" not in params


class TestCodeMappings:
    def test_realty_types(self):
        assert REALTY_TYPES["토지+건물"] == "0"
        assert REALTY_TYPES["집합건물"] == "1"
        assert REALTY_TYPES["토지"] == "2"
        assert REALTY_TYPES["건물"] == "3"

    def test_issue_types(self):
        assert ISSUE_TYPES["발급"] == "0"
        assert ISSUE_TYPES["열람"] == "1"
        assert ISSUE_TYPES["고유번호조회"] == "2"

    def test_inquiry_types(self):
        assert INQUIRY_TYPES["고유번호"] == "0"
        assert INQUIRY_TYPES["간편검색"] == "1"
        assert INQUIRY_TYPES["소재지번"] == "2"
        assert INQUIRY_TYPES["도로명주소"] == "3"


def _make_codef_response(code: str, data: dict | None = None) -> str:
    """CODEF 응답 JSON 문자열 생성 헬퍼"""
    resp = {
        "result": {"code": code, "message": f"msg-{code}"},
        "data": data or {},
    }
    return json.dumps(resp)


def _mock_post_response(body_text: str, status_code: int = 200) -> MagicMock:
    """requests.post 반환값 mock 생성"""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = body_text
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


@patch("src.codef_api.encrypt_password", return_value="ENCRYPTED")
@patch("src.codef_api.CodefAuth")
class TestCodefRegisterClient:
    """CodefRegisterClient 응답 파싱 / 재시도 / 타임아웃 테스트"""

    def _make_client(self, mock_auth_cls, mock_config):
        mock_auth_cls.return_value.get_headers.return_value = {
            "Authorization": "Bearer test"
        }
        return CodefRegisterClient(mock_config)

    # --- 응답 파싱 ---

    def test_success_cf00000(self, mock_auth_cls, _enc, mock_config):
        client = self._make_client(mock_auth_cls, mock_config)
        body = _make_codef_response("CF-00000", {"resOriGinalData": "cGRm"})
        with patch("src.codef_api.requests.post", return_value=_mock_post_response(body)):
            result = client.request_register(RegisterRequest(address="test"))
        assert result.success is True
        assert result.pdf_base64 == "cGRm"

    def test_two_way_cf03002(self, mock_auth_cls, _enc, mock_config):
        client = self._make_client(mock_auth_cls, mock_config)
        data = {
            "resAddrList": [{"address": "A", "uniqueNo": "001"}],
            "jobIndex": "j1",
            "threadIndex": "t1",
            "jti": "abc",
            "twoWayTimestamp": "ts1",
        }
        body = _make_codef_response("CF-03002", data)
        with patch("src.codef_api.requests.post", return_value=_mock_post_response(body)):
            result = client.request_register(RegisterRequest(address="test"))
        assert result.need_two_way is True
        assert len(result.addr_list) == 1
        assert result.two_way_info["jobIndex"] == "j1"

    def test_two_way_addr_list_normalized(self, mock_auth_cls, _enc, mock_config):
        """API 필드명(commUniqueNo 등)이 내부 필드명(uniqueNo 등)으로 정규화"""
        client = self._make_client(mock_auth_cls, mock_config)
        data = {
            "resAddrList": [
                {
                    "commUniqueNo": "1101-2024-000001",
                    "commAddrLotNumber": "서울 강남구 테헤란로 152",
                    "resUserNm": "홍길동",
                    "resState": "현행",
                    "resType": "집합건물",
                },
            ],
            "jobIndex": "0",
            "threadIndex": "0",
            "jti": "abc",
            "twoWayTimestamp": "123",
        }
        body = _make_codef_response("CF-03002", data)
        with patch("src.codef_api.requests.post", return_value=_mock_post_response(body)):
            result = client.request_register(RegisterRequest(address="test"))
        assert result.need_two_way is True
        addr = result.addr_list[0]
        assert addr["uniqueNo"] == "1101-2024-000001"
        assert addr["address"] == "서울 강남구 테헤란로 152"
        assert addr["owner"] == "홍길동"
        assert addr["realtyType"] == "집합건물"

    def test_two_way_addr_list_fallback_fields(self, mock_auth_cls, _enc, mock_config):
        """기존 필드명(uniqueNo, address)도 fallback으로 지원"""
        client = self._make_client(mock_auth_cls, mock_config)
        data = {
            "resAddrList": [{"uniqueNo": "U001", "address": "기존주소"}],
            "jobIndex": "0", "threadIndex": "0", "jti": "x", "twoWayTimestamp": "0",
        }
        body = _make_codef_response("CF-03002", data)
        with patch("src.codef_api.requests.post", return_value=_mock_post_response(body)):
            result = client.request_register(RegisterRequest(address="test"))
        addr = result.addr_list[0]
        assert addr["uniqueNo"] == "U001"
        assert addr["address"] == "기존주소"

    def test_error_code(self, mock_auth_cls, _enc, mock_config):
        client = self._make_client(mock_auth_cls, mock_config)
        body = _make_codef_response("CF-12000")
        with patch("src.codef_api.requests.post", return_value=_mock_post_response(body)):
            result = client.request_register(RegisterRequest(address="test"))
        assert result.success is False
        assert result.code == "CF-12000"

    def test_parse_url_encoded_response(self, mock_auth_cls, _enc, mock_config):
        client = self._make_client(mock_auth_cls, mock_config)
        inner = {"resOriGinalData": "pdf"}
        data_encoded = urllib.parse.quote_plus(json.dumps(inner))
        resp = {"result": {"code": "CF-00000", "message": "ok"}, "data": data_encoded}
        body = urllib.parse.quote_plus(json.dumps(resp))
        with patch("src.codef_api.requests.post", return_value=_mock_post_response(body)):
            result = client.request_register(RegisterRequest(address="test"))
        assert result.success is True
        assert result.pdf_base64 == "pdf"

    # --- 타임아웃 / 네트워크 ---

    def test_timeout_handling(self, mock_auth_cls, _enc, mock_config):
        client = self._make_client(mock_auth_cls, mock_config)
        with patch("src.codef_api.requests.post", side_effect=http_requests.exceptions.Timeout):
            result = client.request_register(RegisterRequest(address="test"))
        assert result.success is False
        assert "시간 초과" in result.error_message

    def test_network_error(self, mock_auth_cls, _enc, mock_config):
        client = self._make_client(mock_auth_cls, mock_config)
        with patch("src.codef_api.requests.post", side_effect=http_requests.exceptions.ConnectionError("refused")):
            with patch("src.codef_api.time.sleep"):
                result = client.request_register(RegisterRequest(address="test"))
        assert result.success is False
        assert "네트워크" in result.error_message

    def test_two_way_uses_second_timeout(self, mock_auth_cls, _enc, mock_config):
        client = self._make_client(mock_auth_cls, mock_config)
        body = _make_codef_response("CF-00000", {})
        with patch("src.codef_api.requests.post", return_value=_mock_post_response(body)) as mock_post:
            client._do_request(
                RegisterRequest(address="test"),
                is_two_way=True,
                two_way_info={"jobIndex": "1"},
            )
        _, kwargs = mock_post.call_args
        assert kwargs["timeout"] == 120

    def test_two_way_params_injected(self, mock_auth_cls, _enc, mock_config):
        client = self._make_client(mock_auth_cls, mock_config)
        body = _make_codef_response("CF-00000", {})
        with patch("src.codef_api.requests.post", return_value=_mock_post_response(body)) as mock_post:
            client._do_request(
                RegisterRequest(address="test"),
                is_two_way=True,
                two_way_info={
                    "uniqueNo": "U001",
                    "jobIndex": "j1",
                    "threadIndex": "t1",
                    "jti": "abc",
                    "twoWayTimestamp": "123",
                },
            )
        sent_json = mock_post.call_args[1]["json"]
        assert sent_json["is2Way"] is True
        assert sent_json["uniqueNo"] == "U001"
        assert sent_json["twoWayInfo"]["jobIndex"] == "j1"
        assert sent_json["twoWayInfo"]["jti"] == "abc"

    # --- 재시도 로직 ---

    def test_retry_on_retryable_error(self, mock_auth_cls, _enc, mock_config):
        client = self._make_client(mock_auth_cls, mock_config)
        fail_body = _make_codef_response("CF-10000")
        ok_body = _make_codef_response("CF-00000", {"resOriGinalData": "ok"})
        responses = [
            _mock_post_response(fail_body),
            _mock_post_response(fail_body),
            _mock_post_response(ok_body),
        ]
        with patch("src.codef_api.requests.post", side_effect=responses):
            with patch("src.codef_api.time.sleep"):
                result = client.request_register(RegisterRequest(address="test"))
        assert result.success is True

    def test_no_retry_on_non_retryable(self, mock_auth_cls, _enc, mock_config):
        client = self._make_client(mock_auth_cls, mock_config)
        body = _make_codef_response("CF-13002")
        with patch("src.codef_api.requests.post", return_value=_mock_post_response(body)) as mock_post:
            result = client.request_register(RegisterRequest(address="test"))
        assert result.success is False
        assert mock_post.call_count == 1

    def test_max_retries_exhausted(self, mock_auth_cls, _enc, mock_config):
        client = self._make_client(mock_auth_cls, mock_config)
        body = _make_codef_response("CF-10000")
        with patch("src.codef_api.requests.post", return_value=_mock_post_response(body)) as mock_post:
            with patch("src.codef_api.time.sleep"):
                result = client.request_register(RegisterRequest(address="test"))
        assert result.success is False
        assert result.code == "CF-10000"
        assert mock_post.call_count == 3

    # --- 배치 ---

    def test_batch_delay(self, mock_auth_cls, _enc, mock_config):
        client = self._make_client(mock_auth_cls, mock_config)
        body = _make_codef_response("CF-00000", {})
        reqs = [RegisterRequest(address=f"addr{i}") for i in range(3)]
        with patch("src.codef_api.requests.post", return_value=_mock_post_response(body)):
            with patch("src.codef_api.time.sleep") as mock_sleep:
                client.request_batch(reqs)
        assert mock_sleep.call_count == 2
