"""엑셀 템플릿 다운로드 API"""

import tempfile
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from ..excel_handler import create_template

router = APIRouter(prefix="/api/template", tags=["template"])


@router.get("/download")
async def download_template():
    """엑셀 입력 템플릿 다운로드"""
    tmp = Path(tempfile.mkdtemp()) / "등기부등본_요청_템플릿.xlsx"
    create_template(str(tmp))
    return FileResponse(
        path=str(tmp),
        filename="등기부등본_요청_템플릿.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
