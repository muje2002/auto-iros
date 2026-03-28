"""payment.py 단위테스트"""

from src.payment import requires_payment, validate_payment_config
from src.config import Config


class TestRequiresPayment:
    def test_issue_requires_payment(self):
        assert requires_payment("발급") is True

    def test_view_requires_payment(self):
        assert requires_payment("열람") is True

    def test_unique_no_query_no_payment(self):
        assert requires_payment("고유번호조회") is False

    def test_raw_data_no_payment(self):
        assert requires_payment("원문데이터") is False


class TestValidatePaymentConfig:
    def test_no_payment_needed(self, mock_config: Config):
        """고유번호조회는 어떤 환경이든 결제 불필요"""
        assert validate_payment_config(mock_config, "고유번호조회") is None

    def test_demo_skips_payment_check(self, mock_config: Config):
        """demo 환경에서는 결제 정보 없어도 통과"""
        assert mock_config.env == "demo"
        assert validate_payment_config(mock_config, "열람") is None
        assert validate_payment_config(mock_config, "발급") is None

    def test_sandbox_skips_payment_check(self, mock_config: Config):
        """sandbox 환경에서도 결제 검증 건너뜀"""
        mock_config.env = "sandbox"
        assert validate_payment_config(mock_config, "열람") is None

    def test_production_requires_eprepay(self):
        """production 환경에서 결제 정보 없으면 에러"""
        prod_config = Config(
            client_id="t", client_secret="t",
            base_url="https://api.codef.io",
            output_dir="./out", phone_no="010", password="1234",
            eprepay_no="", eprepay_pass="", env="production",
        )
        err = validate_payment_config(prod_config, "발급")
        assert err is not None
        assert "전자민원캐시" in err

    def test_production_with_valid_config(self, mock_config_with_payment: Config):
        """production + 결제 정보 있으면 통과"""
        assert mock_config_with_payment.env == "production"
        assert validate_payment_config(mock_config_with_payment, "발급") is None

    def test_production_wrong_eprepay_length(self):
        """production에서 ePrepayNo 길이 오류"""
        prod_config = Config(
            client_id="t", client_secret="t",
            base_url="https://api.codef.io",
            output_dir="./out", phone_no="010", password="1234",
            eprepay_no="123", eprepay_pass="pass", env="production",
        )
        err = validate_payment_config(prod_config, "발급")
        assert err is not None
        assert "12자리" in err

    def test_production_missing_eprepay_pass(self):
        """production에서 ePrepayPass 누락"""
        prod_config = Config(
            client_id="t", client_secret="t",
            base_url="https://api.codef.io",
            output_dir="./out", phone_no="010", password="1234",
            eprepay_no="123456789012", eprepay_pass="", env="production",
        )
        err = validate_payment_config(prod_config, "발급")
        assert err is not None
