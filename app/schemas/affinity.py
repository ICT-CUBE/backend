"""친밀도 도메인 API 응답 스키마."""

from enum import StrEnum

from app.schemas.base import ApiSchema


class AffinityLevelStatus(StrEnum):
    """전체 레벨 목록에서 현재 레벨을 기준으로 계산하는 진행 상태."""

    COMPLETED = "COMPLETED"
    CURRENT = "CURRENT"
    LOCKED = "LOCKED"


class AffinityRewardResponse(ApiSchema):
    id: int
    name: str
    reward_type: str
    description: str | None
    reward_count: int | None
    reward_level: int | None


class AffinityLevelRewardResponse(ApiSchema):
    id: int
    level: int
    level_name: str
    required_xp: int
    rewards: list[AffinityRewardResponse]


class AffinityProgressResponse(ApiSchema):
    id: int
    current_xp: int
    progress_percent: int
    remaining_xp: int
    current_level: AffinityLevelRewardResponse
    next_level: AffinityLevelRewardResponse | None


class AffinityDailyActivityResponse(ApiSchema):
    id: int
    title: str
    description: str | None
    target_action: str
    current_count: int
    target_count: int
    status: str
    reward_claimed: bool
    reward: AffinityRewardResponse


class AffinityLevelItemResponse(ApiSchema):
    id: int
    level: int
    level_name: str
    required_xp: int
    status: AffinityLevelStatus


class AffinityDetailResponse(ApiSchema):
    affinity: AffinityProgressResponse
    daily_activities: list[AffinityDailyActivityResponse]
    levels: list[AffinityLevelItemResponse]
