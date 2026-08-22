"""미션 도메인 API 라우터."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.schemas.common import ErrorResponse
from app.schemas.mission import MissionListResponse
from app.services.mission import get_missions

router = APIRouter()


@router.get(
    "/missions",
    response_model=MissionListResponse,
    summary="미션 목록 조회",
    description="현재 사용자의 미션 화면 정보를 조회합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "활성화된 마지막 접근 큐브 소유권이 존재하지 않음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "ACTIVE_CUBE_OWNERSHIP_NOT_FOUND",
                        "message": "활성화된 큐브 소유권을 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def read_missions(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> MissionListResponse:
    """GET /api/v1/users/me/missions"""
    return get_missions(db=db, current_user_id=current_user_id)
