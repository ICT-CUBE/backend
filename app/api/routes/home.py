"""홈 화면 API 라우터."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.schemas.common import ErrorResponse
from app.schemas.home import HomeResponse
from app.services.home import get_home

router = APIRouter()


@router.get(
    "/home",
    response_model=HomeResponse,
    summary="홈 정보 조회",
    description="현재 사용자의 홈 화면 정보를 조회합니다.",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "소유권은 존재하지만 ACTIVE 상태가 아님",
            "content": {
                "application/json": {
                    "example": {
                        "code": "CUBE_OWNERSHIP_FORBIDDEN",
                        "message": "해당 큐브 소유권 정보를 조회할 권한이 없습니다.",
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "큐브 소유권 또는 친밀도 정보가 존재하지 않음",
            "content": {
                "application/json": {
                    "examples": {
                        "cubeOwnershipNotFound": {
                            "summary": "큐브 소유권 없음",
                            "value": {
                                "code": "CUBE_OWNERSHIP_NOT_FOUND",
                                "message": "큐브 소유권 정보를 찾을 수 없습니다.",
                            },
                        },
                        "cubeAffinityNotFound": {
                            "summary": "큐브 친밀도 없음",
                            "value": {
                                "code": "CUBE_AFFINITY_NOT_FOUND",
                                "message": "큐브 친밀도 정보를 찾을 수 없습니다.",
                            },
                        },
                    }
                }
            },
        },
    },
)
def read_home(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> HomeResponse:
    """GET /api/v1/users/me/home"""
    return get_home(db=db, current_user_id=current_user_id)
