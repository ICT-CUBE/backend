"""홈 정보 조회 API 응답 스키마."""

from datetime import datetime

from app.schemas.base import ApiSchema


class HomeUserResponse(ApiSchema):
    id: int
    profile_character_img_url: str | None


class HomeCubeOwnershipResponse(ApiSchema):
    id: int
    avatar_nickname: str | None
    acquired_at: datetime


class HomeCubeResponse(ApiSchema):
    id: int
    artist_name: str


class HomeLevelResponse(ApiSchema):
    id: int
    level: int
    level_name: str
    level_xp: int


class HomeAffinityResponse(ApiSchema):
    id: int
    current_xp: int
    level: HomeLevelResponse


class HomeResponse(ApiSchema):
    user: HomeUserResponse
    cube_ownership: HomeCubeOwnershipResponse
    cube: HomeCubeResponse
    affinity: HomeAffinityResponse
