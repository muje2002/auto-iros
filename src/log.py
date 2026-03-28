"""로깅 설정 모듈"""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """애플리케이션 로깅 설정.

    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
    """
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        datefmt=datefmt,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
