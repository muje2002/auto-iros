"""CODEF 2-Way 추가인증 처리 모듈

주소 검색 결과가 여러 건일 때 사용자가 선택 → 2차 요청을 보내는 흐름.

1차 요청 → CF-03002 (continue2Way) → 주소 목록 표시 → 사용자 선택
→ 2차 요청 (is2Way=true, uniqueNo, twoWayInfo) → 최종 응답

순수 로직(build_two_way_params)과 CLI 어댑터(handle_two_way_cli)를 분리하여
웹 UI에서도 재사용 가능하게 설계.
"""

from rich.console import Console
from rich.table import Table

from .codef_api import CodefRegisterClient, RegisterResult

console = Console()


# --- 순수 로직 (UI 무관) ---


def build_two_way_params(
    first_result: RegisterResult,
    selected_addr: dict,
) -> dict:
    """2-Way 2차 요청에 필요한 파라미터를 구성한다. I/O 없음.

    Args:
        first_result: 1차 요청 결과 (CF-03002)
        selected_addr: 사용자가 선택한 주소 dict (uniqueNo 포함)

    Returns:
        2차 요청에 전달할 twoWayInfo dict
    """
    two_way_info = dict(first_result.two_way_info or {})
    two_way_info["uniqueNo"] = selected_addr.get("uniqueNo", "")
    return two_way_info


# --- CLI 어댑터 (터미널 전용) ---


def _select_address_cli(addr_list: list[dict]) -> dict | None:
    """CLI: 주소 목록을 표시하고 사용자에게 선택받는다."""
    if not addr_list:
        console.print("[red]주소 목록이 비어있습니다.[/]")
        return None

    table = Table(title="검색된 부동산 목록")
    table.add_column("#", style="dim", width=4)
    table.add_column("주소", min_width=40)
    table.add_column("고유번호", width=18)
    table.add_column("부동산구분", width=12)

    for i, addr in enumerate(addr_list, 1):
        table.add_row(
            str(i),
            addr.get("address", addr.get("resAddr", "")),
            addr.get("uniqueNo", ""),
            addr.get("realtyType", ""),
        )

    console.print(table)
    console.print()

    while True:
        choice = console.input(
            f"[yellow]선택할 번호를 입력하세요 (1-{len(addr_list)}, 취소: 0): [/]"
        )
        try:
            idx = int(choice)
            if idx == 0:
                return None
            if 1 <= idx <= len(addr_list):
                return addr_list[idx - 1]
            console.print(f"[red]1~{len(addr_list)} 사이의 번호를 입력하세요.[/]")
        except ValueError:
            console.print("[red]숫자를 입력하세요.[/]")


def handle_two_way_cli(
    client: CodefRegisterClient,
    first_result: RegisterResult,
) -> RegisterResult:
    """CLI용 2-Way 추가인증 전체 흐름을 처리한다.

    Args:
        client: CODEF API 클라이언트
        first_result: 1차 요청 결과 (CF-03002)

    Returns:
        2차 요청 결과 (최종)
    """
    if not first_result.need_two_way:
        return first_result

    addr_list = first_result.addr_list or []

    if not addr_list:
        console.print("[red]추가인증이 필요하지만 주소 목록이 없습니다.[/]")
        return first_result

    console.print(
        f"\n[yellow]검색 결과 {len(addr_list)}건이 발견되었습니다. "
        "선택해주세요.[/]\n"
    )

    selected = _select_address_cli(addr_list)
    if selected is None:
        console.print("[dim]취소되었습니다.[/]")
        first_result.error_message = "사용자가 선택을 취소했습니다."
        return first_result

    two_way_info = build_two_way_params(first_result, selected)

    console.print(
        f"\n[bold blue]선택:[/] {selected.get('address', selected.get('resAddr', ''))}"
        f" (고유번호: {selected.get('uniqueNo', '')})"
    )
    console.print("[dim]2차 요청 중... (타임아웃: 120초)[/]")

    return client.request_register(
        first_result.request,
        is_two_way=True,
        two_way_info=two_way_info,
    )
