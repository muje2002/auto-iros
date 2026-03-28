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
        assert validate_payment_config(mock_config, "고유번호조회") is None

    def test_payment_needed_but_no_eprepay(self, mock_config: Config):
        err = validate_payment_config(mock_config, "발급")
        assert err is not None
        assert "전자민원캐시" in err

    def test_payment_with_valid_config(self, mock_config_with_payment: Config):
        assert validate_payment_config(mock_config_with_payment, "발급") is None

    def test_wrong_eprepay_length(self, mock_config: Config):
        mock_config.eprepay_no = "123"  # 12자리가 아님
        err = validate_payment_config(mock_config, "발급")
        assert err is not None
        assert "12자리" in err

    def test_missing_eprepay_pass(self, mock_config: Config):
        mock_config.eprepay_no = "123456789012"
        mock_config.eprepay_pass = ""
        err = validate_payment_config(mock_config, "발급")
        assert err is not None
