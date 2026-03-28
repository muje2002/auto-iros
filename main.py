"""
auto-iros: 인터넷 등기소 등기부등본 자동 발급 프로그램
CODEF API를 활용한 등기부등본 PDF 일괄 출력
"""

import argparse
import os
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.config import Config
from src.codef_api import CodefRegisterClient, RegisterRequest, INQUIRY_TYPES
from src.excel_handler import create_template, read_requests
from src.pdf_handler import save_batch_pdfs
from src.two_way import handle_two_way_cli
from src.log import setup_logging
from src.maintenance import get_maintenance_warning
from src.payment import validate_payment_config

setup_logging()
console = Console()


def _check_maintenance() -> None:
    """점검 시간대 경고 출력"""
    warning = get_maintenance_warning()
    if warning:
        console.print(f"[bold yellow]⚠ {warning}[/]\n")


def cmd_single(args: argparse.Namespace) -> None:
    """단건 등기부등본 조회"""
    config = Config.from_env()

    # 결제 검증
    payment_err = validate_payment_config(config, args.issue_type)
    if payment_err:
        console.print(f"[red]결제 오류:[/] {payment_err}")
        sys.exit(1)

    req = RegisterRequest(
        inquiry_type=args.inquiry_type,
        address=args.address or "",
        dong=args.dong or "",
        ho=args.ho or "",
        realty_type=args.realty_type,
        register_type=args.register_type,
        issue_type=args.issue_type,
        unique_no=args.unique_no or "",
    )

    console.print(f"\n[bold blue]조회 중:[/] {req.display_name}")
    if req.dong:
        console.print(f"  동: {req.dong}, 호: {req.ho}")
    console.print(f"  조회구분: {req.inquiry_type}, 발급유형: {req.issue_type}")

    client = CodefRegisterClient(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("CODEF API 요청 중...", total=None)
        result = client.request_register(req)

    # 2-Way 추가인증 처리
    if result.need_two_way:
        result = handle_two_way_cli(client, result)

    if result.success:
        summaries = save_batch_pdfs([result], config.output_dir)
        filepath = summaries[0].get("file")
        if filepath:
            console.print(
                Panel(
                    f"[green]발급 완료![/]\n저장 위치: {filepath}",
                    title="결과",
                )
            )
        else:
            console.print(
                Panel(
                    "[green]조회 성공![/]\nPDF 데이터 없음 (고유번호조회 등)",
                    title="결과",
                )
            )
    else:
        console.print(
            Panel(
                f"[red]발급 실패[/]\n{result.error_message}",
                title="오류",
            )
        )
        sys.exit(1)


def cmd_batch(args: argparse.Namespace) -> None:
    """엑셀 파일 기반 일괄 조회"""
    config = Config.from_env()
    client = CodefRegisterClient(config)

    console.print(f"\n[bold blue]엑셀 파일 읽는 중:[/] {args.file}")

    try:
        requests_list = read_requests(args.file)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]오류:[/] {e}")
        sys.exit(1)

    # 결제 검증 (발급/열람 건이 있는 경우)
    for req in requests_list:
        payment_err = validate_payment_config(config, req.issue_type)
        if payment_err:
            console.print(f"[red]결제 오류:[/] {payment_err}")
            sys.exit(1)

    console.print(f"총 [bold]{len(requests_list)}건[/]의 요청을 처리합니다.\n")

    # 요청 목록 미리보기
    table = Table(title="요청 목록")
    table.add_column("#", style="dim", width=4)
    table.add_column("조회구분", width=10)
    table.add_column("주소/고유번호", min_width=30)
    table.add_column("동/호")
    table.add_column("부동산구분")
    table.add_column("발급유형")

    for i, req in enumerate(requests_list, 1):
        dong_ho = f"{req.dong} {req.ho}".strip() if req.dong or req.ho else "-"
        table.add_row(
            str(i), req.inquiry_type, req.display_name,
            dong_ho, req.realty_type, req.issue_type,
        )

    console.print(table)
    console.print()

    # 확인 프롬프트
    if not args.yes:
        confirm = console.input("[yellow]진행하시겠습니까? (y/N): [/]")
        if confirm.lower() not in ("y", "yes"):
            console.print("취소되었습니다.")
            return

    # 일괄 요청 실행
    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("처리 중...", total=len(requests_list))
        for i, req in enumerate(requests_list, 1):
            progress.update(
                task,
                description=f"[{i}/{len(requests_list)}] {req.display_name}",
            )
            result = client.request_register(req)
            # 배치에서는 2-Way 처리 생략 (대화형 선택 불가)
            results.append(result)
            progress.advance(task)

    # PDF 저장 및 결과 출력
    summaries = save_batch_pdfs(results, config.output_dir)

    result_table = Table(title="처리 결과")
    result_table.add_column("#", style="dim", width=4)
    result_table.add_column("주소/고유번호", min_width=30)
    result_table.add_column("상태")
    result_table.add_column("파일/오류")

    success_count = 0
    for i, summary in enumerate(summaries, 1):
        status = summary["status"]
        if status == "성공":
            success_count += 1
            style = "green"
            detail = os.path.basename(summary["file"]) if summary["file"] else ""
        else:
            style = "red"
            detail = summary.get("error", "")

        result_table.add_row(
            str(i), summary["address"], f"[{style}]{status}[/]", detail,
        )

    console.print()
    console.print(result_table)
    console.print(
        f"\n[bold]완료:[/] 성공 {success_count}건 / "
        f"실패 {len(summaries) - success_count}건"
    )
    console.print(f"저장 위치: {os.path.abspath(config.output_dir)}")


