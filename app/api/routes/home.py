"""홈 도메인 API 라우터."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ErrorResponse
from app.schemas.home import HomeResponse
from app.services.home import get_home

router = APIRouter()


@router.get(
    "/home",
    response_model=HomeResponse,
    summary="홈 정보 조회",
    description="로그인 구현 전 고정 사용자 ID 1의 홈 화면 정보를 조회합니다.",
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
            "description": "사용자의 큐브 소유권이 존재하지 않음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "CUBE_OWNERSHIP_NOT_FOUND",
                        "message": "큐브 소유권 정보를 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def read_home(db: Annotated[Session, Depends(get_db)]) -> HomeResponse:
    """GET /api/v1/users/me/home"""
    return get_home(db)
