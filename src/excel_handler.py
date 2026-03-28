"""엑셀 파일 기반 주소 일괄 입력 처리"""

import os
from openpyxl import Workbook, load_workbook

from .codef_api import RegisterRequest, PROPERTY_TYPES, REGISTER_TYPES, ISSUE_TYPES


# 엑셀 컬럼 헤더 정의
HEADERS = [
    "주소",
    "동",
    "호",
    "부동산구분",
    "등기유형",
    "발급유형",
    "고유번호",
]

# 기본값
DEFAULTS = {
    "부동산구분": "건물",
    "등기유형": "전체",
    "발급유형": "발급",
}


def create_template(output_path: str) -> str:
    """입력용 엑셀 템플릿 생성"""
    wb = Workbook()
    ws = wb.active
    ws.title = "등기부등본 요청"

    # 헤더 작성
    for col, header in enumerate(HEADERS, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = cell.font.copy(bold=True)

    # 컬럼 너비 조정
    ws.column_dimensions["A"].width = 50  # 주소
    ws.column_dimensions["B"].width = 10  # 동
    ws.column_dimensions["C"].width = 10  # 호
    ws.column_dimensions["D"].width = 15  # 부동산구분
    ws.column_dimensions["E"].width = 12  # 등기유형
    ws.column_dimensions["F"].width = 12  # 발급유형
    ws.column_dimensions["G"].width = 20  # 고유번호

    # 안내 시트
    guide = wb.create_sheet("입력안내")
    guide_data = [
        ["컬럼", "설명", "필수여부", "허용값"],
        ["주소", "부동산 소재지 전체 주소", "필수", "예: 서울특별시 강남구 테헤란로 123"],
        ["동", "집합건물의 동 (해당시)", "선택", ""],
        ["호", "집합건물의 호 (해당시)", "선택", ""],
        ["부동산구분", "부동산 유형", "선택(기본:건물)", ", ".join(PROPERTY_TYPES.keys())],
        ["등기유형", "등기 조회 범위", "선택(기본:전체)", ", ".join(REGISTER_TYPES.keys())],
        ["발급유형", "열람 또는 발급", "선택(기본:발급)", ", ".join(ISSUE_TYPES.keys())],
        ["고유번호", "부동산 고유번호 (알고 있는 경우)", "선택", ""],
    ]
    for row_idx, row_data in enumerate(guide_data, 1):
        for col_idx, value in enumerate(row_data, 1):
            guide.cell(row=row_idx, column=col_idx, value=value)

    # 예시 데이터 (2~3행)
    examples = [
        ["서울특별시 강남구 테헤란로 123", "", "", "건물", "전체", "발급", ""],
        ["서울특별시 서초구 서초대로 456", "101동", "202호", "집합건물", "전체", "발급", ""],
    ]
    for row_idx, example in enumerate(examples, 2):
        for col_idx, value in enumerate(example, 1):
            ws.cell(row=row_idx, column=col_idx, value=value)

    wb.save(output_path)
    return output_path


def read_requests(file_path: str) -> list[RegisterRequest]:
    """엑셀 파일에서 등기부등본 요청 목록 읽기"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    wb = load_workbook(file_path, read_only=True)
    ws = wb.active

    requests_list = []
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
        if not row or not row[0]:
            continue

        address = str(row[0]).strip()
        if not address:
            continue

        def cell_val(idx: int) -> str:
            if idx < len(row) and row[idx] is not None:
                return str(row[idx]).strip()
            return ""

        req = RegisterRequest(
            address=address,
            dong=cell_val(1),
            ho=cell_val(2),
            property_type=cell_val(3) or DEFAULTS["부동산구분"],
            register_type=cell_val(4) or DEFAULTS["등기유형"],
            issue_type=cell_val(5) or DEFAULTS["발급유형"],
            unique_no=cell_val(6),
        )
        requests_list.append(req)

    wb.close()

    if not requests_list:
        raise ValueError(f"엑셀 파일에 유효한 요청 데이터가 없습니다: {file_path}")

    return requests_list
