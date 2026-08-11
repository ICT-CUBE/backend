"""트랙 도메인 API 라우터."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Path, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ErrorResponse
from app.schemas.track import (
    TrackSessionCreateRequest,
    TrackSessionCreateResponse,
    TrackSessionUpdateRequest,
)
from app.services.track import (
    create_track_session,
    save_track_capture,
    save_track_session,
)

router = APIRouter()
track_session_router = APIRouter()


@router.post(
    "/{trackId}/sessions",
    response_model=TrackSessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="트랙 재생 세션 생성",
    description=(
        "트랙과 고정 사용자 ID 1의 마지막 활성 큐브 소유권을 기준으로 "
        "트랙 재생 세션을 생성합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "트랙 또는 큐브 소유권 정보가 없음",
            "content": {
                "application/json": {
                    "examples": {
                        "trackNotFound": {
                            "value": {
                                "code": "TRACK_NOT_FOUND",
                                "message": "앨범 트랙을 찾을 수 없습니다.",
                            }
                        },
                        "cubeOwnershipNotFound": {
                            "value": {
                                "code": "CUBE_OWNERSHIP_NOT_FOUND",
                                "message": "큐브 소유권을 찾을 수 없습니다.",
                            }
                        },
                    }
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "동일 트랙에 이미 PLAYING 세션이 있음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "TRACK_SESSION_ALREADY_PLAYING",
                        "message": "이미 재생 중인 트랙 세션이 있습니다.",
                    }
                }
            },
        },
    },
)
def create_playback_session(
    track_id: Annotated[int, Path(alias="trackId")],
    body: TrackSessionCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TrackSessionCreateResponse:
    """POST /api/v1/tracks/{trackId}/sessions"""
    return create_track_session(
        db=db,
        track_id=track_id,
        play_mode=body.playMode,
    )


@track_session_router.patch(
    "/{trackSessionId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="트랙 재생 세션 상태 저장",
    description=(
        "고정 사용자 ID 1의 PLAYING 트랙 세션에 종료 상태, 최종 재생 위치, "
        "실제 감상 시간과 한국시간 종료 시각을 저장합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "세션이 없거나 현재 사용자의 세션이 아님",
            "content": {
                "application/json": {
                    "example": {
                        "code": "TRACK_SESSION_NOT_FOUND",
                        "message": "트랙 재생 세션을 찾을 수 없습니다.",
                    }
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "이미 종료된 트랙 재생 세션",
            "content": {
                "application/json": {
                    "example": {
                        "code": "TRACK_SESSION_ALREADY_ENDED",
                        "message": "이미 종료된 트랙 재생 세션입니다.",
                    }
                }
            },
        },
    },
)
def update_playback_session(
    track_session_id: Annotated[int, Path(alias="trackSessionId")],
    body: TrackSessionUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """PATCH /api/v1/users/me/track-sessions/{trackSessionId}"""
    save_track_session(
        db=db,
        track_session_id=track_session_id,
        end_status=body.status,
        last_position_seconds=body.lastPositionSeconds,
        viewed_seconds=body.viewedSeconds,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@track_session_router.post(
    "/{trackSessionId}/captures",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="트랙 재생 캡처 저장",
    description=(
        "고정 사용자 ID 1의 트랙 세션을 확인하고, 캡처 이미지를 Azure Blob "
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
                        "code": "TRACK_SESSION_NOT_FOUND",
                        "message": "트랙 재생 세션을 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def create_track_capture(
    track_session_id: Annotated[int, Path(alias="trackSessionId")],
    image: Annotated[UploadFile, File(description="JPEG, PNG 또는 WebP 이미지")],
    captured_position_seconds: Annotated[
        int, Form(alias="capturedPositionSeconds")
    ],
    captured_at: Annotated[datetime, Form(alias="capturedAt")],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """POST /api/v1/users/me/track-sessions/{trackSessionId}/captures"""
    save_track_capture(
        db=db,
        track_session_id=track_session_id,
        image_file=image.file,
        image_content_type=image.content_type,
        captured_position_seconds=captured_position_seconds,
        captured_at=captured_at,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
