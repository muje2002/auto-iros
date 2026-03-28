"""register_parser.py 단위테스트"""

from src.register_parser import (
    parse_registration_summary,
    parse_registration_history,
    format_summary_text,
    format_history_text,
)


class TestParseRegistrationSummary:
    def test_empty_data(self):
        assert parse_registration_summary({}) == []

    def test_empty_list(self):
        assert parse_registration_summary({"resRegistrationSumList": []}) == []

    def test_parse_items(self):
        data = {
            "resRegistrationSumList": [
                {"resType": "소유자", "resContents": "홍길동", "resDate": "2024-01-15", "resRankNo": "1"},
                {"resType": "근저당", "resContents": "국민은행 3억", "resDate": "2024-02-20", "resRankNo": "2"},
            ]
        }
        result = parse_registration_summary(data)
        assert len(result) == 2
        assert result[0].category == "소유자"
        assert result[0].content == "홍길동"
        assert result[0].date == "2024-01-15"
        assert result[1].category == "근저당"

    def test_alternative_field_names(self):
        """대안 필드명 (resCategory, resContent 등)도 파싱"""
        data = {
            "resRegistrationSumList": [
                {"resCategory": "전세권", "resContent": "전세 2억", "resAcceptDate": "2024-03-01", "resRank": "3"},
            ]
        }
        result = parse_registration_summary(data)
        assert len(result) == 1
        assert result[0].category == "전세권"
        assert result[0].content == "전세 2억"
        assert result[0].date == "2024-03-01"


class TestParseRegistrationHistory:
    def test_empty_data(self):
        assert parse_registration_history({}) == []

    def test_parse_items(self):
        data = {
            "resRegistrationHisList": [
                {"resType": "갑구", "resPurpose": "소유권이전", "resDate": "2024-01-15", "resNumber": "12345"},
                {"resType": "을구", "resPurpose": "근저당설정", "resDate": "2024-02-20", "resNumber": "67890"},
            ]
        }
        result = parse_registration_history(data)
        assert len(result) == 2
        assert result[0].reg_type == "갑구"
        assert result[0].purpose == "소유권이전"
        assert result[1].number == "67890"


class TestFormatting:
    def test_format_summary_empty(self):
        assert "없음" in format_summary_text([])

    def test_format_history_empty(self):
        assert "없음" in format_history_text([])

    def test_format_summary_text(self):
        data = {
            "resRegistrationSumList": [
                {"resType": "소유자", "resContents": "홍길동", "resDate": "2024-01-15", "resRankNo": "1"},
            ]
        }
        summaries = parse_registration_summary(data)
        text = format_summary_text(summaries)
        assert "소유자" in text
        assert "홍길동" in text

    def test_format_history_text(self):
        data = {
            "resRegistrationHisList": [
                {"resType": "갑구", "resPurpose": "소유권이전", "resDate": "2024-01-15", "resNumber": "12345"},
            ]
        }
        histories = parse_registration_history(data)
        text = format_history_text(histories)
        assert "소유권이전" in text
        assert "갑구" in text
