"""갤러리 조회 API 응답 스키마."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel


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


class GalleryItemResponse(BaseModel):
    id: int
    sourceType: GallerySourceType
    category: GalleryCategory
    imageUrl: str
    displayDate: date


class GalleryPaginationResponse(BaseModel):
    page: int
    size: int
    hasNext: bool


class GalleryResponse(BaseModel):
    galleryItems: list[GalleryItemResponse]
    pagination: GalleryPaginationResponse


class GalleryStageResponse(BaseModel):
    id: int
    title: str
    videoUrl: str
    durationSeconds: int


class GalleryTrackResponse(BaseModel):
    id: int
    title: str
    audioUrl: str
    durationSeconds: int


class GalleryArExperienceItemResponse(BaseModel):
    contentType: GalleryContentType
    requiredMode: GalleryRequiredMode
    startPositionSeconds: int | None
    stage: GalleryStageResponse | None = None
    track: GalleryTrackResponse | None = None


class GalleryArExperienceResponse(BaseModel):
    galleryItem: GalleryArExperienceItemResponse
