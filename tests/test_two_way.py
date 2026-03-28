"""two_way.py 단위테스트"""

from src.codef_api import RegisterRequest, RegisterResult
from src.two_way import build_two_way_params


class TestBuildTwoWayParams:
    def test_basic(self):
        result = RegisterResult(
            request=RegisterRequest(address="test"),
            success=False,
            need_two_way=True,
            two_way_info={
                "jobIndex": "1",
                "threadIndex": "2",
                "jti": "abc",
                "twoWayTimestamp": "12345",
            },
        )
        selected = {"uniqueNo": "1101-2024-000001", "address": "서울 강남구"}

        params = build_two_way_params(result, selected)
        assert params["uniqueNo"] == "1101-2024-000001"
        assert params["jobIndex"] == "1"
        assert params["threadIndex"] == "2"
        assert params["jti"] == "abc"

    def test_does_not_mutate_original(self):
        original_info = {"jobIndex": "1", "threadIndex": "2"}
        result = RegisterResult(
            request=RegisterRequest(),
            success=False,
            need_two_way=True,
            two_way_info=original_info,
        )
        selected = {"uniqueNo": "XXX"}

        params = build_two_way_params(result, selected)
        assert "uniqueNo" in params
        assert "uniqueNo" not in original_info  # 원본 미변경

    def test_empty_two_way_info(self):
        result = RegisterResult(
            request=RegisterRequest(),
            success=False,
            need_two_way=True,
            two_way_info=None,
        )
        params = build_two_way_params(result, {"uniqueNo": "XXX"})
        assert params["uniqueNo"] == "XXX"
