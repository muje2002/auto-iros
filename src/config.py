"""CODEF API 설정 관리"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# CODEF API 베이스 URL
CODEF_URLS = {
    "sandbox": "https://development.codef.io",
    "production": "https://api.codef.io",
}

CODEF_TOKEN_URL = "https://oauth.codef.io/oauth/token"

# 등기부등본 API 경로
REGISTER_API_PATH = "/v1/kr/public/ck/real-estate-register/status"


@dataclass
class Config:
    client_id: str
    client_secret: str
    base_url: str
    output_dir: str

    @classmethod
    def from_env(cls) -> "Config":
        env = os.getenv("CODEF_ENV", "sandbox")
        client_id = os.getenv("CODEF_CLIENT_ID", "")
        client_secret = os.getenv("CODEF_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            raise ValueError(
                "CODEF_CLIENT_ID와 CODEF_CLIENT_SECRET 환경변수를 설정하세요.\n"
                ".env.example을 참고하여 .env 파일을 생성하세요."
            )

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            base_url=CODEF_URLS.get(env, CODEF_URLS["sandbox"]),
            output_dir=os.getenv("OUTPUT_DIR", "./output"),
        )
