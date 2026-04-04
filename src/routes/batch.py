"""일괄 조회 API"""

import asyncio
import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from ..codef_api import (
    BATCH_REQUEST_DELAY,
    CodefRegisterClient,
    RegisterRequest,
    RegisterResult,
)
from ..config import Config
from ..excel_handler import export_results, read_requests
from ..payment import validate_payment_config
from ..pdf_handler import save_batch_pdfs

router = APIRouter(prefix="/api/batch", tags=["batch"])


@router.post("/upload")
async def upload_excel(request: Request, file: UploadFile = File(...)):
    """엑셀 파일 업로드 → 요청 목록 미리보기 반환"""
    config: Config | None = request.app.state.config
    if config is None:
        return {"status": "error", "message": ".env 설정이 필요합니다."}
    # 임시 파일에 저장
    suffix = Path(file.filename or "upload.xlsx").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        requests_list = read_requests(tmp_path)
    except (FileNotFoundError, ValueError) as e:
        os.unlink(tmp_path)
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # 미리보기 데이터 반환
    preview = []
    for i, req in enumerate(requests_list):
        preview.append({
            "index": i,
            "inquiry_type": req.inquiry_type,
            "display_name": req.display_name,
            "dong": req.dong,
            "ho": req.ho,
            "realty_type": req.realty_type,
            "issue_type": req.issue_type,
        })

    return {
        "status": "success",
        "count": len(requests_list),
        "preview": preview,
        # 직렬화된 요청 데이터 (execute에 재전달)
        "requests_data": [_serialize_request(req) for req in requests_list],
    }


def _serialize_request(req: RegisterRequest) -> dict:
    """RegisterRequest를 JSON 직렬화 가능한 dict로 변환"""
    return {
        "inquiry_type": req.inquiry_type,
        "address": req.address,
        "unique_no": req.unique_no,
        "dong": req.dong,
        "ho": req.ho,
        "realty_type": req.realty_type,
        "register_type": req.register_type,
        "issue_type": req.issue_type,
        "addr_sido": req.addr_sido,
        "addr_dong": req.addr_dong,
        "addr_lot_number": req.addr_lot_number,
        "addr_sigungu": req.addr_sigungu,
        "addr_road_name": req.addr_road_name,
        "addr_building_number": req.addr_building_number,
    }


def _deserialize_request(data: dict) -> RegisterRequest:
    """dict를 RegisterRequest로 변환"""
    return RegisterRequest(
        inquiry_type=data.get("inquiry_type", "간편검색"),
        address=data.get("address", ""),
        unique_no=data.get("unique_no", ""),
        dong=data.get("dong", ""),
        ho=data.get("ho", ""),
        realty_type=data.get("realty_type", "토지+건물"),
        register_type=data.get("register_type", "전체"),
        issue_type=data.get("issue_type", "열람"),
        addr_sido=data.get("addr_sido", ""),
        addr_dong=data.get("addr_dong", ""),
        addr_lot_number=data.get("addr_lot_number", ""),
        addr_sigungu=data.get("addr_sigungu", ""),
        addr_road_name=data.get("addr_road_name", ""),
        addr_building_number=data.get("addr_building_number", ""),
    )


class ExecuteBody(BaseModel):
    requests_data: list[dict]


