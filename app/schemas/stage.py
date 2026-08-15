"""스테이지 재생 세션 API 요청·응답 스키마."""

from enum import StrEnum

from app.models.enums import StageViewMode
from app.schemas.base import ApiSchema


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
