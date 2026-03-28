"""공통 테스트 fixture"""

import os
import pytest
from unittest.mock import patch

from src.config import Config


@pytest.fixture
def mock_config() -> Config:
    """테스트용 Config (실제 API 호출 없이 사용)"""
    return Config(
        client_id="test_client_id",
        client_secret="test_client_secret",
        base_url="https://development.codef.io",
        output_dir="./test_output",
        phone_no="01012345678",
        password="1234",
        eprepay_no="",
        eprepay_pass="",
    )


@pytest.fixture
def mock_config_with_payment() -> Config:
    """결제 정보 포함 Config"""
    return Config(
        client_id="test_client_id",
        client_secret="test_client_secret",
        base_url="https://development.codef.io",
        output_dir="./test_output",
        phone_no="01012345678",
        password="1234",
        eprepay_no="123456789012",
        eprepay_pass="test_pass",
    )


def _can_load_config() -> bool:
    """실제 .env가 있고 Config.from_env()가 성공하는지 확인"""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if not os.path.exists(env_path):
        return False
    try:
        Config.from_env()
        return True
    except ValueError:
        return False


# 실제 API 키가 있을 때만 실행하는 마커
requires_env = pytest.mark.skipif(
    not _can_load_config(),
    reason=".env 미설정 - 실제 API 테스트 스킵",
)


@pytest.fixture
def test_client():
    """FastAPI TestClient (Config mock 적용)"""
    with patch.object(Config, "from_env") as mock_from_env:
        mock_from_env.return_value = Config(
            client_id="test",
            client_secret="test",
            base_url="https://development.codef.io",
            output_dir="./test_output",
            phone_no="01012345678",
            password="1234",
            eprepay_no="",
            eprepay_pass="",
        )
        from fastapi.testclient import TestClient
        from app import app

        # startup 이벤트가 mock config를 사용하도록
        app.state.config = mock_from_env.return_value
        yield TestClient(app, raise_server_exceptions=False)
