"""앨범 도메인 API 라우터."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Path, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.album.schemas import (
    AlbumResponse,
    AlbumTrackDetailGetResponse,
    TrackSessionCreateRequest,
    TrackSessionCreateResponse,
    TrackSessionUpdateRequest,
)
from app.album.service import (
    create_track_session,
    get_album,
    get_album_track,
    save_track_capture,
    save_track_session,
)
from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.core.schemas import ErrorResponse

album_router = APIRouter()
router = APIRouter()
track_session_router = APIRouter()


@album_router.get(
    "",
    response_model=AlbumResponse,
    summary="앨범 조회",
    description="현재 사용자의 앨범 화면 정보를 조회합니다.",
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
def read_album(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> AlbumResponse:
    """GET /api/v1/album"""
    return get_album(db=db, current_user_id=current_user_id)


@router.get(
    "/{trackId}",
    response_model=AlbumTrackDetailGetResponse,
    summary="앨범 트랙 조회",
    description="현재 사용자의 앨범 트랙 재생 정보를 조회합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "트랙 또는 큐브 소유권 정보가 없음",
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
                        "trackNotFound": {
                            "summary": "앨범 트랙 없음",
                            "value": {
                                "code": "TRACK_NOT_FOUND",
                                "message": "앨범 트랙을 찾을 수 없습니다.",
                            },
                        },
                    }
                }
            },
        },
    },
)
def read_album_track(
    track_id: Annotated[int, Path(alias="trackId")],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> AlbumTrackDetailGetResponse:
    """GET /api/v1/tracks/{trackId}"""
    return get_album_track(
        db=db,
        current_user_id=current_user_id,
        track_id=track_id,
    )


@router.post(
    "/{trackId}/sessions",
    response_model=TrackSessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="트랙 재생 세션 생성",
    description=(
        "트랙과 현재 사용자의 마지막 활성 큐브 소유권을 기준으로 "
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
    },
)
def create_playback_session(
    track_id: Annotated[int, Path(alias="trackId")],
    body: TrackSessionCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> TrackSessionCreateResponse:
    """POST /api/v1/tracks/{trackId}/sessions"""
    return create_track_session(
        db=db,
        current_user_id=current_user_id,
        track_id=track_id,
        play_mode=body.play_mode,
    )


@track_session_router.patch(
    "/{trackSessionId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="트랙 재생 세션 상태 저장",
    description=(
        "현재 사용자의 PLAYING 트랙 세션에 종료 상태, 최종 재생 위치, "
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
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> Response:
    """PATCH /api/v1/users/me/track-sessions/{trackSessionId}"""
    save_track_session(
        db=db,
        current_user_id=current_user_id,
        track_session_id=track_session_id,
        end_status=body.status,
        last_position_seconds=body.last_position_seconds,
        viewed_seconds=body.viewed_seconds,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@track_session_router.post(
    "/{trackSessionId}/captures",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="트랙 재생 캡처 저장",
    description=(
        "현재 사용자의 트랙 세션을 확인하고, 캡처 이미지를 Azure Blob "
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
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> Response:
    """POST /api/v1/users/me/track-sessions/{trackSessionId}/captures"""
    save_track_capture(
        db=db,
        current_user_id=current_user_id,
        track_session_id=track_session_id,
        image_file=image.file,
        image_content_type=image.content_type,
        captured_position_seconds=captured_position_seconds,
        captured_at=captured_at,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
