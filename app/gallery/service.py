"""갤러리 조회 로직."""

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import func, literal, select, union_all
from sqlalchemy.orm import Session, joinedload

from app.album.models import Album, AlbumImage, TrackCapture, TrackSession
from app.avatar.models import AvatarInteractionPicture, AvatarInteractionSession
from app.core.enums import AlbumImageType, OwnershipStatus
from app.core.exceptions import ApiError
from app.cube.models import CubeOwnership
from app.gallery.schemas import (
    GalleryArExperienceItemResponse,
    GalleryArExperienceResponse,
    GalleryArExperienceSourceType,
    GalleryCategory,
    GalleryContentType,
    GalleryDeletableSourceType,
    GalleryItemResponse,
    GalleryPaginationResponse,
    GalleryRequiredMode,
    GalleryResponse,
    GallerySourceType,
    GalleryStageResponse,
    GalleryTrackResponse,
)
from app.stage.models import StageCapture, StageSession

GALLERY_PAGE_SIZE = 20
KOREA_TIMEZONE = timezone(timedelta(hours=9))


def _date_value(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise TypeError(f"Unsupported display date value: {value!r}")


def _sort_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    if isinstance(value, str):
        return datetime.fromisoformat(value[:19])
    raise TypeError(f"Unsupported sort date value: {value!r}")


def _gallery_sort_key(row: Any) -> tuple[datetime, int]:
    if row["source_type"] == GallerySourceType.ALBUM_IMAGE.value:
        return datetime.min, -int(row["sort_id"])  # noqa: DTZ901
    return _sort_datetime(row["sort_at"]), int(row["sort_id"])


def get_gallery(
    *,
    db: Session,
    current_user_id: int,
    category: GalleryCategory,
    page: int,
    size: int,
) -> GalleryResponse:
    """여러 이미지 출처를 하나의 갤러리 응답으로 합쳐 반환합니다."""
    statements = []

    if category in (GalleryCategory.ALL, GalleryCategory.CAPTURE):
        statements.extend(
            [
                _stage_capture_query(current_user_id),
                _track_capture_query(current_user_id),
                _interaction_capture_query(current_user_id),
            ]
        )

    if category in (GalleryCategory.ALL, GalleryCategory.ALBUM):
        statements.append(
            _album_image_query(
                image_type=AlbumImageType.ALBUM_IMAGE,
                category=GalleryCategory.ALBUM,
            )
        )

    if category in (GalleryCategory.ALL, GalleryCategory.CONCERT_STILLCUT):
        statements.append(
            _album_image_query(
                image_type=AlbumImageType.CONCERT_STILLCUT,
                category=GalleryCategory.CONCERT_STILLCUT,
            )
        )

    if not statements:
        return GalleryResponse(
            gallery_items=[],
            pagination=GalleryPaginationResponse(
                page=page,
                size=size,
                has_next=False,
            ),
        )

    combined = union_all(*statements).subquery()
    rows = db.execute(select(combined)).mappings().all()
    sorted_rows = sorted(
        rows,
        key=_gallery_sort_key,
        reverse=True,
    )

    start = page * size
    end = start + size
    page_rows = sorted_rows[start : end + 1]
    has_next = len(page_rows) > size

    return GalleryResponse(
        gallery_items=[
            GalleryItemResponse(
                id=row["id"],
                source_type=GallerySourceType(row["source_type"]),
                category=GalleryCategory(row["category"]),
                image_url=row["image_url"],
                display_date=_date_value(row["display_date"]),
            )
            for row in page_rows[:size]
        ],
        pagination=GalleryPaginationResponse(
            page=page,
            size=size,
            has_next=has_next,
        ),
    )


def get_gallery_ar_experience(
    *,
    db: Session,
    current_user_id: int,
    source_type: GalleryArExperienceSourceType,
    gallery_item_id: int,
) -> GalleryArExperienceResponse:
    """캡처 항목의 원본 콘텐츠와 AR 재경험 시작 위치를 반환합니다."""
    if source_type == GalleryArExperienceSourceType.STAGE_CAPTURE:
        return _get_stage_ar_experience(
            db=db,
            current_user_id=current_user_id,
            gallery_item_id=gallery_item_id,
        )
    if source_type == GalleryArExperienceSourceType.TRACK_CAPTURE:
        return _get_track_ar_experience(
            db=db,
            current_user_id=current_user_id,
            gallery_item_id=gallery_item_id,
        )

    raise ApiError(
        status_code=400,
        code="INVALID_REQUEST",
        message="요청값이 올바르지 않습니다.",
    )


def delete_gallery_item(
    *,
    db: Session,
    current_user_id: int,
    source_type: GalleryDeletableSourceType,
    gallery_item_id: int,
) -> None:
    """사용자 캡처 갤러리 항목을 소프트 딜리트합니다."""
    if source_type == GalleryDeletableSourceType.STAGE_CAPTURE:
        capture = _get_deletable_stage_capture(db, current_user_id, gallery_item_id)
    elif source_type == GalleryDeletableSourceType.TRACK_CAPTURE:
        capture = _get_deletable_track_capture(db, current_user_id, gallery_item_id)
    elif source_type == GalleryDeletableSourceType.INTERACTION_CAPTURE:
        capture = _get_deletable_interaction_picture(
            db, current_user_id, gallery_item_id
        )
    else:
        raise ApiError(
            status_code=400,
            code="INVALID_REQUEST",
            message="요청값이 올바르지 않습니다.",
        )

    if capture is None:
        raise ApiError(
            status_code=404,
            code="GALLERY_ITEM_NOT_FOUND",
            message="삭제할 갤러리 항목을 찾을 수 없습니다.",
        )

    capture.deleted_at = datetime.now(KOREA_TIMEZONE).replace(tzinfo=None)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _active_ownership_conditions(current_user_id: int) -> tuple[Any, ...]:
    return (
        CubeOwnership.user_id == current_user_id,
        CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
    )


def _get_deletable_stage_capture(
    db: Session,
    current_user_id: int,
    gallery_item_id: int,
) -> StageCapture | None:
    return db.scalar(
        select(StageCapture)
        .join(StageCapture.stage_session)
        .join(StageSession.cube_ownership)
        .where(
            StageCapture.id == gallery_item_id,
            *_active_ownership_conditions(current_user_id),
            StageCapture.deleted_at.is_(None),
        )
        .limit(1)
        .with_for_update()
    )


def _get_deletable_track_capture(
    db: Session,
    current_user_id: int,
    gallery_item_id: int,
) -> TrackCapture | None:
    return db.scalar(
        select(TrackCapture)
        .join(TrackCapture.track_session)
        .join(TrackSession.cube_ownership)
        .where(
            TrackCapture.id == gallery_item_id,
            *_active_ownership_conditions(current_user_id),
            TrackCapture.deleted_at.is_(None),
        )
        .limit(1)
        .with_for_update()
    )


def _get_deletable_interaction_picture(
    db: Session,
    current_user_id: int,
    gallery_item_id: int,
) -> AvatarInteractionPicture | None:
    return db.scalar(
        select(AvatarInteractionPicture)
        .join(AvatarInteractionPicture.interaction_session)
        .join(AvatarInteractionSession.cube_ownership)
        .where(
            AvatarInteractionPicture.id == gallery_item_id,
            *_active_ownership_conditions(current_user_id),
            AvatarInteractionPicture.deleted_at.is_(None),
        )
        .limit(1)
        .with_for_update()
    )


def _get_stage_ar_experience(
    *,
    db: Session,
    current_user_id: int,
    gallery_item_id: int,
) -> GalleryArExperienceResponse:
    capture = db.scalar(
        select(StageCapture)
        .join(StageCapture.stage_session)
        .join(StageSession.cube_ownership)
        .where(
            StageCapture.id == gallery_item_id,
            *_active_ownership_conditions(current_user_id),
            StageCapture.deleted_at.is_(None),
        )
        .options(joinedload(StageCapture.stage_session).joinedload(StageSession.stage))
        .limit(1)
    )
    if capture is None:
        raise ApiError(
            status_code=404,
            code="GALLERY_ITEM_NOT_FOUND",
            message="갤러리 항목을 찾을 수 없습니다.",
        )

    stage = capture.stage_session.stage
    return GalleryArExperienceResponse(
        gallery_item=GalleryArExperienceItemResponse(
            content_type=GalleryContentType.STAGE,
            required_mode=GalleryRequiredMode.AR,
            start_position_seconds=capture.captured_position_seconds,
            stage=GalleryStageResponse(
                id=stage.id,
                title=stage.title,
                video_url=stage.video_url,
                duration_seconds=stage.duration_seconds,
            ),
        )
    )


def _get_track_ar_experience(
    *,
    db: Session,
    current_user_id: int,
    gallery_item_id: int,
) -> GalleryArExperienceResponse:
    capture = db.scalar(
        select(TrackCapture)
        .join(TrackCapture.track_session)
        .join(TrackSession.cube_ownership)
        .where(
            TrackCapture.id == gallery_item_id,
            *_active_ownership_conditions(current_user_id),
            TrackCapture.deleted_at.is_(None),
        )
        .options(joinedload(TrackCapture.track_session).joinedload(TrackSession.track))
        .limit(1)
    )
    if capture is None:
        raise ApiError(
            status_code=404,
            code="GALLERY_ITEM_NOT_FOUND",
            message="갤러리 항목을 찾을 수 없습니다.",
        )

    track = capture.track_session.track
    return GalleryArExperienceResponse(
        gallery_item=GalleryArExperienceItemResponse(
            content_type=GalleryContentType.TRACK,
            required_mode=GalleryRequiredMode.SPECIAL,
            start_position_seconds=capture.captured_position_seconds,
            track=GalleryTrackResponse(
                id=track.id,
                title=track.title,
                audio_url=track.audio_url,
                duration_seconds=track.duration_seconds,
            ),
        )
    )


def _stage_capture_query(current_user_id: int):
    return (
        select(
            StageCapture.id.label("id"),
            literal(GallerySourceType.STAGE_CAPTURE.value).label("source_type"),
            literal(GalleryCategory.CAPTURE.value).label("category"),
            StageCapture.stage_capture_img_url.label("image_url"),
            func.date(StageCapture.captured_at).label("display_date"),
            StageCapture.captured_at.label("sort_at"),
            StageCapture.id.label("sort_id"),
        )
        .join(StageSession, StageCapture.stage_session_id == StageSession.id)
        .join(CubeOwnership, StageSession.cube_ownership_id == CubeOwnership.id)
        .where(
            *_active_ownership_conditions(current_user_id),
            StageCapture.deleted_at.is_(None),
        )
    )


def _track_capture_query(current_user_id: int):
    return (
        select(
            TrackCapture.id.label("id"),
            literal(GallerySourceType.TRACK_CAPTURE.value).label("source_type"),
            literal(GalleryCategory.CAPTURE.value).label("category"),
            TrackCapture.track_capture_img_url.label("image_url"),
            func.date(TrackCapture.captured_at).label("display_date"),
            TrackCapture.captured_at.label("sort_at"),
            TrackCapture.id.label("sort_id"),
        )
        .join(TrackSession, TrackCapture.track_session_id == TrackSession.id)
        .join(CubeOwnership, TrackSession.cube_ownership_id == CubeOwnership.id)
        .where(
            *_active_ownership_conditions(current_user_id),
            TrackCapture.deleted_at.is_(None),
        )
    )


def _interaction_capture_query(current_user_id: int):
    return (
        select(
            AvatarInteractionPicture.id.label("id"),
            literal(GallerySourceType.INTERACTION_CAPTURE.value).label("source_type"),
            literal(GalleryCategory.CAPTURE.value).label("category"),
            AvatarInteractionPicture.picture_img_url.label("image_url"),
            func.date(AvatarInteractionPicture.pictured_at).label("display_date"),
            AvatarInteractionPicture.pictured_at.label("sort_at"),
            AvatarInteractionPicture.id.label("sort_id"),
        )
        .join(
            AvatarInteractionSession,
            AvatarInteractionPicture.interaction_session_id
            == AvatarInteractionSession.id,
        )
        .join(
            CubeOwnership,
            AvatarInteractionSession.cube_ownership_id == CubeOwnership.id,
        )
        .where(
            *_active_ownership_conditions(current_user_id),
            AvatarInteractionPicture.picture_img_url.is_not(None),
            AvatarInteractionPicture.deleted_at.is_(None),
        )
    )


def _album_image_query(
    *,
    image_type: AlbumImageType,
    category: GalleryCategory,
):
    return (
        select(
            AlbumImage.id.label("id"),
            literal(GallerySourceType.ALBUM_IMAGE.value).label("source_type"),
            literal(category.value).label("category"),
            AlbumImage.album_contents_img_url.label("image_url"),
            Album.release_date.label("display_date"),
            Album.release_date.label("sort_at"),
            AlbumImage.id.label("sort_id"),
        )
        .join(Album, AlbumImage.album_id == Album.id)
        .where(AlbumImage.image_type == image_type)
    )
