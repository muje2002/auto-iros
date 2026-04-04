"""config.py 단위테스트"""

import os
from unittest.mock import patch

import pytest

from src.config import Config, CODEF_URLS


# load_dotenv()는 모듈 임포트 시 이미 실행됨 — os.environ 패치로 격리
_VALID_ENV = {
    "CODEF_CLIENT_ID": "test-id",
    "CODEF_CLIENT_SECRET": "test-secret",
    "CODEF_PHONE_NO": "01012345678",
    "CODEF_PASSWORD": "1234",
}


class TestConfigFromEnv:
    @patch.dict(os.environ, _VALID_ENV, clear=True)
    def test_valid_env(self):
        config = Config.from_env()
        assert config.client_id == "test-id"
        assert config.client_secret == "test-secret"
        assert config.phone_no == "01012345678"
        assert config.password == "1234"

    @patch.dict(os.environ, {
        "CODEF_CLIENT_SECRET": "s", "CODEF_PHONE_NO": "010", "CODEF_PASSWORD": "1234",
    }, clear=True)
    def test_missing_client_id_raises(self):
        with pytest.raises(ValueError, match="CODEF_CLIENT_ID"):
            Config.from_env()

    @patch.dict(os.environ, {
        "CODEF_CLIENT_ID": "i", "CODEF_PHONE_NO": "010", "CODEF_PASSWORD": "1234",
    }, clear=True)
    def test_missing_client_secret_raises(self):
        with pytest.raises(ValueError, match="CODEF_CLIENT_SECRET"):
            Config.from_env()

    @patch.dict(os.environ, {
        "CODEF_CLIENT_ID": "i", "CODEF_CLIENT_SECRET": "s", "CODEF_PASSWORD": "1234",
    }, clear=True)
    def test_missing_phone_raises(self):
        with pytest.raises(ValueError, match="CODEF_PHONE_NO"):
            Config.from_env()

    @patch.dict(os.environ, {
        "CODEF_CLIENT_ID": "i", "CODEF_CLIENT_SECRET": "s", "CODEF_PHONE_NO": "010",
    }, clear=True)
    def test_missing_password_raises(self):
        with pytest.raises(ValueError, match="CODEF_PASSWORD"):
            Config.from_env()

    @patch.dict(os.environ, {**_VALID_ENV, "CODEF_ENV": "demo"}, clear=True)
    def test_env_demo_url(self):
        config = Config.from_env()
        assert config.base_url == CODEF_URLS["demo"]

    @patch.dict(os.environ, {**_VALID_ENV, "CODEF_ENV": "sandbox"}, clear=True)
    def test_env_sandbox_url(self):
        config = Config.from_env()
        assert config.base_url == CODEF_URLS["sandbox"]

    @patch.dict(os.environ, {**_VALID_ENV, "CODEF_ENV": "production"}, clear=True)
    def test_env_production_url(self):
        config = Config.from_env()
        assert config.base_url == CODEF_URLS["production"]

    @patch.dict(os.environ, {**_VALID_ENV, "CODEF_ENV": "invalid"}, clear=True)
    def test_env_invalid_fallback(self):
        config = Config.from_env()
        assert config.base_url == CODEF_URLS["demo"]

    @patch.dict(os.environ, _VALID_ENV, clear=True)
    def test_optional_defaults(self):
        config = Config.from_env()
        assert config.output_dir == "./output"
        assert config.eprepay_no == ""
        assert config.eprepay_pass == ""
