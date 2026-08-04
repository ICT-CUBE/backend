"""현재 사용자의 홈·프로필 등 사용자 API 엔드포인트."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user_id
from app.db.session import get_db_session
from app.schemas.common import ErrorResponse
from app.schemas.home import HomeResponse
from app.services.home import get_home

router = APIRouter()


@router.get(
    "/me/home",
    response_model=HomeResponse,
    summary="홈 정보 조회",
    description=(
        "서비스 메인 홈 화면에 필요한 사용자, 큐브 소유권, 큐브, 친밀도 정보를 "
        "한 번에 반환합니다. 인증 없이 설정된 데모 사용자를 사용합니다."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "큐브 소유권 조회 권한 없음",
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
            "description": "활성 큐브 소유권 없음",
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
async def read_home(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> HomeResponse:
    """GET /api/v1/users/me/home"""
    return await get_home(session=session, user_id=user_id)
