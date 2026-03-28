"""crypto.py 단위테스트"""

import base64
import os

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA


class TestEncryptPassword:
    def test_roundtrip_with_generated_key(self):
        """생성 키로 암호화 → 복호화 라운드트립"""
        key = RSA.generate(2048)
        pub_der = key.publickey().export_key("DER")
        pub_b64 = base64.b64encode(pub_der).decode()

        os.environ["CODEF_PUBLIC_KEY"] = pub_b64

        # 모듈 리로드
        import importlib
        import src.config
        importlib.reload(src.config)
        import src.crypto
        importlib.reload(src.crypto)

        from src.crypto import encrypt_password

        encrypted = encrypt_password("1234")
        assert len(encrypted) > 50

        # 복호화 검증
        cipher = PKCS1_v1_5.new(key)
        decrypted = cipher.decrypt(base64.b64decode(encrypted), None)
        assert decrypted == b"1234"

    def test_different_passwords_produce_different_output(self):
        """같은 키로 다른 비밀번호를 암호화하면 다른 결과"""
        key = RSA.generate(2048)
        pub_b64 = base64.b64encode(key.publickey().export_key("DER")).decode()
        os.environ["CODEF_PUBLIC_KEY"] = pub_b64

        import importlib
        import src.config
        importlib.reload(src.config)
        import src.crypto
        importlib.reload(src.crypto)
        from src.crypto import encrypt_password

        e1 = encrypt_password("1234")
        e2 = encrypt_password("5678")
        # RSA with PKCS1_v1_5 has random padding, so even same input differs
        # But different inputs should definitely differ
        assert e1 != e2
