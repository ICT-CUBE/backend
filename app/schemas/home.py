"""홈 정보 조회 API 응답 schema."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HomeUserResponse(BaseModel):
    """홈 화면에 필요한 사용자 정보."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    profile_character_img_code: str | None = Field(
        serialization_alias="profileCharacterImgCode"
    )


class HomeCubeOwnershipResponse(BaseModel):
    """사용자가 마지막으로 접근한 활성 큐브 소유권."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    avatar_nickname: str | None = Field(serialization_alias="avatarNickname")
    acquired_at: datetime = Field(serialization_alias="acquiredAt")


class HomeCubeResponse(BaseModel):
    """홈 화면에 필요한 큐브 정보."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    artist_name: str = Field(serialization_alias="artistName")


class HomeLevelResponse(BaseModel):
    """현재 친밀도 레벨 정보."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    level: int
    level_name: str = Field(serialization_alias="levelName")
    level_xp: int = Field(serialization_alias="levelXp")


class HomeAffinityResponse(BaseModel):
    """현재 큐브 소유권의 친밀도 정보."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    current_xp: int = Field(serialization_alias="currentXp")
    level: HomeLevelResponse


class HomeResponse(BaseModel):
    """ 홈 정보 조회 정상 응답 전체 구조."""

    model_config = ConfigDict(populate_by_name=True)

    user: HomeUserResponse
    cube_ownership: HomeCubeOwnershipResponse = Field(
        serialization_alias="cubeOwnership"
    )
    cube: HomeCubeResponse
    affinity: HomeAffinityResponse
