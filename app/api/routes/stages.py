"""스테이지 영상 및 재생 세션 API."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user_id
from app.db.session import get_db_session
from app.schemas.common import ErrorResponse
from app.schemas.stage import StageSessionCreateRequest, StageSessionCreateResponse
from app.services.stage import create_stage_session

router = APIRouter()


@router.post(
    "/{stageId}/sessions",
    response_model=StageSessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="스테이지 재생 세션 생성",
    description=(
        "인증 없이 DB의 데모 사용자를 기준으로 NORMAL 또는 AR 모드의 "
        "스테이지 재생 세션을 생성합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "stageId 또는 요청 Body가 올바르지 않음",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "스테이지 또는 활성 큐브 소유권 없음",
            "content": {
                "application/json": {
                    "examples": {
                        "stageNotFound": {
                            "value": {
                                "code": "STAGE_NOT_FOUND",
                                "message": "스테이지 영상을 찾을 수 없습니다.",
                            }
                        },
                        "activeCubeOwnershipNotFound": {
                            "value": {
                                "code": "ACTIVE_CUBE_OWNERSHIP_NOT_FOUND",
                                "message": "활성화된 큐브 소유권을 찾을 수 없습니다.",
                            }
                        },
                    }
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "예상하지 못한 서버 또는 DB 오류",
        },
    },
)
async def create_stage_playback_session(
    stage_id: Annotated[int, Path(alias="stageId", ge=1)],
    body: StageSessionCreateRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StageSessionCreateResponse:
    """POST /api/v1/stages/{stageId}/sessions"""
    return await create_stage_session(
        session=session,
        user_id=user_id,
        stage_id=stage_id,
        view_mode=body.view_mode,
    )
