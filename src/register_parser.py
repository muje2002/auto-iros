"""등기부등본 응답 데이터 파싱 모듈

CODEF API 응답의 등기사항 요약/이력 데이터를 구조화하여 표시.

API 응답의 resRegistrationSumList / resRegistrationHisList는 다음 중첩 구조를 가짐:
  [{
    "resType": "...",          # 섹션 구분 (예: "표제부", "갑구", "을구", "소유자")
    "resType1": "...",         # 부가 구분
    "resContentsList": [{
      "resNumber": "...",      # 항목 순번
      "resType2": "...",       # 행 유형 (1: 헤더 행)
      "resDetailList": [{
        "resNumber": "...",    # 셀 순번
        "resContents": "...",  # 셀 내용 (& 마커 / | 분할 포함 가능)
      }]
    }]
  }]
"""

from dataclasses import dataclass, field


@dataclass
class RegistrationRow:
    """등기사항 한 행 (여러 셀 묶음)"""

    cells: list[str] = field(default_factory=list)


@dataclass
class RegistrationSection:
    """등기사항 한 섹션 (예: 표제부, 갑구, 을구)"""

    type: str  # 섹션 구분
    type1: str = ""  # 부가 구분
    rows: list[RegistrationRow] = field(default_factory=list)


@dataclass
class RegisterEntry:
    """등기부등본 엔트리 기본 정보 + 요약/이력 섹션"""

    unique_no: str
    doc_title: str
    realty: str
    registry_office: str
    publish_no: str = ""
    publish_date: str = ""
    summary_sections: list[RegistrationSection] = field(default_factory=list)  # resRegistrationSumList
    history_sections: list[RegistrationSection] = field(default_factory=list)  # resRegistrationHisList


def _get_entry_data(data: dict) -> dict:
    """resRegisterEntriesList 안의 첫 번째 entry를 반환 (없으면 data 자체)."""
    entries = data.get("resRegisterEntriesList", [])
    if entries and isinstance(entries, list):
        return entries[0]
    return data


def _clean_content(text: str) -> str:
    """CODEF 응답의 & 마커를 제거하고 줄바꿈 정리.

    `&...&`는 실제 출력물에서 취소선 처리되는 문자이지만, 여기서는 단순 제거.
    (취소선 표시는 추후 개선)
    """
    if not isinstance(text, str):
        return ""
    return text.replace("&", "").strip()


def _parse_sections(raw_list: list[dict]) -> list[RegistrationSection]:
    """resRegistrationSumList / resRegistrationHisList 의 중첩 구조 파싱."""
    sections: list[RegistrationSection] = []
    for section in raw_list or []:
        rows: list[RegistrationRow] = []
        for content in section.get("resContentsList", []):
            # resType2='1'은 헤더 행 — 사람이 보기 위한 컬럼 제목이므로 스킵
            if content.get("resType2") == "1":
                continue
            cells = [
                _clean_content(detail.get("resContents", ""))
                for detail in content.get("resDetailList", [])
            ]
            if any(cells):
                rows.append(RegistrationRow(cells=cells))
        sections.append(RegistrationSection(
            type=section.get("resType", ""),
            type1=section.get("resType1", ""),
            rows=rows,
        ))
    return sections


def parse_registration_summary(data: dict) -> list[RegistrationSection]:
    """주요 등기사항 요약을 파싱 (resRegistrationSumList).

    Args:
        data: API 응답의 result_data dict

    Returns:
        RegistrationSection 리스트 (섹션별 행 데이터)
    """
    entry = _get_entry_data(data)
    raw_list = entry.get("resRegistrationSumList") or data.get("resRegistrationSumList") or []
    return _parse_sections(raw_list)


def parse_registration_history(data: dict) -> list[RegistrationSection]:
    """등기 이력을 파싱 (resRegistrationHisList).

    Args:
        data: API 응답의 result_data dict

    Returns:
        RegistrationSection 리스트 (표제부/갑구/을구 섹션별 행 데이터)
    """
    entry = _get_entry_data(data)
    raw_list = entry.get("resRegistrationHisList") or data.get("resRegistrationHisList") or []
    return _parse_sections(raw_list)


def parse_register_entries(data: dict) -> list[RegisterEntry]:
    """resRegisterEntriesList 전체를 파싱 (요약 + 이력 + 메타데이터).

    Args:
        data: API 응답의 result_data dict

    Returns:
        RegisterEntry 리스트
    """
    entries_raw = data.get("resRegisterEntriesList", [])
    result: list[RegisterEntry] = []
    for entry in entries_raw:
        result.append(RegisterEntry(
            unique_no=entry.get("commUniqueNo", ""),
            doc_title=entry.get("resDocTitle", ""),
            realty=entry.get("resRealty", ""),
            registry_office=entry.get("commCompetentRegistryOffice", ""),
            publish_no=entry.get("resPublishNo", ""),
            publish_date=entry.get("resPublishDate", ""),
            summary_sections=_parse_sections(entry.get("resRegistrationSumList", [])),
            history_sections=_parse_sections(entry.get("resRegistrationHisList", [])),
        ))
    return result


def _format_sections_text(title: str, sections: list[RegistrationSection]) -> str:
    """섹션 리스트를 텍스트로 포맷 (CLI/로그용)"""
    if not sections or not any(s.rows for s in sections):
        return f"{title} 데이터 없음"
    lines = [f"[{title}]"]
    for s in sections:
        if not s.rows:
            continue
        lines.append(f"  <{s.type}>")
        for row in s.rows:
            lines.append("    " + " | ".join(row.cells))
    return "\n".join(lines)


def format_summary_text(sections: list[RegistrationSection]) -> str:
    """요약 섹션을 텍스트로 포맷팅 (CLI/로그용)"""
    return _format_sections_text("등기사항 요약", sections)


def format_history_text(sections: list[RegistrationSection]) -> str:
    """이력 섹션을 텍스트로 포맷팅 (CLI/로그용)"""
    return _format_sections_text("등기 이력", sections)
