"""트랙 재생 세션 생성 로직."""

from datetime import datetime, timedelta, timezone
from typing import BinaryIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ApiError
from app.models.cube import CubeOwnership
from app.models.enums import (
    OwnershipStatus,
    TrackPlayMode,
    TrackSessionStatus,
)
from app.models.track import Track, TrackCapture, TrackSession
from app.schemas.track import (
    TrackSessionCreateResponse,
    TrackSessionEndStatus,
    TrackSessionResponse,
)
from app.services.blob_storage import normalize_image_content_type, upload_track_capture

KOREA_TIMEZONE = timezone(timedelta(hours=9))


def create_track_session(
    *,
    db: Session,
    current_user_id: int,
    track_id: int,
    play_mode: TrackPlayMode,
) -> TrackSessionCreateResponse:
    """트랙과 현재 사용자의 마지막 활성 소유권으로 재생 세션을 만듭니다."""
    track = db.get(Track, track_id)
    if track is None:
        raise ApiError(
            status_code=404,
            code="TRACK_NOT_FOUND",
            message="앨범 트랙을 찾을 수 없습니다.",
        )

    # 동일 소유권에 대한 동시 생성 요청이 중복 세션을 만들지 않게 잠급니다.
    ownership = db.scalar(
        select(CubeOwnership)
        .where(
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .limit(1)
        .with_for_update()
    )
    if ownership is None:
        raise ApiError(
            status_code=404,
            code="CUBE_OWNERSHIP_NOT_FOUND",
            message="큐브 소유권을 찾을 수 없습니다.",
        )

    # 다른 트랙의 PLAYING 세션은 검사하지 않고 같은 트랙의 중복만 막습니다.
    playing_session_id = db.scalar(
        select(TrackSession.id)
        .where(
            TrackSession.cube_ownership_id == ownership.id,
            TrackSession.track_id == track.id,
            TrackSession.status == TrackSessionStatus.PLAYING,
        )
        .limit(1)
    )
    if playing_session_id is not None:
        db.rollback()
        raise ApiError(
            status_code=409,
            code="TRACK_SESSION_ALREADY_PLAYING",
            message="이미 재생 중인 트랙 세션이 있습니다.",
        )

    track_session = TrackSession(
        cube_ownership_id=ownership.id,
        track_id=track.id,
        started_at=datetime.now(KOREA_TIMEZONE).replace(tzinfo=None),
        ended_at=None,
        last_position_seconds=0,
        viewed_seconds=0,
        play_mode=play_mode,
        status=TrackSessionStatus.PLAYING,
    )
    try:
        db.add(track_session)
        db.flush()
        track_session_id = track_session.id
        db.commit()
    except Exception:
        db.rollback()
        raise

    return TrackSessionCreateResponse(
        track_session=TrackSessionResponse(
            id=track_session_id,
            play_mode=play_mode,
        )
    )


def save_track_session(
    *,
    db: Session,
    current_user_id: int,
    track_session_id: int,
    end_status: TrackSessionEndStatus,
    last_position_seconds: int,
    viewed_seconds: int,
) -> None:
    """현재 사용자의 PLAYING 트랙 세션을 종료 상태로 저장합니다."""
    # 합의에 따라 동시 요청을 위한 행 잠금과 숫자 범위 검증은 하지 않습니다.
    track_session = db.scalar(
        select(TrackSession)
        .join(TrackSession.cube_ownership)
        .where(
            TrackSession.id == track_session_id,
            CubeOwnership.user_id == current_user_id,
        )
        .limit(1)
    )
    if track_session is None:
        raise ApiError(
            status_code=404,
            code="TRACK_SESSION_NOT_FOUND",
            message="트랙 재생 세션을 찾을 수 없습니다.",
        )
    if track_session.status != TrackSessionStatus.PLAYING:
        raise ApiError(
            status_code=409,
            code="TRACK_SESSION_ALREADY_ENDED",
            message="이미 종료된 트랙 재생 세션입니다.",
        )

    track_session.status = TrackSessionStatus(end_status.value)
    track_session.last_position_seconds = last_position_seconds
    track_session.viewed_seconds = viewed_seconds
    track_session.ended_at = datetime.now(KOREA_TIMEZONE).replace(tzinfo=None)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def save_track_capture(
    *,
    db: Session,
    current_user_id: int,
    track_session_id: int,
    image_file: BinaryIO,
    image_content_type: str | None,
    captured_position_seconds: int,
    captured_at: datetime,
) -> None:
    """현재 사용자의 트랙 세션에 속한 캡처를 Azure와 DB에 저장합니다."""
    # 세션 상태와 재생 모드는 프론트 흐름을 신뢰하고 검사하지 않습니다.
    track_session = db.scalar(
        select(TrackSession)
        .join(TrackSession.cube_ownership)
        .where(
            TrackSession.id == track_session_id,
            CubeOwnership.user_id == current_user_id,
        )
        .limit(1)
    )
    if track_session is None:
        raise ApiError(
            status_code=404,
            code="TRACK_SESSION_NOT_FOUND",
            message="트랙 재생 세션을 찾을 수 없습니다.",
        )

    normalized_content_type = normalize_image_content_type(image_content_type)
    if normalized_content_type is None:
        raise ApiError(
            status_code=400,
            code="INVALID_REQUEST",
            message="요청값이 올바르지 않습니다.",
        )

    try:
        image_url = upload_track_capture(
            file=image_file,
            content_type=normalized_content_type,
            user_id=current_user_id,
            track_session_id=track_session.id,
        )
    except Exception as exc:
        raise ApiError(
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="서버 내부 오류가 발생했습니다.",
        ) from exc

    capture = TrackCapture(
        track_session_id=track_session.id,
        track_capture_img_url=image_url,
        captured_position_seconds=captured_position_seconds,
        captured_at=captured_at,
        deleted_at=None,
    )
    try:
        db.add(capture)
        db.commit()
    except Exception:
        db.rollback()
        raise
