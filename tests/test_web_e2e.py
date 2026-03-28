"""웹 API E2E 테스트 스위트 (Level 3)

FastAPI TestClient 기반. 실제 CODEF API 호출 없이 모든 엔드포인트를 검증.
"""

import os
import tempfile
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.config import Config
from src.codef_api import RegisterResult, RegisterRequest


def _mock_api(mock_result):
    """CodefRegisterClient.request_register를 mock하는 데코레이터"""
    return patch(
        "src.codef_api.CodefRegisterClient.request_register",
        return_value=mock_result,
    )


@pytest.fixture
def app_client():
    """Config mock이 적용된 TestClient (결제 정보 포함)"""
    mock_cfg = Config(
        client_id="test", client_secret="test",
        base_url="https://development.codef.io",
        output_dir=tempfile.mkdtemp(),
        phone_no="01012345678", password="1234",
        eprepay_no="123456789012", eprepay_pass="testpass",
    )
    with patch.object(Config, "from_env", return_value=mock_cfg):
        from app import app
        app.state.config = mock_cfg
        yield TestClient(app, raise_server_exceptions=False), mock_cfg


# === HTML 페이지 렌더링 ===


class TestHTMLPages:
    def test_index(self, app_client):
        client, _ = app_client
        r = client.get("/")
        assert r.status_code == 200
        assert "auto-iros" in r.text

    def test_single_page(self, app_client):
        client, _ = app_client
        r = client.get("/single")
        assert r.status_code == 200
        assert "단건" in r.text or "inquiry_type" in r.text

    def test_batch_page(self, app_client):
        client, _ = app_client
        r = client.get("/batch")
        assert r.status_code == 200
        assert "엑셀" in r.text or "upload" in r.text

    def test_search_page(self, app_client):
        client, _ = app_client
        r = client.get("/search")
        assert r.status_code == 200
        assert "검색" in r.text or "query" in r.text


# === 템플릿 다운로드 ===


class TestTemplateDownload:
    def test_download_xlsx(self, app_client):
        client, _ = app_client
        r = client.get("/api/template/download")
        assert r.status_code == 200
        assert "spreadsheet" in r.headers.get("content-type", "")
        assert len(r.content) > 1000


# === 검색 API ===


class TestSearchAPI:
    def test_search_success_with_addr_list(self, app_client):
        """검색 성공 → 주소 목록 반환"""
        client, _ = app_client
        mock_result = RegisterResult(
            request=RegisterRequest(address="테헤란로"),
            success=False,
            need_two_way=True,
            addr_list=[
                {"address": "서울 강남구 테헤란로 1", "uniqueNo": "1101-0001"},
                {"address": "서울 강남구 테헤란로 2", "uniqueNo": "1101-0002"},
            ],
        )
        with _mock_api(mock_result):
            r = client.post("/api/search", json={"query": "테헤란로"})
        data = r.json()
        assert data["status"] == "success"
        assert data["count"] == 2
        assert len(data["addr_list"]) == 2

    def test_search_error(self, app_client):
        """검색 에러 → 에러 메시지"""
        client, _ = app_client
        mock_result = RegisterResult(
            request=RegisterRequest(),
            success=False,
            error_message="검색 결과 없음",
        )
        with _mock_api(mock_result):
            r = client.post("/api/search", json={"query": "없는주소"})
        data = r.json()
        assert data["status"] == "error"

    def test_search_no_config(self):
        """설정 없을 때 → 안내 메시지"""
        from app import app
        app.state.config = None
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/search", json={"query": "test"})
        data = r.json()
        assert data["status"] == "error"
        assert ".env" in data["message"]


# === 단건 조회 API ===


class TestSingleAPI:
    def test_single_success_with_pdf(self, app_client):
        """단건 성공 → PDF URL 반환"""
        client, _ = app_client
        mock_result = RegisterResult(
            request=RegisterRequest(address="테헤란로 123"),
            success=True,
            code="CF-00000",
            data={},
            pdf_base64="dGVzdA==",  # "test" in base64
        )
        with _mock_api(mock_result):
            r = client.post("/api/single", json={
                "address": "테헤란로 123", "issue_type": "열람",
            })
        data = r.json()
        assert data["status"] == "success"
        assert data["has_pdf"] is True
        assert data["pdf_id"] is not None

    def test_single_two_way(self, app_client):
        """단건 2-Way → session_id + addr_list 반환"""
        client, _ = app_client
        mock_result = RegisterResult(
            request=RegisterRequest(address="테헤란로"),
            success=False,
            code="CF-03002",
            need_two_way=True,
            two_way_info={"jobIndex": "1", "threadIndex": "2"},
            addr_list=[{"address": "A", "uniqueNo": "001"}],
        )
        with _mock_api(mock_result):
            r = client.post("/api/single", json={
                "address": "테헤란로", "issue_type": "열람",
            })
        data = r.json()
        assert data["status"] == "two_way"
        assert "session_id" in data
        assert len(data["addr_list"]) == 1

    def test_single_error(self, app_client):
        """단건 에러 → 에러 메시지"""
        client, _ = app_client
        mock_result = RegisterResult(
            request=RegisterRequest(),
            success=False,
            code="CF-12000",
            error_message="해당 부동산을 찾을 수 없습니다.",
        )
        with _mock_api(mock_result):
            r = client.post("/api/single", json={
                "address": "없는주소", "issue_type": "열람",
            })
        data = r.json()
        assert data["status"] == "error"

    def test_single_payment_validation_production(self):
        """production에서 결제 필요한데 ePrepay 없음 → 에러"""
        prod_cfg = Config(
            client_id="test", client_secret="test",
            base_url="https://api.codef.io",
            output_dir=tempfile.mkdtemp(),
            phone_no="01012345678", password="1234",
            eprepay_no="", eprepay_pass="", env="production",
        )
        from app import app
        app.state.config = prod_cfg
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/single", json={
            "address": "test", "issue_type": "발급",
        })
        data = r.json()
        assert data["status"] == "error"
        assert "전자민원캐시" in data["message"]


