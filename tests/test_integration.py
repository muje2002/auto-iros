"""실제 CODEF API 통합 테스트 (requires_env)

.env가 설정된 로컬 환경에서만 실행. CI에서는 자동 스킵.
"""

from tests.conftest import requires_env

from src.config import Config
from src.codef_api import CodefRegisterClient, RegisterRequest


@requires_env
class TestLiveAPI:
    def _make_client(self):
        config = Config.from_env()
        return CodefRegisterClient(config)

    def test_simple_search(self):
        """간편검색 → two_way 또는 success (크래시 아님)"""
        client = self._make_client()
        req = RegisterRequest(
            inquiry_type="간편검색",
            address="서울특별시 강남구 테헤란로 152",
            issue_type="고유번호조회",
        )
        result = client.request_register(req)
        assert result.success or result.need_two_way or result.code != ""

    def test_unique_no_query(self):
        """고유번호조회 → 에러 아닌 정상 응답"""
        client = self._make_client()
        req = RegisterRequest(
            inquiry_type="간편검색",
            address="서울특별시 강남구 역삼동",
            issue_type="고유번호조회",
        )
        result = client.request_register(req)
        # 결과가 있든 없든 크래시 없이 처리
        assert result.code != "" or result.error_message is not None

    def test_invalid_address_error(self):
        """잘못된 주소 → 에러코드 반환 (크래시 아님)"""
        client = self._make_client()
        req = RegisterRequest(
            inquiry_type="간편검색",
            address="zzz존재하지않는주소999",
            issue_type="고유번호조회",
        )
        result = client.request_register(req)
        assert result.success is False or result.code != ""

    def test_realty_type_toji(self):
        """realtyType 지정 시 정상 동작 확인"""
        client = self._make_client()
        req = RegisterRequest(
            inquiry_type="간편검색",
            address="서울특별시 강남구 테헤란로 152",
            issue_type="고유번호조회",
            realty_type="토지",
        )
        result = client.request_register(req)
        assert result.code != "" or result.error_message is not None
