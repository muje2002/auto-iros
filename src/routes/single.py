"""단건 등기부등본 조회 API"""

import asyncio
import base64
import time
import uuid
from dataclasses import dataclass
from io import BytesIO

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..codef_api import CodefRegisterClient, RegisterRequest, RegisterResult
from ..config import Config
from ..payment import validate_payment_config
from ..register_parser import parse_registration_history, parse_registration_summary
from ..two_way import build_two_way_params

router = APIRouter(prefix="/api/single", tags=["single"])

# 2-Way 세션 저장소 (인메모리)
TWO_WAY_TIMEOUT = 120  # 초


@dataclass
class TwoWaySession:
    result: RegisterResult
    client: CodefRegisterClient
    created_at: float


_sessions: dict[str, TwoWaySession] = {}


def _cleanup_sessions() -> None:
    """만료된 2-Way 세션 정리"""
    now = time.time()
    expired = [
        sid for sid, s in _sessions.items()
        if now - s.created_at > TWO_WAY_TIMEOUT
    ]
    for sid in expired:
        del _sessions[sid]


# PDF 결과 임시 저장
_pdf_store: dict[str, str] = {}  # session_id -> base64 pdf


class SingleBody(BaseModel):
    inquiry_type: str = "간편검색"
    address: str = ""
    unique_no: str = ""
    dong: str = ""
    ho: str = ""
    realty_type: str = "토지+건물"
    register_type: str = "전체"
    issue_type: str = "열람"
    # 소재지번
    addr_sido: str = ""
    addr_dong: str = ""
    addr_lot_number: str = ""
    # 도로명주소
    addr_sigungu: str = ""
    addr_road_name: str = ""
    addr_building_number: str = ""


class TwoWayBody(BaseModel):
    session_id: str
    selected_index: int


@router.post("")
async def single_query(body: SingleBody, request: Request):
    """단건 조회 요청"""
    config: Config | None = request.app.state.config
    if config is None:
        return {"status": "error", "message": ".env 설정이 필요합니다. .env.example을 참고하세요."}

    # 결제 검증
    payment_err = validate_payment_config(config, body.issue_type)
    if payment_err:
        return {"status": "error", "message": payment_err}

    client = CodefRegisterClient(config)
    req = RegisterRequest(
        inquiry_type=body.inquiry_type,
        address=body.address,
        unique_no=body.unique_no,
        dong=body.dong,
        ho=body.ho,
        realty_type=body.realty_type,
        register_type=body.register_type,
        issue_type=body.issue_type,
        addr_sido=body.addr_sido,
        addr_dong=body.addr_dong,
        addr_lot_number=body.addr_lot_number,
        addr_sigungu=body.addr_sigungu,
        addr_road_name=body.addr_road_name,
        addr_building_number=body.addr_building_number,
    )

    try:
        result = await asyncio.to_thread(client.request_register, req)
    except Exception as e:
        return {"status": "error", "message": f"API 호출 실패: {e}"}

    if result.need_two_way:
        # 2-Way: 세션 저장 후 주소 목록 반환
        _cleanup_sessions()
        session_id = uuid.uuid4().hex
        _sessions[session_id] = TwoWaySession(
            result=result,
            client=client,
            created_at=time.time(),
        )
        return {
            "status": "two_way",
            "session_id": session_id,
            "addr_list": result.addr_list or [],
        }
    elif result.success:
        # 성공: PDF 저장
        session_id = uuid.uuid4().hex
        if result.pdf_base64:
            _pdf_store[session_id] = result.pdf_base64
        return _build_success_response(result, session_id)
    else:
        return {
            "status": "error",
            "message": result.error_message or "조회 실패",
        }


@router.post("/two-way")
async def two_way_select(body: TwoWayBody, request: Request):
    """2-Way 추가인증: 주소 선택 후 2차 요청"""
    _cleanup_sessions()

    session = _sessions.get(body.session_id)
    if not session:
        return {"status": "error", "message": "세션이 만료되었습니다. 다시 조회해주세요."}

    addr_list = session.result.addr_list or []
    if not (0 <= body.selected_index < len(addr_list)):
        return {"status": "error", "message": "잘못된 선택입니다."}

    selected_addr = addr_list[body.selected_index]
    two_way_info = build_two_way_params(session.result, selected_addr)

    try:
        result = await asyncio.to_thread(
            session.client.request_register,
            session.result.request,
            is_two_way=True,
            two_way_info=two_way_info,
        )
    except Exception as e:
        del _sessions[body.session_id]
        return {"status": "error", "message": f"2차 요청 실패: {e}"}

    # 세션 정리
    del _sessions[body.session_id]

    if result.success:
        pdf_id = uuid.uuid4().hex
        if result.pdf_base64:
            _pdf_store[pdf_id] = result.pdf_base64
        return _build_success_response(result, pdf_id)
    else:
        return {
            "status": "error",
            "message": result.error_message or "2차 요청 실패",
        }


def _build_success_response(result: RegisterResult, pdf_id: str) -> dict:
    """성공 응답 구성 (요약/이력 포함)"""
    resp: dict = {
        "status": "success",
        "message": "조회 성공",
        "has_pdf": bool(result.pdf_base64),
        "pdf_id": pdf_id if result.pdf_base64 else None,
        "display_name": result.request.display_name,
    }
    if result.data:
        summaries = parse_registration_summary(result.data)
        histories = parse_registration_history(result.data)
        if summaries:
            resp["registration_summary"] = [
                {"category": s.category, "content": s.content, "date": s.date}
                for s in summaries
            ]
        if histories:
            resp["registration_history"] = [
                {"type": h.reg_type, "purpose": h.purpose, "date": h.date, "number": h.number}
                for h in histories
            ]
    return resp


@router.get("/pdf/{pdf_id}")
async def download_pdf(pdf_id: str):
    """PDF 다운로드"""
    pdf_b64 = _pdf_store.pop(pdf_id, None)
    if not pdf_b64:
        return {"status": "error", "message": "PDF를 찾을 수 없습니다."}

    pdf_bytes = base64.b64decode(pdf_b64)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=register.pdf"},
    )
