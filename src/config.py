"""CODEF API 설정 관리"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# CODEF API 베이스 URL (3개 환경)
CODEF_URLS = {
    "demo": "https://development.codef.io",       # 데모 (개발/테스트)
    "sandbox": "https://sandbox.codef.io",         # 샌드박스 (고정 응답)
    "production": "https://api.codef.io",          # 정식 (운영)
}

CODEF_TOKEN_URL = "https://oauth.codef.io/oauth/token"

# 등기부등본 API 경로
REGISTER_API_PATH = "/v1/kr/public/ck/real-estate-register/status"

# CODEF RSA 공개키 (비밀번호 암호화용)
# CODEF 개발자센터에서 발급받은 공개키를 .env CODEF_PUBLIC_KEY에 설정
CODEF_PUBLIC_KEY = os.getenv("CODEF_PUBLIC_KEY", "")

# API 타임아웃 (초)
API_TIMEOUT_FIRST = 300  # 1차 요청
API_TIMEOUT_SECOND = 120  # 2차 요청 (추가인증)


@dataclass
class Config:
    client_id: str
    client_secret: str
    base_url: str
    output_dir: str
    phone_no: str
    password: str
    eprepay_no: str
    eprepay_pass: str
    env: str = "demo"  # demo / sandbox / production

    @classmethod
    def from_env(cls) -> "Config":
        env = os.getenv("CODEF_ENV", "demo")
        client_id = os.getenv("CODEF_CLIENT_ID", "")
        client_secret = os.getenv("CODEF_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            raise ValueError(
                "CODEF_CLIENT_ID와 CODEF_CLIENT_SECRET 환경변수를 설정하세요.\n"
                ".env.example을 참고하여 .env 파일을 생성하세요."
            )

        phone_no = os.getenv("CODEF_PHONE_NO", "")
        password = os.getenv("CODEF_PASSWORD", "")

        if not phone_no or not password:
            raise ValueError(
                "CODEF_PHONE_NO와 CODEF_PASSWORD 환경변수를 설정하세요.\n"
                "phoneNo: 전화번호, password: 4자리 숫자"
            )

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            base_url=CODEF_URLS.get(env, CODEF_URLS["demo"]),
            output_dir=os.getenv("OUTPUT_DIR", "./output"),
            phone_no=phone_no,
            password=password,
            eprepay_no=os.getenv("EPREPAY_NO", ""),
            eprepay_pass=os.getenv("EPREPAY_PASS", ""),
            env=env,
        )
