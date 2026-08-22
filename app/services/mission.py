"""미션 목록 조회 서비스 로직."""

from datetime import datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ApiError
from app.models.cube import Affinity, CubeOwnership
from app.models.enums import (
    MissionProgressStatus,
    MissionType,
    OwnershipStatus,
    RewardItemType,
)
from app.models.reward import Mission, MissionProgress, RewardItem, UserReward
from app.schemas.mission import (
    MissionAffinityResponse,
    MissionItemResponse,
    MissionLevelResponse,
    MissionListResponse,
    MissionRewardResponse,
)

KST = timezone(timedelta(hours=9))


def get_missions(*, db: Session, current_user_id: int) -> MissionListResponse:
    """현재 사용자의 마지막 접근 큐브 소유권 기준 미션 목록을 조회합니다."""
    cube_ownership = db.scalar(
        select(CubeOwnership)
        .where(
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .options(
            joinedload(CubeOwnership.affinity).joinedload(Affinity.level_info),
        )
        .limit(1)
    )
    if cube_ownership is None:
        raise ApiError(
            status_code=404,
            code="ACTIVE_CUBE_OWNERSHIP_NOT_FOUND",
            message="활성화된 큐브 소유권을 찾을 수 없습니다.",
        )

    missions = list(
        db.scalars(
            select(Mission)
            .where(
                Mission.is_active.is_(True),
                Mission.deleted_at.is_(None),
            )
            .options(joinedload(Mission.reward_item))
            .order_by(Mission.id.asc())
        )
    )
    mission_ids = [mission.id for mission in missions]
    progress_by_mission_id = _get_progress_by_mission_id(
        db=db,
        cube_ownership_id=cube_ownership.id,
        mission_ids=mission_ids,
    )
    today_earned_xp = _get_today_earned_xp(
        db=db,
        cube_ownership_id=cube_ownership.id,
    )

    affinity = cube_ownership.affinity
    level = affinity.level_info
    daily_missions = [
        _build_mission_item(mission, progress_by_mission_id.get(mission.id))
        for mission in missions
        if mission.mission_type == MissionType.DAILY
    ]
    event_missions = [
        _build_mission_item(mission, progress_by_mission_id.get(mission.id))
        for mission in missions
        if mission.mission_type == MissionType.EVENT
    ]

    return MissionListResponse(
        affinity=MissionAffinityResponse(
            current_xp=affinity.current_xp,
            today_earned_xp=today_earned_xp,
            level=MissionLevelResponse(
                level=level.level,
                level_name=level.level_name.value,
                level_xp=level.level_xp,
            ),
        ),
        daily_missions=daily_missions,
        event_missions=event_missions,
    )


def _get_progress_by_mission_id(
    *,
    db: Session,
    cube_ownership_id: int,
    mission_ids: list[int],
) -> dict[int, MissionProgress]:
    if not mission_ids:
        return {}

    progresses = db.scalars(
        select(MissionProgress).where(
            MissionProgress.cube_ownership_id == cube_ownership_id,
            MissionProgress.mission_id.in_(mission_ids),
        )
    )
    return {progress.mission_id: progress for progress in progresses}


def _get_today_earned_xp(*, db: Session, cube_ownership_id: int) -> int:
    today_start = datetime.combine(
        datetime.now(KST).date(),
        time.min,
    )
    tomorrow_start = today_start + timedelta(days=1)

    today_earned_xp = db.scalar(
        select(func.coalesce(func.sum(RewardItem.reward_count), 0))
        .select_from(UserReward)
        .join(UserReward.reward_item)
        .where(
            UserReward.cube_ownership_id == cube_ownership_id,
            UserReward.acquired_at >= today_start,
            UserReward.acquired_at < tomorrow_start,
            RewardItem.reward_type == RewardItemType.AFFINITY_POINT,
        )
    )
    return int(today_earned_xp or 0)


def _build_mission_item(
    mission: Mission,
    progress: MissionProgress | None,
) -> MissionItemResponse:
    current_count = progress.current_count if progress is not None else 0
    progress_status = (
        progress.status if progress is not None else MissionProgressStatus.IN_PROGRESS
    )
    reward_claimed = progress.reward_claimed if progress is not None else False
    completed_at = progress.completed_at if progress is not None else None
    claimed_at = progress.claimed_at if progress is not None else None
    reward_item = mission.reward_item

    return MissionItemResponse(
        id=mission.id,
        title=mission.title,
        description=mission.description,
        mission_type=mission.mission_type.value,
        target_count=mission.target_count,
        current_count=current_count,
        status=progress_status.value,
        reward_claimed=reward_claimed,
        completed_at=completed_at,
        claimed_at=claimed_at,
        reward=MissionRewardResponse(
            reward_type=reward_item.reward_type.value,
            reward_count=reward_item.reward_count,
        ),
        start_at=mission.start_at,
        end_at=mission.end_at,
    )
