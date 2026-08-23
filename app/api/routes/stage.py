"""스테이지 도메인 API 라우터."""

from datetime import datetime
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Path,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.models.enums import StageVideoType
from app.schemas.common import ErrorResponse
from app.schemas.stage import (
    StageListResponse,
    StageSessionCreateRequest,
    StageSessionCreateResponse,
    StageSessionUpdateRequest,
    StageVideoDetailResponse,
)
from app.services.stage import (
    create_stage_session,
    get_stage_video,
    get_stages,
    save_stage_capture,
    save_stage_session,
)

router = APIRouter()
stage_session_router = APIRouter()


@router.get(
    "",
    response_model=StageListResponse,
    summary="스테이지 조회",
    description="현재 사용자의 스테이지 영상 목록을 조회합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "현재 사용자의 마지막 접근 ACTIVE 큐브 소유권이 존재하지 않음",
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
def read_stages(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    video_type: Annotated[
        StageVideoType,
        Query(alias="videoType"),
    ] = StageVideoType.MUSIC_VIDEO,
) -> StageListResponse:
    """GET /api/v1/stages"""
    return get_stages(
        db=db,
        current_user_id=current_user_id,
        video_type=video_type,
    )


@router.get(
    "/{stageId}",
    response_model=StageVideoDetailResponse,
    summary="스테이지 영상 조회",
    description="현재 사용자의 스테이지 영상 재생 정보를 조회합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "스테이지 또는 큐브 소유권 정보가 없음",
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
                        "stageNotFound": {
                            "summary": "스테이지 없음",
                            "value": {
                                "code": "STAGE_NOT_FOUND",
                                "message": "스테이지 영상을 찾을 수 없습니다.",
                            },
                        },
                    }
                }
            },
        },
    },
)
def read_stage_video(
    stage_id: Annotated[int, Path(alias="stageId")],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> StageVideoDetailResponse:
    """GET /api/v1/stages/{stageId}"""
    return get_stage_video(
        db=db,
        current_user_id=current_user_id,
        stage_id=stage_id,
    )


@router.post(
    "/{stageId}/sessions",
    response_model=StageSessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="스테이지 재생 세션 생성",
    description=(
        "활성 스테이지와 현재 사용자의 마지막 활성 큐브 소유권을 기준으로 "
        "재생 세션을 생성합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "활성 스테이지 또는 큐브 소유권 정보가 없음",
            "content": {
                "application/json": {
                    "examples": {
                        "stageNotFound": {
                            "value": {
                                "code": "STAGE_NOT_FOUND",
                                "message": "스테이지 영상을 찾을 수 없습니다.",
                            }
                        },
                        "cubeOwnershipNotFound": {
                            "value": {
                                "code": "CUBE_OWNERSHIP_NOT_FOUND",
                                "message": "큐브 소유권 정보를 찾을 수 없습니다.",
                            }
                        },
                    }
                }
            },
        },
    },
)
def create_playback_session(
    stage_id: Annotated[int, Path(alias="stageId")],
    body: StageSessionCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> StageSessionCreateResponse:
    """POST /api/v1/stages/{stageId}/sessions"""
    return create_stage_session(
        db=db,
        current_user_id=current_user_id,
        stage_id=stage_id,
        view_mode=body.view_mode,
    )


@stage_session_router.patch(
    "/{stageSessionId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="스테이지 재생 세션 저장",
    description=(
        "현재 사용자의 PLAYING 세션에 최종 재생 위치, 실제 누적 시청 시간, "
        "종료 상태와 한국시간 종료 시각을 저장합니다."
    ),
    responses={
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
    stage_session_id: Annotated[int, Path(alias="stageSessionId")],
    body: StageSessionUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> Response:
    """PATCH /api/v1/users/me/stage-sessions/{stageSessionId}"""
    save_stage_session(
        db=db,
        current_user_id=current_user_id,
        stage_session_id=stage_session_id,
        end_status=body.status,
        last_position_seconds=body.last_position_seconds,
        viewed_seconds=body.viewed_seconds,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@stage_session_router.post(
    "/{stageSessionId}/captures",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="스테이지 캡처 저장",
    description=(
        "현재 사용자의 스테이지 세션을 확인하고, 캡처 이미지를 Azure Blob "
        "Storage에 업로드한 뒤 이미지 URL과 촬영 정보를 DB에 저장합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "필수 multipart 필드가 없거나 지원하지 않는 이미지 형식",
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
    },
)
def create_stage_capture(
    stage_session_id: Annotated[int, Path(alias="stageSessionId", ge=1)],
    image: Annotated[UploadFile, File(description="JPG, JPEG, PNG 또는 WebP 이미지")],
    captured_position_seconds: Annotated[
        int, Form(alias="capturedPositionSeconds")
    ],
    captured_at: Annotated[datetime, Form(alias="capturedAt")],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> Response:
    """POST /api/v1/users/me/stage-sessions/{stageSessionId}/captures"""
    save_stage_capture(
        db=db,
        current_user_id=current_user_id,
        stage_session_id=stage_session_id,
        image_file=image.file,
        image_content_type=image.content_type,
        captured_position_seconds=captured_position_seconds,
        captured_at=captured_at,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
