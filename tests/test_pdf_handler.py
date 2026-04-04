"""pdf_handler.py 단위테스트"""

import base64
import os

from src.codef_api import RegisterRequest, RegisterResult
from src.pdf_handler import sanitize_filename, save_pdf, save_batch_pdfs


class TestSanitizeFilename:
    def test_removes_special_chars(self):
        result = sanitize_filename('a<b>c:d"e/f\\g|h?i*j')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result

    def test_collapses_whitespace(self):
        result = sanitize_filename("a  b\tc")
        assert result == "a_b_c"

    def test_truncates_to_100(self):
        long_name = "a" * 200
        result = sanitize_filename(long_name)
        assert len(result) == 100

    def test_empty_string(self):
        assert sanitize_filename("") == ""


class TestSavePdf:
    def test_saves_valid_pdf(self, tmp_path):
        pdf_data = base64.b64encode(b"fakepdfcontent").decode()
        result = RegisterResult(
            request=RegisterRequest(address="test addr"),
            success=True,
            pdf_base64=pdf_data,
        )
        filepath = save_pdf(result, str(tmp_path))
        assert filepath is not None
        assert os.path.exists(filepath)
        with open(filepath, "rb") as f:
            assert f.read() == b"fakepdfcontent"

    def test_returns_none_on_failure(self, tmp_path):
        result = RegisterResult(
            request=RegisterRequest(address="test"),
            success=False,
        )
        assert save_pdf(result, str(tmp_path)) is None

    def test_returns_none_without_pdf(self, tmp_path):
        result = RegisterResult(
            request=RegisterRequest(address="test"),
            success=True,
            pdf_base64=None,
        )
        assert save_pdf(result, str(tmp_path)) is None

    def test_creates_output_dir(self, tmp_path):
        new_dir = str(tmp_path / "subdir" / "nested")
        pdf_data = base64.b64encode(b"data").decode()
        result = RegisterResult(
            request=RegisterRequest(address="test"),
            success=True,
            pdf_base64=pdf_data,
        )
        filepath = save_pdf(result, new_dir)
        assert filepath is not None
        assert os.path.isdir(new_dir)


class TestSaveBatchPdfs:
    def test_mixed_results(self, tmp_path):
        pdf_data = base64.b64encode(b"pdf").decode()
        results = [
            RegisterResult(request=RegisterRequest(address="ok1"), success=True, pdf_base64=pdf_data),
            RegisterResult(request=RegisterRequest(address="ok2"), success=True, pdf_base64=pdf_data),
            RegisterResult(request=RegisterRequest(address="fail"), success=False, error_message="에러"),
        ]
        summaries = save_batch_pdfs(results, str(tmp_path))
        assert len(summaries) == 3
        assert summaries[0]["status"] == "성공"
        assert summaries[1]["status"] == "성공"
        assert summaries[2]["status"] == "실패"
        assert summaries[2]["error"] == "에러"

    def test_empty_list(self, tmp_path):
        assert save_batch_pdfs([], str(tmp_path)) == []
