"""CODEF RSA 비밀번호 암호화 모듈

easycodefpy 참조: base64 디코딩 → RSA.importKey(DER) → PKCS1_v1_5 암호화
"""

import base64
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

from .config import CODEF_PUBLIC_KEY


def encrypt_password(plain_password: str) -> str:
    """CODEF RSA 공개키로 비밀번호를 암호화하여 Base64 문자열로 반환.

    Args:
        plain_password: 4자리 숫자 비밀번호 (평문)

    Returns:
        RSA 암호화 + Base64 인코딩된 비밀번호 문자열

    Raises:
        ValueError: CODEF_PUBLIC_KEY가 설정되지 않았거나 유효하지 않을 때
    """
    if not CODEF_PUBLIC_KEY:
        raise ValueError(
            "CODEF_PUBLIC_KEY가 설정되지 않았습니다.\n"
            "CODEF 개발자센터에서 발급받은 공개키를 .env에 설정하세요."
        )

    key_der = base64.b64decode(CODEF_PUBLIC_KEY)
    public_key = RSA.import_key(key_der)
    cipher = PKCS1_v1_5.new(public_key)
    encrypted = cipher.encrypt(plain_password.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")
