"""CODEF API OAuth2 인증 모듈"""

import base64
import time
import requests

from .config import CODEF_TOKEN_URL, Config


class CodefAuth:
    """CODEF OAuth2 토큰 관리"""

    def __init__(self, config: Config):
        self.config = config
        self._token: str | None = None
        self._token_expires_at: float = 0

    def get_token(self) -> str:
        """유효한 액세스 토큰을 반환. 만료 시 자동 갱신."""
        if self._token and time.time() < self._token_expires_at:
            return self._token

        self._token = self._request_token()
        return self._token

    def _request_token(self) -> str:
        """CODEF OAuth2 서버에서 액세스 토큰 발급"""
        # Basic Auth: base64(client_id:client_secret)
        credentials = f"{self.config.client_id}:{self.config.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        response = requests.post(
            CODEF_TOKEN_URL,
            headers={
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        self._token_expires_at = time.time() + data.get("expires_in", 3600) - 60
        return data["access_token"]

    def get_headers(self) -> dict:
        """API 요청에 사용할 인증 헤더 반환"""
        return {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json",
        }
