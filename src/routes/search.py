"""주소 검색 API"""

import asyncio

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ..codef_api import CodefRegisterClient, RegisterRequest
from ..config import Config

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchBody(BaseModel):
    query: str
    realty_type: str = "토지+건물"


@router.post("")
async def search_address(body: SearchBody, request: Request):
    """주소 검색 (결제 불필요, 목록만 반환)"""
    config: Config | None = request.app.state.config
    if config is None:
        return {"status": "error", "message": ".env 설정이 필요합니다. .env.example을 참고하세요."}
    client = CodefRegisterClient(config)

    req = RegisterRequest(
        inquiry_type="간편검색",
        address=body.query,
        issue_type="고유번호조회",
        realty_type=body.realty_type,
    )

    try:
        result = await asyncio.to_thread(client.request_register, req)
    except Exception as e:
        return {"status": "error", "message": f"API 호출 실패: {e}"}

    if result.need_two_way and result.addr_list:
        return {
            "status": "success",
            "addr_list": result.addr_list,
            "count": len(result.addr_list),
        }
    elif result.success and result.data:
        addr_list = result.data.get("resAddrList", [])
        return {
            "status": "success",
            "addr_list": addr_list,
            "count": len(addr_list),
        }
    else:
        return {
            "status": "error",
            "message": result.error_message or "검색 결과가 없습니다.",
        }
