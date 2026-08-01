"""애플리케이션 공통 로깅 설정."""

import logging

from app.core.config import get_settings


def configure_logging() -> None:
    """Container Apps가 수집하기 쉬운 표준 출력 로그를 활성화합니다."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

