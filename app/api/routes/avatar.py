"""아바타 도메인 API 라우터."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Path, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ErrorResponse
from app.schemas.avatar import (
    AvatarInteractionSessionCreateResponse,
    YezulFramesResponse,
)
from app.services.avatar import (
    create_avatar_interaction_session,
    get_yezul_frames,
    save_avatar_interaction_picture,
    save_avatar_interaction_session,
)

router = APIRouter()


@router.post(
    "/avatar-interaction-sessions",
    response_model=AvatarInteractionSessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="아바타 소환 세션 생성",
    description=(
        "고정 사용자 ID 1의 마지막 활성 큐브 소유권에 아바타 소환 "
        "세션을 생성합니다."
    ),
)
def create_interaction_session(
    db: Annotated[Session, Depends(get_db)],
) -> AvatarInteractionSessionCreateResponse:
    """POST /api/v1/users/me/avatar-interaction-sessions"""
    return create_avatar_interaction_session(db=db)


@router.get(
    "/album/yezul-frames",
    response_model=YezulFramesResponse,
    summary="예절샷 프레임 조회",
    description="album_image.image_type이 YEZUL_FRAME인 예절샷 프레임을 조회합니다.",
)
def read_yezul_frames(
    db: Annotated[Session, Depends(get_db)],
) -> YezulFramesResponse:
    """GET /api/v1/users/me/album/yezul-frames"""
    return get_yezul_frames(db=db)


@router.patch(
    "/avatar-interaction-sessions/{avatarInteractionSessionId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="아바타 소환 세션 상태 저장",
    description=(
        "고정 사용자 ID 1의 활성 큐브 소유권에 속한 아바타 소환 세션을 "
        "COMPLETED 상태로 저장하고 종료 시각을 기록합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "아바타 소환 세션을 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "AVATAR_INTERACTION_SESSION_NOT_FOUND",
                        "message": "아바타 소환 세션을 찾을 수 없습니다.",
                    }
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "이미 종료된 아바타 소환 세션",
            "content": {
                "application/json": {
                    "example": {
                        "code": "AVATAR_INTERACTION_SESSION_ALREADY_COMPLETED",
                        "message": "이미 종료된 아바타 소환 세션입니다.",
                    }
                }
            },
        },
    },
)
def update_interaction_session(
    db: Annotated[Session, Depends(get_db)],
    avatar_interaction_session_id: Annotated[
        int,
        Path(alias="avatarInteractionSessionId", ge=1),
    ],
) -> Response:
    """PATCH /api/v1/users/me/avatar-interaction-sessions/{avatarInteractionSessionId}"""
    save_avatar_interaction_session(
        db=db,
        avatar_interaction_session_id=avatar_interaction_session_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/avatar-interaction-sessions/{avatarInteractionSessionId}/pictures",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="아바타 소환 캡처 저장",
    description=(
        "고정 사용자 ID 1의 아바타 소환 세션을 확인하고, 촬영 이미지를 "
        "Azure Blob Storage에 업로드한 뒤 이미지 URL과 촬영 시각을 DB에 저장합니다."
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
            "description": "아바타 소환 세션을 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "AVATAR_INTERACTION_SESSION_NOT_FOUND",
                        "message": "아바타 소환 세션을 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def create_interaction_picture(
    avatar_interaction_session_id: Annotated[
        int,
        Path(alias="avatarInteractionSessionId", ge=1),
    ],
    image: Annotated[UploadFile, File(description="JPEG, PNG 또는 WebP 이미지")],
    pictured_at: Annotated[datetime, Form(alias="picturedAt")],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """POST /api/v1/users/me/avatar-interaction-sessions/{avatarInteractionSessionId}/pictures"""
    save_avatar_interaction_picture(
        db=db,
        avatar_interaction_session_id=avatar_interaction_session_id,
        image_file=image.file,
        image_content_type=image.content_type,
        pictured_at=pictured_at,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
