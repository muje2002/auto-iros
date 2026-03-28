"""errors.py 단위테스트"""

from src.errors import get_error_message, is_retryable_error


class TestGetErrorMessage:
    def test_known_code(self):
        msg = get_error_message("CF-12100")
        assert "500명" in msg

    def test_success_code(self):
        msg = get_error_message("CF-00000")
        assert "정상" in msg

    def test_unknown_code_with_fallback(self):
        msg = get_error_message("CF-99998", "some message")
        assert "CF-99998" in msg
        assert "some message" in msg

    def test_unknown_code_without_fallback(self):
        msg = get_error_message("CF-99997")
        assert "CF-99997" in msg
        assert "알 수 없는" in msg

    def test_auth_error(self):
        msg = get_error_message("CF-01000")
        assert "인증" in msg

    def test_phone_error(self):
        msg = get_error_message("CF-13002")
        assert "전화번호" in msg


class TestIsRetryableError:
    def test_server_errors_are_retryable(self):
        assert is_retryable_error("CF-10000") is True
        assert is_retryable_error("CF-10001") is True
        assert is_retryable_error("CF-10002") is True
        assert is_retryable_error("CF-09999") is True

    def test_client_errors_not_retryable(self):
        assert is_retryable_error("CF-01000") is False
        assert is_retryable_error("CF-02000") is False
        assert is_retryable_error("CF-13002") is False
        assert is_retryable_error("CF-12100") is False

    def test_unknown_code_not_retryable(self):
        assert is_retryable_error("CF-99999") is False
