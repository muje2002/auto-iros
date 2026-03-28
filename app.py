"""auto-iros 웹 서버 (FastAPI)

브라우저 기반 등기부등본 조회/발급 인터페이스.
실행: uvicorn app:app --reload
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import Config
from src.log import setup_logging
from src.maintenance import get_maintenance_warning
from src.routes import single, batch, search, template

setup_logging()

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="auto-iros", description="인터넷 등기소 등기부등본 자동 발급")

# 정적 파일 & 템플릿
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# 라우트 등록
app.include_router(single.router)
app.include_router(batch.router)
app.include_router(search.router)
app.include_router(template.router)


app.state.config = None  # 기본값


@app.on_event("startup")
def startup() -> None:
    """서버 시작 시 설정 검증 및 로드"""
    try:
        app.state.config = Config.from_env()
    except ValueError as e:
        import logging
        logging.getLogger(__name__).warning("설정 로드 실패: %s", e)


def _ctx(request: Request) -> dict:
    """템플릿 공통 컨텍스트 (점검 경고 포함)"""
    return {
        "request": request,
        "maintenance_warning": get_maintenance_warning(),
    }


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", _ctx(request))


@app.get("/single")
async def single_page(request: Request):
    return templates.TemplateResponse("single.html", _ctx(request))


@app.get("/batch")
async def batch_page(request: Request):
    return templates.TemplateResponse("batch.html", _ctx(request))


@app.get("/search")
async def search_page(request: Request):
    return templates.TemplateResponse("search.html", _ctx(request))
