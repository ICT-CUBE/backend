from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

# 다른 도메인 모델을 문자열로 참조하는 관계를 해석하려면 모든 ORM 모델이 등록돼 있어야 합니다.
from app import models  # noqa: F401
from app.core.config import Settings, get_settings
from app.core.database import get_db, ping_database
from app.core.exceptions import (
    ApiError,
    api_error_handler,
    internal_server_error_handler,
    request_validation_error_handler,
)
from app.core.openapi import configure_openapi
from app.router import api_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
    )
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(Exception, internal_server_error_handler)
    app.add_exception_handler(
        RequestValidationError,
        request_validation_error_handler,
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    configure_openapi(app)

    @app.get("/")
    def root() -> dict[str, str]:
        return {"message": "hanium-api is running"}

    @app.get("/health")
    def health(
        settings: Annotated[Settings, Depends(get_settings)],
    ) -> dict[str, str]:
        return {
            "status": "ok",
            "environment": settings.environment,
        }

    @app.get("/health/db")
    def health_db(_: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
        ping_database()
        return {"status": "ok"}

    return app


app = create_app()
