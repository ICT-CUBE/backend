"""스테이지 재생 세션 API의 요청·응답 schema."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ViewMode


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
