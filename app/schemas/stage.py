"""스테이지 재생 세션 API 요청·응답 스키마."""

from enum import StrEnum

from pydantic import BaseModel

from app.models.enums import StageViewMode


class StageSessionEndStatus(StrEnum):
    """세션 저장 API에서 허용하는 종료 상태."""

    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class StageSessionCreateRequest(BaseModel):
    # API 명세의 JSON 키를 그대로 필드명으로 사용해 별도 alias 변환을 없앴습니다.
    viewMode: StageViewMode


class StageSessionResponse(BaseModel):
    id: int
    viewMode: StageViewMode


class StageSessionCreateResponse(BaseModel):
    stageSession: StageSessionResponse


class StageSessionUpdateRequest(BaseModel):
    status: StageSessionEndStatus
    lastPositionSeconds: int
    viewedSeconds: int
