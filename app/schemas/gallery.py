"""갤러리 조회 API 응답 스키마."""

from datetime import date
from enum import StrEnum

from app.schemas.base import ApiSchema


class GalleryCategory(StrEnum):
    ALL = "ALL"
    CAPTURE = "CAPTURE"
    ALBUM = "ALBUM"
    CONCERT_STILLCUT = "CONCERT_STILLCUT"


class GallerySourceType(StrEnum):
    STAGE_CAPTURE = "STAGE_CAPTURE"
    TRACK_CAPTURE = "TRACK_CAPTURE"
    INTERACTION_CAPTURE = "INTERACTION_CAPTURE"
    ALBUM_IMAGE = "ALBUM_IMAGE"


class GalleryArExperienceSourceType(StrEnum):
    STAGE_CAPTURE = "STAGE_CAPTURE"
    TRACK_CAPTURE = "TRACK_CAPTURE"


class GalleryDeletableSourceType(StrEnum):
    STAGE_CAPTURE = "STAGE_CAPTURE"
    TRACK_CAPTURE = "TRACK_CAPTURE"
    INTERACTION_CAPTURE = "INTERACTION_CAPTURE"


class GalleryContentType(StrEnum):
    STAGE = "STAGE"
    TRACK = "TRACK"


class GalleryRequiredMode(StrEnum):
    AR = "AR"
    SPECIAL = "SPECIAL"


class GalleryItemResponse(ApiSchema):
    id: int
    source_type: GallerySourceType
    category: GalleryCategory
    image_url: str
    display_date: date


class GalleryPaginationResponse(ApiSchema):
    page: int
    size: int
    has_next: bool


class GalleryResponse(ApiSchema):
    gallery_items: list[GalleryItemResponse]
    pagination: GalleryPaginationResponse


class GalleryStageResponse(ApiSchema):
    id: int
    title: str
    video_url: str
    duration_seconds: int


class GalleryTrackResponse(ApiSchema):
    id: int
    title: str
    audio_url: str
    duration_seconds: int


class GalleryArExperienceItemResponse(ApiSchema):
    content_type: GalleryContentType
    required_mode: GalleryRequiredMode
    start_position_seconds: int | None
    stage: GalleryStageResponse | None = None
    track: GalleryTrackResponse | None = None


class GalleryArExperienceResponse(ApiSchema):
    gallery_item: GalleryArExperienceItemResponse
