from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.database import get_db, ping_database


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/")
    def root() -> dict[str, str]:
        return {"message": "hanium-api is running"}

    @app.get("/health")
    def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
        return {
            "status": "ok",
            "environment": settings.environment,
        }

    @app.get("/health/db")
    def health_db(_: Session = Depends(get_db)) -> dict[str, str]:
        ping_database()
        return {"status": "ok"}

    return app


app = create_app()
