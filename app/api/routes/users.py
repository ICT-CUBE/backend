"""현재 데모 사용자를 기준으로 동작하는 사용자 API."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user_id
from app.db.session import get_db_session
from app.schemas.common import ErrorResponse
from app.schemas.home import HomeResponse
from app.schemas.stage import StageSessionUpdateRequest
from app.services.home import get_home
from app.services.stage import update_stage_session

router = APIRouter()


@router.get(
    "/me/home",
    response_model=HomeResponse,
    summary="홈 정보 조회",
    description=(
        "인증 없이 DB의 데모 사용자를 기준으로 사용자, 큐브 소유권, 큐브, 친밀도 정보를 반환합니다."
    ),
    responses={
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
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "예상하지 못한 서버 또는 데이터 오류",
            "content": {
                "application/json": {
                    "example": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "서버 오류가 발생했습니다.",
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


@router.patch(
    "/me/stage-sessions/{stageSessionId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="스테이지 세션 상태 저장",
    description=(
        "인증 없이 DB의 데모 사용자를 기준으로 재생 중인 스테이지 세션의 "
        "최종 재생 위치, 실제 시청 시간과 종료 상태를 저장합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "경로 또는 요청 Body가 올바르지 않음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "INVALID_REQUEST",
                        "message": "요청값이 올바르지 않습니다.",
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "현재 사용자의 스테이지 재생 세션을 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "STAGE_SESSION_NOT_FOUND",
                        "message": "스테이지 재생 세션을 찾을 수 없습니다.",
                    }
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "이미 종료된 스테이지 재생 세션",
            "content": {
                "application/json": {
                    "example": {
                        "code": "STAGE_SESSION_ALREADY_ENDED",
                        "message": "이미 종료된 스테이지 재생 세션입니다.",
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
async def save_stage_session_state(
    stage_session_id: Annotated[int, Path(alias="stageSessionId", ge=1)],
    body: StageSessionUpdateRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    """PATCH /api/v1/users/me/stage-sessions/{stageSessionId}"""
    await update_stage_session(
        session=session,
        user_id=user_id,
        stage_session_id=stage_session_id,
        playback_status=body.status,
        last_position_seconds=body.last_position_seconds,
        viewed_seconds=body.viewed_seconds,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
