"""register_parser.py 단위테스트 (중첩 구조 파서)"""

from src.register_parser import (
    parse_register_entries,
    parse_registration_history,
    parse_registration_summary,
    format_summary_text,
    format_history_text,
)


def _make_section(section_type: str, rows: list[list[str]], type1: str = "") -> dict:
    """API 응답의 섹션 구조 생성 헬퍼."""
    contents = [
        {
            # 헤더 행 (resType2='1')은 스킵되어야 함
            "resType2": "1",
            "resNumber": "0",
            "resDetailList": [
                {"resNumber": str(i), "resContents": f"헤더{i}"}
                for i in range(len(rows[0]) if rows else 0)
            ],
        }
    ]
    for row_idx, row in enumerate(rows):
        contents.append({
            "resType2": "2",
            "resNumber": str(row_idx + 1),
            "resDetailList": [
                {"resNumber": str(i), "resContents": cell}
                for i, cell in enumerate(row)
            ],
        })
    return {
        "resType": section_type,
        "resType1": type1,
        "resContentsList": contents,
    }


# 테스트용 응답 데이터
SAMPLE_DATA = {
    "resRegisterEntriesList": [
        {
            "commUniqueNo": "1101-2024-000001",
            "resDocTitle": "부동산등기부등본",
            "resRealty": "집합건물",
            "commCompetentRegistryOffice": "서울중앙지방법원 등기국",
            "resPublishNo": "20260409-001",
            "resPublishDate": "2026-04-09",
            "resRegistrationSumList": [
                _make_section("소유자", [
                    ["1", "홍길동", "2020-03-15"],
                    ["2", "김철수", "2024-01-15"],
                ]),
                _make_section("근저당", [
                    ["1", "국민은행", "5억원"],
                ]),
            ],
            "resRegistrationHisList": [
                _make_section("표제부", [
                    ["1", "테헤란로 152", "2020-03-15"],
                ]),
                _make_section("갑구", [
                    ["1", "소유권이전", "2024-01-15", "12345"],
                ]),
                _make_section("을구", [
                    ["1", "근저당설정", "2024-02-20", "67890"],
                ]),
            ],
        }
    ]
}


class TestParseRegistrationSummary:
    def test_empty_data(self):
        assert parse_registration_summary({}) == []

    def test_empty_list(self):
        data = {"resRegisterEntriesList": [{"resRegistrationSumList": []}]}
        assert parse_registration_summary(data) == []

    def test_parses_nested_structure(self):
        sections = parse_registration_summary(SAMPLE_DATA)
        assert len(sections) == 2

        # 첫 번째 섹션 (소유자)
        owner_section = sections[0]
        assert owner_section.type == "소유자"
        assert len(owner_section.rows) == 2  # 헤더 제외
        assert owner_section.rows[0].cells == ["1", "홍길동", "2020-03-15"]
        assert owner_section.rows[1].cells == ["2", "김철수", "2024-01-15"]

        # 두 번째 섹션 (근저당)
        mort_section = sections[1]
        assert mort_section.type == "근저당"
        assert mort_section.rows[0].cells == ["1", "국민은행", "5억원"]

    def test_falls_back_to_top_level(self):
        """resRegisterEntriesList 없이 top-level에 있을 때도 파싱"""
        data = {
            "resRegistrationSumList": [
                _make_section("소유자", [["1", "홍길동", "2020"]]),
            ]
        }
        sections = parse_registration_summary(data)
        assert len(sections) == 1
        assert sections[0].rows[0].cells == ["1", "홍길동", "2020"]


class TestParseRegistrationHistory:
    def test_empty_data(self):
        assert parse_registration_history({}) == []

    def test_parses_nested_structure(self):
        sections = parse_registration_history(SAMPLE_DATA)
        assert len(sections) == 3

        types = [s.type for s in sections]
        assert types == ["표제부", "갑구", "을구"]

        # 갑구
        gap_section = sections[1]
        assert gap_section.rows[0].cells == ["1", "소유권이전", "2024-01-15", "12345"]


class TestParseRegisterEntries:
    def test_full_entry(self):
        entries = parse_register_entries(SAMPLE_DATA)
        assert len(entries) == 1

        entry = entries[0]
        assert entry.unique_no == "1101-2024-000001"
        assert entry.doc_title == "부동산등기부등본"
        assert entry.realty == "집합건물"
        assert entry.registry_office == "서울중앙지방법원 등기국"
        assert entry.publish_no == "20260409-001"
        assert entry.publish_date == "2026-04-09"

        # 요약 섹션
        assert len(entry.summary_sections) == 2
        assert entry.summary_sections[0].type == "소유자"
        assert len(entry.summary_sections[0].rows) == 2

        # 이력 섹션 (표제부/갑구/을구)
        assert len(entry.history_sections) == 3
        assert entry.history_sections[0].type == "표제부"
        assert entry.history_sections[1].type == "갑구"
        assert entry.history_sections[2].type == "을구"

    def test_empty(self):
        assert parse_register_entries({}) == []
        assert parse_register_entries({"resRegisterEntriesList": []}) == []

    def test_skips_header_rows(self):
        """resType2='1' 헤더 행이 스킵되는지 확인"""
        entries = parse_register_entries(SAMPLE_DATA)
        # 표제부에는 1개 데이터 행만 있어야 함 (헤더 1개는 스킵)
        assert len(entries[0].history_sections[0].rows) == 1

    def test_cleans_ampersand_markers(self):
        """&...& 마커가 제거되는지 확인"""
        data = {
            "resRegisterEntriesList": [{
                "resRegistrationHisList": [
                    _make_section("갑구", [["1", "&주식회사 코드에프&", "2024"]]),
                ],
            }]
        }
        entries = parse_register_entries(data)
        cell = entries[0].history_sections[0].rows[0].cells[1]
        assert "&" not in cell
        assert "주식회사 코드에프" in cell


class TestFormatting:
    def test_format_summary_empty(self):
        assert "없음" in format_summary_text([])

    def test_format_history_empty(self):
        assert "없음" in format_history_text([])

    def test_format_summary_text(self):
        sections = parse_registration_summary(SAMPLE_DATA)
        text = format_summary_text(sections)
        assert "소유자" in text
        assert "홍길동" in text
        assert "근저당" in text

    def test_format_history_text(self):
        sections = parse_registration_history(SAMPLE_DATA)
        text = format_history_text(sections)
        assert "갑구" in text
        assert "소유권이전" in text
