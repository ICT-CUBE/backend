"""홈 정보 조회 API 응답 스키마."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HomeSchema(BaseModel):
    """snake_case 필드로 생성하고 camelCase로 응답하기 위한 공통 설정."""

    model_config = ConfigDict(populate_by_name=True)


class HomeUserResponse(HomeSchema):
    id: int
    profile_character_img_url: str | None = Field(
        serialization_alias="profileCharacterImgUrl"
    )


class HomeCubeOwnershipResponse(HomeSchema):
    id: int
    avatar_nickname: str | None = Field(serialization_alias="avatarNickname")
    acquired_at: datetime = Field(serialization_alias="acquiredAt")


class HomeCubeResponse(HomeSchema):
    id: int
    artist_name: str = Field(serialization_alias="artistName")


class HomeLevelResponse(HomeSchema):
    id: int
    level: int
    level_name: str = Field(serialization_alias="levelName")
    level_xp: int = Field(serialization_alias="levelXp")


class HomeAffinityResponse(HomeSchema):
    id: int
    current_xp: int = Field(serialization_alias="currentXp")
    level: HomeLevelResponse


class HomeResponse(HomeSchema):
    user: HomeUserResponse
    cube_ownership: HomeCubeOwnershipResponse = Field(
        serialization_alias="cubeOwnership"
    )
    cube: HomeCubeResponse
    affinity: HomeAffinityResponse
