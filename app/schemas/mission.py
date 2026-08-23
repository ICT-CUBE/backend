"""미션 도메인 API 응답 스키마."""

from datetime import datetime

from app.schemas.base import ApiSchema


class MissionLevelResponse(ApiSchema):
    level: int
    level_name: str
    level_xp: int


class MissionAffinityResponse(ApiSchema):
    current_xp: int
    today_earned_xp: int
    level: MissionLevelResponse


class MissionRewardResponse(ApiSchema):
    reward_type: str
    reward_count: int | None


class MissionItemResponse(ApiSchema):
    id: int
    title: str
    description: str | None
    mission_type: str
    target_count: int
    current_count: int
    status: str
    reward_claimed: bool
    completed_at: datetime | None
    claimed_at: datetime | None
    reward: MissionRewardResponse
    start_at: datetime | None
    end_at: datetime | None


class MissionListResponse(ApiSchema):
    affinity: MissionAffinityResponse
    daily_missions: list[MissionItemResponse]
    event_missions: list[MissionItemResponse]