# === 2-Way 흐름 E2E ===


class TestTwoWayFlow:
    def test_full_two_way_flow(self, app_client):
        """1차 요청 → 2-Way → 선택 → 2차 요청 → 성공"""
        client, _ = app_client

        # Step 1: 1차 요청 → 2-Way
        mock_first = RegisterResult(
            request=RegisterRequest(address="테헤란로"),
            success=False, code="CF-03002",
            need_two_way=True,
            two_way_info={"jobIndex": "1", "threadIndex": "2", "jti": "abc", "twoWayTimestamp": "123"},
            addr_list=[
                {"address": "서울 테헤란로 1", "uniqueNo": "U001"},
                {"address": "서울 테헤란로 2", "uniqueNo": "U002"},
            ],
        )
        with _mock_api(mock_first):
            r1 = client.post("/api/single", json={"address": "테헤란로", "issue_type": "열람"})
        data1 = r1.json()
        assert data1["status"] == "two_way"
        session_id = data1["session_id"]

        # Step 2: 2차 요청 → 성공
        mock_second = RegisterResult(
            request=RegisterRequest(address="테헤란로"),
            success=True, code="CF-00000",
            data={}, pdf_base64="cGRm",
        )
        with _mock_api(mock_second):
            r2 = client.post("/api/single/two-way", json={
                "session_id": session_id, "selected_index": 1,
            })
        data2 = r2.json()
        assert data2["status"] == "success"
        assert data2["has_pdf"] is True

    def test_expired_session(self, app_client):
        """만료된 세션 → 에러"""
        client, _ = app_client
        r = client.post("/api/single/two-way", json={
            "session_id": "nonexistent", "selected_index": 0,
        })
        data = r.json()
        assert data["status"] == "error"
        assert "만료" in data["message"]

    def test_invalid_selection(self, app_client):
        """잘못된 인덱스 → 에러"""
        client, _ = app_client

        mock_first = RegisterResult(
            request=RegisterRequest(),
            success=False, code="CF-03002",
            need_two_way=True,
            two_way_info={"jobIndex": "1"},
            addr_list=[{"address": "A", "uniqueNo": "001"}],
        )
        with _mock_api(mock_first):
            r1 = client.post("/api/single", json={"address": "test", "issue_type": "열람"})
        sid = r1.json()["session_id"]

        r2 = client.post("/api/single/two-way", json={
            "session_id": sid, "selected_index": 99,
        })
        assert r2.json()["status"] == "error"


# === PDF 다운로드 ===


class TestPDFDownload:
    def test_download_existing_pdf(self, app_client):
        """PDF 다운로드 성공"""
        client, _ = app_client
        # 먼저 단건 조회로 PDF 저장
        mock_result = RegisterResult(
            request=RegisterRequest(address="test"),
            success=True, data={},
            pdf_base64="dGVzdHBkZg==",
        )
        with _mock_api(mock_result):
            r = client.post("/api/single", json={"address": "test", "issue_type": "열람"})
        pdf_id = r.json()["pdf_id"]

        r2 = client.get(f"/api/single/pdf/{pdf_id}")
        assert r2.status_code == 200
        assert r2.headers["content-type"] == "application/pdf"

    def test_download_nonexistent_pdf(self, app_client):
        client, _ = app_client
        r = client.get("/api/single/pdf/nonexistent")
        assert r.json()["status"] == "error"


# === 배치 업로드/실행 ===


class TestBatchAPI:
    def test_upload_valid_excel(self, app_client):
        """유효한 엑셀 업로드 → 미리보기 반환"""
        client, _ = app_client
        # 템플릿 생성 후 업로드
        from src.excel_handler import create_template
        tmp = os.path.join(tempfile.mkdtemp(), "test.xlsx")
        create_template(tmp)

        with open(tmp, "rb") as f:
            r = client.post("/api/batch/upload", files={"file": ("test.xlsx", f)})
        data = r.json()
        assert data["status"] == "success"
        assert data["count"] >= 2
        assert "requests_data" in data
        os.unlink(tmp)

    def test_batch_download_nonexistent(self, app_client):
        client, _ = app_client
        r = client.get("/api/batch/download/nonexistent.pdf")
        assert r.json()["status"] == "error"
