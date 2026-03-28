"""codef_api.py 단위테스트"""

from unittest.mock import patch

from src.codef_api import (
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
