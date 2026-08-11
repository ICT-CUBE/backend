"""트랙 재생 세션 생성 API 요청·응답 스키마."""

from enum import StrEnum

from pydantic import BaseModel

from app.models.enums import TrackPlayMode


class TrackSessionCreateRequest(BaseModel):
    playMode: TrackPlayMode


class TrackSessionResponse(BaseModel):
    id: int
    playMode: TrackPlayMode


class TrackSessionCreateResponse(BaseModel):
    trackSession: TrackSessionResponse


class TrackSessionEndStatus(StrEnum):
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TrackSessionUpdateRequest(BaseModel):
    # 숫자 범위는 검증하지 않고 세 필드가 전달됐는지만 확인합니다.
    status: TrackSessionEndStatus
    lastPositionSeconds: int
    viewedSeconds: int
