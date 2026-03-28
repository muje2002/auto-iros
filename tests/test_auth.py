"""auth.py 단위테스트 + 실제 CODEF 데모 연동 테스트"""

import time
from unittest.mock import MagicMock, patch


from src.auth import CodefAuth
from src.config import Config
from tests.conftest import requires_env


class TestCodefAuthUnit:
    """단위 테스트 (mock, 외부 호출 없음)"""

    def test_token_caching(self, mock_config: Config):
        """토큰이 캐시되어 재사용되는지 확인"""
        auth = CodefAuth(mock_config)

        with patch.object(auth, "_request_token", return_value="test_token") as mock_req:
            # 첫 번째 호출 → _request_token 실행
            token1 = auth.get_token()
            assert token1 == "test_token"
            assert mock_req.call_count == 1

            # 캐시가 유효하도록 만료 시간 설정
            auth._token_expires_at = time.time() + 3600

            # 두 번째 호출 → 캐시에서 반환
            token2 = auth.get_token()
            assert token2 == "test_token"
            assert mock_req.call_count == 1  # 추가 호출 없음

    def test_token_refresh_on_expiry(self, mock_config: Config):
        """토큰 만료 시 자동 갱신되는지 확인"""
        auth = CodefAuth(mock_config)

        with patch.object(auth, "_request_token", return_value="token_v1") as mock_req:
            auth.get_token()
            assert mock_req.call_count == 1

            # 만료 시뮬레이션
            auth._token_expires_at = time.time() - 1
            mock_req.return_value = "token_v2"

            token = auth.get_token()
            assert token == "token_v2"
            assert mock_req.call_count == 2

    def test_get_headers_format(self, mock_config: Config):
        """헤더 형식 확인"""
        auth = CodefAuth(mock_config)

        with patch.object(auth, "get_token", return_value="my_token"):
            headers = auth.get_headers()
            assert headers["Authorization"] == "Bearer my_token"
            assert headers["Content-Type"] == "application/json"

    def test_request_token_sends_correct_params(self, mock_config: Config):
        """토큰 요청 시 올바른 파라미터가 전송되는지 확인"""
        auth = CodefAuth(mock_config)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "abc123",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("src.auth.requests.post", return_value=mock_response) as mock_post:
            token = auth._request_token()
            assert token == "abc123"

            call_kwargs = mock_post.call_args
            assert call_kwargs.kwargs["data"]["grant_type"] == "client_credentials"
            assert call_kwargs.kwargs["data"]["scope"] == "read"
            assert "Basic " in call_kwargs.kwargs["headers"]["Authorization"]


class TestCodefAuthLive:
    """실제 CODEF 데모 API 연동 테스트 (.env 필요)"""

    @requires_env
    def test_live_token_issuance(self):
        """실제 데모 API에서 토큰 발급 확인"""
        config = Config.from_env()
        auth = CodefAuth(config)
        token = auth.get_token()

        assert token is not None
        assert len(token) > 10
        print(f"토큰 발급 성공: {token[:20]}...")
