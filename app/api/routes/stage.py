"""스테이지 도메인 API 라우터."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ErrorResponse
from app.schemas.stage import (
    StageSessionCreateRequest,
    StageSessionCreateResponse,
    StageSessionUpdateRequest,
)
from app.services.stage import create_stage_session, save_stage_session

router = APIRouter()
stage_session_router = APIRouter()


@router.post(
    "/{stageId}/sessions",
    response_model=StageSessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="스테이지 재생 세션 생성",
    description=(
        "활성 스테이지와 고정 사용자 ID 1의 마지막 활성 큐브 소유권을 기준으로 "
        "재생 세션을 생성합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "stageId 또는 요청 Body가 올바르지 않음",
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
            "description": "활성 스테이지 또는 마지막 활성 큐브 소유권이 없음",
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
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "동일 스테이지에 이미 PLAYING 세션이 있음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "STAGE_SESSION_ALREADY_PLAYING",
                        "message": "이미 재생 중인 스테이지 세션이 있습니다.",
                    }
                }
            },
        },
    },
)
def create_playback_session(
    stage_id: Annotated[int, Path(alias="stageId", ge=1)],
    body: StageSessionCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> StageSessionCreateResponse:
    """POST /api/v1/stages/{stageId}/sessions"""
    return create_stage_session(
        db=db,
        stage_id=stage_id,
        view_mode=body.viewMode,
    )


@stage_session_router.patch(
    "/{stageSessionId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="스테이지 재생 세션 저장",
    description=(
        "고정 사용자 ID 1의 PLAYING 세션에 최종 재생 위치, 실제 누적 시청 시간, "
        "종료 상태와 한국시간 종료 시각을 저장합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Path·Body가 잘못됐거나 최종 재생 위치가 영상 길이를 초과함",
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
            "description": "세션이 없거나 현재 사용자의 세션이 아님",
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
    },
)
def update_playback_session(
    stage_session_id: Annotated[int, Path(alias="stageSessionId", ge=1)],
    body: StageSessionUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """PATCH /api/v1/users/me/stage-sessions/{stageSessionId}"""
    save_stage_session(
        db=db,
        stage_session_id=stage_session_id,
        end_status=body.status,
        last_position_seconds=body.lastPositionSeconds,
        viewed_seconds=body.viewedSeconds,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
