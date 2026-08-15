"""트랙 재생 세션 생성 API 요청·응답 스키마."""

from enum import StrEnum

from app.models.enums import TrackPlayMode
from app.schemas.base import ApiSchema


class TrackSessionCreateRequest(ApiSchema):
    play_mode: TrackPlayMode


class TrackSessionResponse(ApiSchema):
    id: int
    play_mode: TrackPlayMode


class TrackSessionCreateResponse(ApiSchema):
    track_session: TrackSessionResponse


class TrackSessionEndStatus(StrEnum):
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TrackSessionUpdateRequest(ApiSchema):
    # 숫자 범위는 검증하지 않고 세 필드가 전달됐는지만 확인합니다.
    status: TrackSessionEndStatus
    last_position_seconds: int
    viewed_seconds: int
