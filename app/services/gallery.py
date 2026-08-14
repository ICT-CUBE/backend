"""갤러리 조회 로직."""

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import func, literal, select, union_all
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ApiError
from app.models.album import Album, AlbumImage
from app.models.avatar import AvatarInteractionPicture, AvatarInteractionSession
from app.models.cube import CubeOwnership
from app.models.enums import AlbumImageType, OwnershipStatus
from app.models.stage import StageCapture, StageSession
from app.models.track import TrackCapture, TrackSession
from app.schemas.gallery import (
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

CURRENT_USER_ID = 1
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
        if value.tzinfo is None:
            return value.replace(tzinfo=KOREA_TIMEZONE)
        return value.astimezone(KOREA_TIMEZONE)
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=KOREA_TIMEZONE)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value[:19])
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=KOREA_TIMEZONE)
        return parsed.astimezone(KOREA_TIMEZONE)
    raise TypeError(f"Unsupported sort date value: {value!r}")


def _gallery_sort_key(row: Any) -> tuple[datetime, int]:
    if row["source_type"] == GallerySourceType.ALBUM_IMAGE.value:
        return datetime.min.replace(tzinfo=KOREA_TIMEZONE), -int(row["sort_id"])
    return _sort_datetime(row["sort_at"]), int(row["sort_id"])


def get_gallery(
    *,
    db: Session,
    category: GalleryCategory,
    page: int,
) -> GalleryResponse:
    """여러 이미지 출처를 하나의 갤러리 응답으로 합쳐 반환합니다."""
    statements = []

    if category in (GalleryCategory.ALL, GalleryCategory.CAPTURE):
        statements.extend(
            [
                _stage_capture_query(),
                _track_capture_query(),
                _interaction_capture_query(),
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
            galleryItems=[],
            pagination=GalleryPaginationResponse(
                page=page,
                size=GALLERY_PAGE_SIZE,
                hasNext=False,
            ),
        )

    combined = union_all(*statements).subquery()
    rows = db.execute(select(combined)).mappings().all()
    sorted_rows = sorted(
        rows,
        key=_gallery_sort_key,
        reverse=True,
    )

    start = page * GALLERY_PAGE_SIZE
    end = start + GALLERY_PAGE_SIZE
    page_rows = sorted_rows[start : end + 1]
    has_next = len(page_rows) > GALLERY_PAGE_SIZE

    return GalleryResponse(
        galleryItems=[
            GalleryItemResponse(
                id=row["id"],
                sourceType=GallerySourceType(row["source_type"]),
                category=GalleryCategory(row["category"]),
                imageUrl=row["image_url"],
                displayDate=_date_value(row["display_date"]),
            )
            for row in page_rows[:GALLERY_PAGE_SIZE]
        ],
        pagination=GalleryPaginationResponse(
            page=page,
            size=GALLERY_PAGE_SIZE,
            hasNext=has_next,
        ),
    )


def get_gallery_ar_experience(
    *,
    db: Session,
    source_type: GalleryArExperienceSourceType,
    gallery_item_id: int,
) -> GalleryArExperienceResponse:
    """캡처 항목의 원본 콘텐츠와 AR 재경험 시작 위치를 반환합니다."""
    if source_type == GalleryArExperienceSourceType.STAGE_CAPTURE:
        return _get_stage_ar_experience(
            db=db,
            gallery_item_id=gallery_item_id,
        )
    if source_type == GalleryArExperienceSourceType.TRACK_CAPTURE:
        return _get_track_ar_experience(
            db=db,
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
    source_type: GalleryDeletableSourceType,
    gallery_item_id: int,
) -> None:
    """사용자 캡처 갤러리 항목을 소프트 딜리트합니다."""
    if source_type == GalleryDeletableSourceType.STAGE_CAPTURE:
        capture = _get_deletable_stage_capture(db, gallery_item_id)
    elif source_type == GalleryDeletableSourceType.TRACK_CAPTURE:
        capture = _get_deletable_track_capture(db, gallery_item_id)
    elif source_type == GalleryDeletableSourceType.INTERACTION_CAPTURE:
        capture = _get_deletable_interaction_picture(db, gallery_item_id)
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


def _active_ownership_conditions() -> tuple[Any, ...]:
    return (
        CubeOwnership.user_id == CURRENT_USER_ID,
        CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
    )


def _get_deletable_stage_capture(
    db: Session,
    gallery_item_id: int,
) -> StageCapture | None:
    return db.scalar(
        select(StageCapture)
        .join(StageCapture.stage_session)
        .join(StageSession.cube_ownership)
        .where(
            StageCapture.id == gallery_item_id,
            *_active_ownership_conditions(),
            StageCapture.deleted_at.is_(None),
        )
        .limit(1)
        .with_for_update()
    )


def _get_deletable_track_capture(
    db: Session,
    gallery_item_id: int,
) -> TrackCapture | None:
    return db.scalar(
        select(TrackCapture)
        .join(TrackCapture.track_session)
        .join(TrackSession.cube_ownership)
        .where(
            TrackCapture.id == gallery_item_id,
            *_active_ownership_conditions(),
            TrackCapture.deleted_at.is_(None),
        )
        .limit(1)
        .with_for_update()
    )


def _get_deletable_interaction_picture(
    db: Session,
    gallery_item_id: int,
) -> AvatarInteractionPicture | None:
    return db.scalar(
        select(AvatarInteractionPicture)
        .join(AvatarInteractionPicture.interaction_session)
        .join(AvatarInteractionSession.cube_ownership)
        .where(
            AvatarInteractionPicture.id == gallery_item_id,
            *_active_ownership_conditions(),
            AvatarInteractionPicture.deleted_at.is_(None),
        )
        .limit(1)
        .with_for_update()
    )


def _get_stage_ar_experience(
    *,
    db: Session,
    gallery_item_id: int,
) -> GalleryArExperienceResponse:
    capture = db.scalar(
        select(StageCapture)
        .join(StageCapture.stage_session)
        .join(StageSession.cube_ownership)
        .where(
            StageCapture.id == gallery_item_id,
            *_active_ownership_conditions(),
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
        galleryItem=GalleryArExperienceItemResponse(
            contentType=GalleryContentType.STAGE,
            requiredMode=GalleryRequiredMode.AR,
            startPositionSeconds=capture.captured_position_seconds,
            stage=GalleryStageResponse(
                id=stage.id,
                title=stage.title,
                videoUrl=stage.video_url,
                durationSeconds=stage.duration_seconds,
            ),
        )
    )


def _get_track_ar_experience(
    *,
    db: Session,
    gallery_item_id: int,
) -> GalleryArExperienceResponse:
    capture = db.scalar(
        select(TrackCapture)
        .join(TrackCapture.track_session)
        .join(TrackSession.cube_ownership)
        .where(
            TrackCapture.id == gallery_item_id,
            *_active_ownership_conditions(),
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
        galleryItem=GalleryArExperienceItemResponse(
            contentType=GalleryContentType.TRACK,
            requiredMode=GalleryRequiredMode.SPECIAL,
            startPositionSeconds=capture.captured_position_seconds,
            track=GalleryTrackResponse(
                id=track.id,
                title=track.title,
                audioUrl=track.audio_url,
                durationSeconds=track.duration_seconds,
            ),
        )
    )


def _stage_capture_query():
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
            *_active_ownership_conditions(),
            StageCapture.deleted_at.is_(None),
        )
    )


def _track_capture_query():
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
            *_active_ownership_conditions(),
            TrackCapture.deleted_at.is_(None),
        )
    )


def _interaction_capture_query():
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
            *_active_ownership_conditions(),
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
