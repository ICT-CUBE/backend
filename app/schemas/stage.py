"""스테이지 재생 세션 API 요청·응답 스키마."""

from datetime import datetime
from enum import StrEnum

from app.models.enums import StageViewMode
from app.schemas.base import ApiSchema


class StageListItemResponse(ApiSchema):
    id: int
    title: str
    description: str | None
    thumbnail_url: str | None
    recorded_at: datetime
    is_title_video: bool


class StageListResponse(ApiSchema):
    stages: list[StageListItemResponse]


class StageVideoResponse(ApiSchema):
    id: int
    video_url: str
    duration_seconds: int


class StageVideoDetailResponse(ApiSchema):
    stage: StageVideoResponse


class StageSessionEndStatus(StrEnum):
    """세션 저장 API에서 허용하는 종료 상태."""

    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class StageSessionCreateRequest(ApiSchema):
    view_mode: StageViewMode


class StageSessionResponse(ApiSchema):
    id: int
    view_mode: StageViewMode


class StageSessionCreateResponse(ApiSchema):
    stage_session: StageSessionResponse


class StageSessionUpdateRequest(ApiSchema):
    status: StageSessionEndStatus
    last_position_seconds: int
    viewed_seconds: int
