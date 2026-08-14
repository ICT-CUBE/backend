"""아바타 소환 세션 생성·저장 로직."""

from datetime import datetime, timedelta, timezone
from typing import BinaryIO, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ApiError
from app.models.album import AlbumImage
from app.models.avatar import AvatarInteractionPicture, AvatarInteractionSession
from app.models.cube import CubeOwnership
from app.models.enums import (
    AlbumImageType,
    AvatarInteractionSessionStatus,
    OwnershipStatus,
)
from app.schemas.avatar import (
    AvatarInteractionSessionCreateItemResponse,
    AvatarInteractionSessionCreateResponse,
    YezulFrameResponse,
    YezulFramesResponse,
)
from app.services.blob_storage import (
    normalize_image_content_type,
    upload_avatar_interaction_picture,
)

CURRENT_USER_ID = 1
KOREA_TIMEZONE = timezone(timedelta(hours=9))


def create_avatar_interaction_session(
    *,
    db: Session,
) -> AvatarInteractionSessionCreateResponse:
    """현재 사용자의 활성 큐브 소유권에 아바타 소환 세션을 생성합니다."""
    ownership = cast(
        CubeOwnership,
        db.scalar(
            select(CubeOwnership)
            .where(
                CubeOwnership.user_id == CURRENT_USER_ID,
                CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
                CubeOwnership.is_last_accessed.is_(True),
            )
            .limit(1)
        )
    )

    interaction_session = AvatarInteractionSession(
        cube_ownership_id=ownership.id,
        started_at=datetime.now(KOREA_TIMEZONE).replace(tzinfo=None),
        ended_at=None,
        status=AvatarInteractionSessionStatus.ACTIVE,
    )
    try:
        db.add(interaction_session)
        db.flush()
        interaction_session_id = interaction_session.id
        db.commit()
    except Exception:
        db.rollback()
        raise

    return AvatarInteractionSessionCreateResponse(
        avatarInteractionSession=AvatarInteractionSessionCreateItemResponse(
            id=interaction_session_id,
        )
    )


def get_yezul_frames(*, db: Session) -> YezulFramesResponse:
    """예절샷 프레임 이미지를 id 오름차순으로 모두 반환합니다."""
    frames = db.scalars(
        select(AlbumImage)
        .where(AlbumImage.image_type == AlbumImageType.YEZUL_FRAME)
        .order_by(AlbumImage.id.asc())
    ).all()

    return YezulFramesResponse(
        yezulFrames=[
            YezulFrameResponse(
                id=frame.id,
                title=frame.title,
                imageUrl=frame.album_contents_img_url,
            )
            for frame in frames
        ]
    )


def save_avatar_interaction_session(
    *,
    db: Session,
    avatar_interaction_session_id: int,
) -> None:
    """아바타 소환 세션을 종료 상태로 저장합니다."""
    interaction_session = db.scalar(
        select(AvatarInteractionSession)
        .join(AvatarInteractionSession.cube_ownership)
        .where(
            AvatarInteractionSession.id == avatar_interaction_session_id,
            CubeOwnership.user_id == CURRENT_USER_ID,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
        )
        .limit(1)
    )
    if interaction_session is None:
        raise ApiError(
            status_code=404,
            code="AVATAR_INTERACTION_SESSION_NOT_FOUND",
            message="아바타 소환 세션을 찾을 수 없습니다.",
        )

    if (
        interaction_session.status == AvatarInteractionSessionStatus.COMPLETED
        or interaction_session.ended_at is not None
    ):
        raise ApiError(
            status_code=409,
            code="AVATAR_INTERACTION_SESSION_ALREADY_COMPLETED",
            message="이미 종료된 아바타 소환 세션입니다.",
        )

    interaction_session.status = AvatarInteractionSessionStatus.COMPLETED
    interaction_session.ended_at = datetime.now(KOREA_TIMEZONE).replace(tzinfo=None)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def save_avatar_interaction_picture(
    *,
    db: Session,
    avatar_interaction_session_id: int,
    image_file: BinaryIO,
    image_content_type: str | None,
    pictured_at: datetime,
) -> None:
    """현재 사용자의 아바타 소환 세션에 속한 사진을 Azure와 DB에 저장합니다."""
    # 세션 상태는 프론트 저장 흐름을 신뢰하고 검사하지 않습니다.
    interaction_session = db.scalar(
        select(AvatarInteractionSession)
        .join(AvatarInteractionSession.cube_ownership)
        .where(
            AvatarInteractionSession.id == avatar_interaction_session_id,
            CubeOwnership.user_id == CURRENT_USER_ID,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
        )
        .limit(1)
    )
    if interaction_session is None:
        raise ApiError(
            status_code=404,
            code="AVATAR_INTERACTION_SESSION_NOT_FOUND",
            message="아바타 소환 세션을 찾을 수 없습니다.",
        )

    normalized_content_type = normalize_image_content_type(image_content_type)
    if normalized_content_type is None:
        raise ApiError(
            status_code=400,
            code="INVALID_REQUEST",
            message="요청값이 올바르지 않습니다.",
        )

    try:
        image_url = upload_avatar_interaction_picture(
            file=image_file,
            content_type=normalized_content_type,
            user_id=CURRENT_USER_ID,
            avatar_interaction_session_id=interaction_session.id,
        )
    except Exception as exc:
        raise ApiError(
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="서버 내부 오류가 발생했습니다.",
        ) from exc

    pictured_at_kst = pictured_at.astimezone(KOREA_TIMEZONE).replace(tzinfo=None)
    picture = AvatarInteractionPicture(
        interaction_session_id=interaction_session.id,
        picture_img_url=image_url,
        pictured_at=pictured_at_kst,
        deleted_at=None,
    )
    try:
        db.add(picture)
        db.commit()
    except Exception:
        db.rollback()
        raise
