"""홈 도메인 API 요청·응답 스키마."""

from datetime import datetime
from enum import StrEnum

from app.core.enums import NotificationType
from app.core.schemas import ApiSchema


class HomeNotificationFilter(StrEnum):
    ALL = "ALL"
    MISSION = "MISSION"
    EVENT = "EVENT"
    MARKET = "MARKET"


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


class HomeNotificationItemResponse(ApiSchema):
    id: int
    notification_type: NotificationType
    title: str
    content: str
    is_read: bool
    sent_at: datetime


class HomePaginationResponse(ApiSchema):
    page: int
    size: int
    has_next: bool


class HomeNotificationsResponse(ApiSchema):
    notifications: list[HomeNotificationItemResponse]
    pagination: HomePaginationResponse
