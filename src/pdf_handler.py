"""PDF 출력 및 저장 처리"""

import base64
import os
import re
from datetime import datetime

from .codef_api import RegisterResult


def sanitize_filename(name: str) -> str:
    """파일명에 사용할 수 없는 문자 제거"""
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", "_", name)
    return name[:100]


def save_pdf(result: RegisterResult, output_dir: str) -> str | None:
    """API 응답의 base64 PDF 데이터를 파일로 저장"""
    if not result.success or not result.pdf_base64:
        return None

    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = sanitize_filename(result.request.display_name)
    filename = f"등기부등본_{safe_name}_{timestamp}.pdf"
    filepath = os.path.join(output_dir, filename)

    pdf_bytes = base64.b64decode(result.pdf_base64)
    with open(filepath, "wb") as f:
        f.write(pdf_bytes)

    return filepath


def save_batch_pdfs(
    results: list[RegisterResult], output_dir: str
) -> list[dict]:
    """여러 건의 결과를 PDF로 저장하고 결과 요약 반환"""
    summaries = []

    for result in results:
        if result.success and result.pdf_base64:
            filepath = save_pdf(result, output_dir)
            summaries.append(
                {
                    "address": result.request.display_name,
                    "status": "성공",
                    "file": filepath,
                }
            )
        else:
            summaries.append(
                {
                    "address": result.request.display_name,
                    "status": "실패",
                    "file": None,
                    "error": result.error_message or "PDF 데이터 없음",
                }
            )

    return summaries