@router.post("/execute")
async def execute_batch(body: ExecuteBody, request: Request):
    """일괄 조회 실행"""
    config: Config | None = request.app.state.config
    if config is None:
        return {"status": "error", "message": ".env 설정이 필요합니다."}

    requests_list = [_deserialize_request(d) for d in body.requests_data]

    # 결제 검증
    for req in requests_list:
        payment_err = validate_payment_config(config, req.issue_type)
        if payment_err:
            return {"status": "error", "message": payment_err}

    client = CodefRegisterClient(config)

    # 순차 실행 (to_thread로 블로킹 방지, 요청 간 딜레이)
    results = []
    for i, req in enumerate(requests_list):
        if i > 0:
            await asyncio.sleep(BATCH_REQUEST_DELAY)
        try:
            result = await asyncio.to_thread(client.request_register, req)
        except Exception as e:
            from ..codef_api import RegisterResult
            result = RegisterResult(
                request=req, success=False, error_message=f"API 호출 실패: {e}",
            )
        results.append(result)

    # PDF 저장
    summaries = save_batch_pdfs(results, config.output_dir)

    # 결과 엑셀 생성
    result_excel_name = "조회결과.xlsx"
    result_excel_path = os.path.join(config.output_dir, result_excel_name)
    os.makedirs(config.output_dir, exist_ok=True)
    export_results(summaries, result_excel_path)

    return {
        "status": "success",
        "count": len(summaries),
        "success_count": sum(1 for s in summaries if s["status"] == "성공"),
        "result_excel": result_excel_name,
        "results": [
            {
                "address": s["address"],
                "unique_no": s.get("unique_no", ""),
                "status": s["status"],
                "filename": os.path.basename(s["file"]) if s.get("file") else None,
                "error": s.get("error"),
            }
            for s in summaries
        ],
        # 실패 건 재처리용 데이터
        "failed_requests": [
            body.requests_data[i]
            for i, s in enumerate(summaries)
            if s["status"] != "성공"
        ],
    }


@router.post("/execute-stream")
async def execute_batch_stream(body: ExecuteBody, request: Request):
    """일괄 조회 실행 (SSE로 건별 진행률 실시간 전달)"""
    config: Config | None = request.app.state.config
    if config is None:
        return {"status": "error", "message": ".env 설정이 필요합니다."}

    requests_list = [_deserialize_request(d) for d in body.requests_data]

    for req in requests_list:
        payment_err = validate_payment_config(config, req.issue_type)
        if payment_err:
            return {"status": "error", "message": payment_err}

    async def event_generator():
        client = CodefRegisterClient(config)
        results: list[RegisterResult] = []
        total = len(requests_list)

        for i, req in enumerate(requests_list):
            if i > 0:
                await asyncio.sleep(BATCH_REQUEST_DELAY)

            # 진행 이벤트
            yield _sse_event("progress", {
                "current": i + 1, "total": total,
                "address": req.display_name, "status": "processing",
            })

            try:
                result = await asyncio.to_thread(client.request_register, req)
            except Exception as e:
                result = RegisterResult(
                    request=req, success=False,
                    error_message=f"API 호출 실패: {e}",
                )
            results.append(result)

            # 건별 결과 이벤트
            yield _sse_event("item", {
                "current": i + 1, "total": total,
                "address": req.display_name,
                "success": result.success,
                "error": result.error_message,
            })

        # PDF 저장 + 결과 엑셀
        summaries = save_batch_pdfs(results, config.output_dir)
        result_excel_name = "조회결과.xlsx"
        result_excel_path = os.path.join(config.output_dir, result_excel_name)
        os.makedirs(config.output_dir, exist_ok=True)
        export_results(summaries, result_excel_path)

        # 최종 결과
        yield _sse_event("done", {
            "count": len(summaries),
            "success_count": sum(1 for s in summaries if s["status"] == "성공"),
            "result_excel": result_excel_name,
            "results": [
                {
                    "address": s["address"],
                    "status": s["status"],
                    "filename": os.path.basename(s["file"]) if s.get("file") else None,
                    "error": s.get("error"),
                }
                for s in summaries
            ],
            "failed_requests": [
                body.requests_data[i]
                for i, s in enumerate(summaries)
                if s["status"] != "성공"
            ],
        })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse_event(event: str, data: dict) -> str:
    """SSE 이벤트 포맷"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/download/{filename}")
async def download_batch_file(filename: str, request: Request):
    """일괄 조회 결과 파일 다운로드 (PDF 또는 엑셀)"""
    config: Config | None = request.app.state.config
    if config is None:
        return {"status": "error", "message": ".env 설정이 필요합니다."}
    filepath = os.path.join(config.output_dir, filename)

    if not os.path.exists(filepath):
        return {"status": "error", "message": "파일을 찾을 수 없습니다."}

    media_type = "application/pdf"
    if filename.endswith(".xlsx"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return FileResponse(path=filepath, filename=filename, media_type=media_type)
