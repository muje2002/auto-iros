"""등기부등본 응답 데이터 파싱 모듈

CODEF API 응답의 등기사항 요약/이력 데이터를 구조화하여 표시.
"""

from dataclasses import dataclass


@dataclass
class RegistrationSummary:
    """주요 등기사항 요약 항목"""

    category: str  # 구분 (소유자, 근저당, 전세권 등)
    content: str  # 내용
    date: str  # 접수일자
    rank: str  # 순위번호


@dataclass
class RegistrationHistory:
    """등기 이력 항목"""

    reg_type: str  # 등기 유형
    purpose: str  # 등기 목적
    date: str  # 접수일자
    number: str  # 접수번호


def parse_registration_summary(data: dict) -> list[RegistrationSummary]:
    """API 응답에서 주요등기사항 요약을 파싱.

    Args:
        data: API 응답의 result_data dict

    Returns:
        RegistrationSummary 리스트
    """
    raw_list = data.get("resRegistrationSumList", [])
    summaries = []
    for item in raw_list:
        summaries.append(RegistrationSummary(
            category=item.get("resType", item.get("resCategory", "")),
            content=item.get("resContents", item.get("resContent", "")),
            date=item.get("resDate", item.get("resAcceptDate", "")),
            rank=item.get("resRankNo", item.get("resRank", "")),
        ))
    return summaries


def parse_registration_history(data: dict) -> list[RegistrationHistory]:
    """API 응답에서 등기이력을 파싱.

    Args:
        data: API 응답의 result_data dict

    Returns:
        RegistrationHistory 리스트
    """
    raw_list = data.get("resRegistrationHisList", [])
    histories = []
    for item in raw_list:
        histories.append(RegistrationHistory(
            reg_type=item.get("resType", ""),
            purpose=item.get("resPurpose", item.get("resRegistrationPurpose", "")),
            date=item.get("resDate", item.get("resAcceptDate", "")),
            number=item.get("resNumber", item.get("resAcceptNo", "")),
        ))
    return histories


def format_summary_text(summaries: list[RegistrationSummary]) -> str:
    """요약을 텍스트로 포맷팅 (CLI/로그용)"""
    if not summaries:
        return "등기사항 요약 데이터 없음"
    lines = ["[등기사항 요약]"]
    for s in summaries:
        line = f"  {s.category}: {s.content}"
        if s.date:
            line += f" ({s.date})"
        lines.append(line)
    return "\n".join(lines)


def format_history_text(histories: list[RegistrationHistory]) -> str:
    """이력을 텍스트로 포맷팅 (CLI/로그용)"""
    if not histories:
        return "등기 이력 데이터 없음"
    lines = ["[등기 이력]"]
    for h in histories:
        line = f"  [{h.reg_type}] {h.purpose}"
        if h.date:
            line += f" ({h.date})"
        if h.number:
            line += f" #{h.number}"
        lines.append(line)
    return "\n".join(lines)
