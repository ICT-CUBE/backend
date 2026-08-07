"""스테이지 재생 세션 API의 요청·응답 schema."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PlaybackStatus, ViewMode


class StageSessionCreateRequest(BaseModel):
    """스테이지 재생 모드."""

    model_config = ConfigDict(populate_by_name=True)

    view_mode: ViewMode = Field(alias="viewMode")


class StageSessionResponse(BaseModel):
    """생성된 스테이지 재생 세션 정보."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    view_mode: ViewMode = Field(serialization_alias="viewMode")


class StageSessionCreateResponse(BaseModel):
    """스테이지 재생 세션 생성 정상 응답."""

    model_config = ConfigDict(populate_by_name=True)

    stage_session: StageSessionResponse = Field(serialization_alias="stageSession")


class StageSessionUpdateRequest(BaseModel):
    """재생이 끝난 스테이지 세션에 저장할 최종 상태와 시청 시간."""

    model_config = ConfigDict(populate_by_name=True)

    # PLAYING은 세션 종료 상태가 아니므로 저장 API에서는 허용하지 않습니다.
    # 값 자체는 DB에서 사용하는 PlaybackStatus Enum을 그대로 사용합니다.
    status: Literal[
        PlaybackStatus.COMPLETED,
        PlaybackStatus.CANCELLED,
    ]
    last_position_seconds: int = Field(alias="lastPositionSeconds", ge=0)
    viewed_seconds: int = Field(alias="viewedSeconds", ge=0)