def cmd_search(args: argparse.Namespace) -> None:
    """주소 검색 (간편검색, 발급 없이 주소 목록만 조회)"""
    config = Config.from_env()
    client = CodefRegisterClient(config)

    req = RegisterRequest(
        inquiry_type="간편검색",
        address=args.query,
        issue_type="고유번호조회",  # 결제 불필요
        realty_type=args.realty_type,
    )

    console.print(f"\n[bold blue]검색 중:[/] {args.query}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("CODEF API 검색 중...", total=None)
        result = client.request_register(req)

    if result.need_two_way and result.addr_list:
        # 검색 결과 표시
        table = Table(title=f"검색 결과 ({len(result.addr_list)}건)")
        table.add_column("#", style="dim", width=4)
        table.add_column("주소", min_width=40)
        table.add_column("고유번호", width=18)
        table.add_column("부동산구분", width=12)

        for i, addr in enumerate(result.addr_list, 1):
            table.add_row(
                str(i),
                addr.get("address", addr.get("resAddr", "")),
                addr.get("uniqueNo", ""),
                addr.get("realtyType", ""),
            )

        console.print(table)
    elif result.success and result.data:
        console.print("[green]조회 완료[/]")
        addr_list = result.data.get("resAddrList", [])
        if addr_list:
            for i, addr in enumerate(addr_list, 1):
                console.print(
                    f"  {i}. {addr.get('address', '')} "
                    f"(고유번호: {addr.get('uniqueNo', '')})"
                )
        else:
            console.print("[dim]주소 목록 없음[/]")
    else:
        console.print(f"[red]검색 실패:[/] {result.error_message}")


def cmd_template(args: argparse.Namespace) -> None:
    """엑셀 템플릿 생성"""
    output_path = args.output or "등기부등본_요청_템플릿.xlsx"
    create_template(output_path)
    console.print(f"[green]템플릿 생성 완료:[/] {output_path}")
    console.print("이 파일에 주소를 입력한 후 [bold]batch[/] 명령으로 일괄 조회하세요.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="auto-iros: 인터넷 등기소 등기부등본 자동 발급 (CODEF API)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 엑셀 템플릿 생성
  python main.py template

  # 단건 조회 (간편검색)
  python main.py single -a "테헤란로 123"

  # 단건 조회 (고유번호)
  python main.py single --inquiry-type 고유번호 --unique-no "1101-2024-123456"

  # 주소 검색
  python main.py search "테헤란로"

  # 엑셀 기반 일괄 조회
  python main.py batch --file 요청목록.xlsx
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="실행할 명령")

    # single 명령
    single_parser = subparsers.add_parser("single", help="단건 등기부등본 조회")
    single_parser.add_argument("--address", "-a", help="검색어/주소")
    single_parser.add_argument("--unique-no", "-u", help="부동산 고유번호")
    single_parser.add_argument("--dong", "-d", help="동 (집합건물)")
    single_parser.add_argument("--ho", help="호 (집합건물)")
    single_parser.add_argument(
        "--inquiry-type", default="간편검색",
        choices=list(INQUIRY_TYPES.keys()),
        help="조회구분 (기본: 간편검색)",
    )
    single_parser.add_argument(
        "--realty-type", "-p", default="토지+건물",
        choices=["토지+건물", "토지", "건물", "집합건물"],
        help="부동산 구분 (기본: 토지+건물)",
    )
    single_parser.add_argument(
        "--register-type", "-r", default="전체",
        choices=["전체", "갑구", "을구", "표제부"],
        help="등기 유형 (기본: 전체)",
    )
    single_parser.add_argument(
        "--issue-type", "-i", default="열람",
        choices=["열람", "발급", "고유번호조회", "원문데이터"],
        help="발급 유형 (기본: 열람)",
    )

    # batch 명령
    batch_parser = subparsers.add_parser("batch", help="엑셀 파일 기반 일괄 조회")
    batch_parser.add_argument(
        "--file", "-f", required=True, help="요청 엑셀 파일 경로",
    )
    batch_parser.add_argument(
        "--yes", "-y", action="store_true", help="확인 없이 바로 실행",
    )

    # search 명령
    search_parser = subparsers.add_parser("search", help="주소 검색 (목록 조회)")
    search_parser.add_argument("query", help="검색어 (최소 3자리)")
    search_parser.add_argument(
        "--realty-type", default="토지+건물",
        choices=["토지+건물", "토지", "건물", "집합건물"],
        help="부동산 구분 (기본: 토지+건물)",
    )

    # template 명령
    template_parser = subparsers.add_parser("template", help="입력용 엑셀 템플릿 생성")
    template_parser.add_argument("--output", "-o", help="출력 파일 경로")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # 헤더 출력
    console.print(
        Panel(
            "[bold]auto-iros[/] - 인터넷 등기소 등기부등본 자동 발급\n"
            "CODEF API 기반 | github.com/muje2002/auto-iros",
            style="blue",
        )
    )

    # 점검 시간대 경고
    _check_maintenance()

    commands = {
        "single": cmd_single,
        "batch": cmd_batch,
        "search": cmd_search,
        "template": cmd_template,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
