"""컨테이너 생존(live) 및 서비스 준비(ready) 상태 확인 API."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine

router = APIRouter()


@router.get("/live")
async def liveness() -> dict[str, str]:
    """프로세스가 요청을 받을 수 있는지만 확인합니다."""
    return {"status": "ok"}


@router.get("/ready")
async def readiness() -> dict[str, str]:
    """MySQL 연결까지 성공해야 준비 상태로 판단합니다."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        # DB 상세 오류나 접속 정보가 응답에 노출되지 않도록 고정 메시지만 반환합니다.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        ) from exc
    return {"status": "ok", "database": "connected"}

