"""앨범 도메인 트랙 재생 세션 로직."""

from datetime import datetime, timedelta, timezone
from typing import BinaryIO

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.album.models import Album, Track, TrackCapture, TrackSession
from app.album.schemas import (
    AlbumInfoResponse,
    AlbumResponse,
    AlbumTrackDetailGetResponse,
    AlbumTrackDetailResponse,
    AlbumTrackResponse,
    TrackSessionCreateResponse,
    TrackSessionEndStatus,
    TrackSessionResponse,
)
from app.core.blob_storage import normalize_image_content_type, upload_track_capture
from app.core.enums import OwnershipStatus, TrackPlayMode, TrackSessionStatus
from app.core.exceptions import ApiError
from app.cube.models import CubeOwnership

KOREA_TIMEZONE = timezone(timedelta(hours=9))


def get_album(*, db: Session, current_user_id: int) -> AlbumResponse:
    """현재 사용자의 마지막 활성 소유권을 확인한 뒤 대표 앨범을 조회합니다."""
    ownership = db.scalar(
        select(CubeOwnership.id)
        .where(
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .limit(1)
    )
    if ownership is None:
        raise ApiError(
            status_code=404,
            code="CUBE_OWNERSHIP_NOT_FOUND",
            message="큐브 소유권 정보를 찾을 수 없습니다.",
        )

    album = db.scalar(
        select(Album)
        .options(selectinload(Album.tracks))
        .order_by(Album.id.asc())
        .limit(1)
    )
    if album is None:
        raise ApiError(
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="서버 내부 오류가 발생했습니다.",
        )

    tracks = sorted(album.tracks, key=lambda track: track.track_number)
    return AlbumResponse(
        album=AlbumInfoResponse(
            id=album.id,
            title=album.title,
            artist_name=album.artist_name,
            track_count=album.track_count,
            track_total_seconds=album.track_total_second,
            cover_image_url=album.cover_image_url,
            release_date=album.release_date,
            tracks=[
                AlbumTrackResponse(
                    id=track.id,
                    track_number=track.track_number,
                    title=track.title,
                    artist_name=track.artist_name,
                    duration_seconds=track.duration_seconds,
                    is_title_track=track.is_title_track,
                )
                for track in tracks
            ],
        )
    )


def get_album_track(
    *,
    db: Session,
    current_user_id: int,
    track_id: int,
) -> AlbumTrackDetailGetResponse:
    """현재 사용자의 마지막 활성 소유권을 확인한 뒤 앨범 트랙을 조회합니다."""
    ownership = db.scalar(
        select(CubeOwnership.id)
        .where(
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .limit(1)
    )
    if ownership is None:
        raise ApiError(
            status_code=404,
            code="CUBE_OWNERSHIP_NOT_FOUND",
            message="큐브 소유권 정보를 찾을 수 없습니다.",
        )

    track = db.scalar(select(Track).where(Track.id == track_id).limit(1))
    if track is None:
        raise ApiError(
            status_code=404,
            code="TRACK_NOT_FOUND",
            message="앨범 트랙을 찾을 수 없습니다.",
        )

    return AlbumTrackDetailGetResponse(
        track=AlbumTrackDetailResponse(
            id=track.id,
            audio_url=track.audio_url,
            duration_seconds=track.duration_seconds,
            lyrics=track.lyrics,
        )
    )


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
