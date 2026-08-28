"""친밀도 상세 조회 서비스 로직."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ApiError
from app.models.cube import Affinity, CubeOwnership, Level
from app.models.enums import (
    MissionProgressStatus,
    MissionType,
    OwnershipStatus,
)
from app.models.reward import Mission, MissionProgress, RewardItem, UserReward
from app.schemas.affinity import (
    AffinityDailyActivityResponse,
    AffinityDetailResponse,
    AffinityLevelItemResponse,
    AffinityLevelRewardResponse,
    AffinityLevelStatus,
    AffinityProgressResponse,
    AffinityRewardResponse,
)

KOREA_TIMEZONE = timezone(timedelta(hours=9))


def get_affinity(*, db: Session, current_user_id: int) -> AffinityDetailResponse:
    """현재 사용자의 마지막 활성 소유권 기준 친밀도 현황을 조회합니다."""
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
            code="CUBE_OWNERSHIP_NOT_FOUND",
            message="큐브 소유권 정보를 찾을 수 없습니다.",
        )

    affinity = cube_ownership.affinity
    if affinity is None:
        raise ApiError(
            status_code=404,
            code="CUBE_AFFINITY_NOT_FOUND",
            message="큐브 친밀도 정보를 찾을 수 없습니다.",
        )

    current_level = affinity.level_info
    levels = list(db.scalars(select(Level).order_by(Level.level.asc())))
    next_level = next(
        (level for level in levels if level.level > current_level.level),
        None,
    )

    current_level_rewards = _get_acquired_level_rewards(
        db=db,
        cube_ownership_id=cube_ownership.id,
        level=current_level.level,
    )
    next_level_rewards = (
        _get_level_rewards(db=db, level=next_level.level)
        if next_level is not None
        else []
    )

    return AffinityDetailResponse(
        affinity=AffinityProgressResponse(
            id=affinity.id,
            current_xp=affinity.current_xp,
            progress_percent=_calculate_progress_percent(
                current_xp=affinity.current_xp,
                next_level=next_level,
            ),
            remaining_xp=_calculate_remaining_xp(
                current_xp=affinity.current_xp,
                next_level=next_level,
            ),
            current_level=_build_level_reward(current_level, current_level_rewards),
            next_level=(
                _build_level_reward(next_level, next_level_rewards)
                if next_level is not None
                else None
            ),
        ),
        daily_activities=_get_daily_activities(
            db=db,
            cube_ownership_id=cube_ownership.id,
        ),
        levels=[
            AffinityLevelItemResponse(
                id=level.id,
                level=level.level,
                level_name=level.level_name.value,
                required_xp=level.level_xp,
                status=_resolve_level_status(level.level, current_level.level),
            )
            for level in levels
        ],
    )


def _calculate_progress_percent(*, current_xp: int, next_level: Level | None) -> int:
    """다음 레벨 필요 XP 대비 진행률을 버림 계산합니다. 최고 레벨은 100입니다."""
    if next_level is None or next_level.level_xp <= 0:
        return 100
    return min(100, current_xp * 100 // next_level.level_xp)


def _calculate_remaining_xp(*, current_xp: int, next_level: Level | None) -> int:
    """다음 레벨까지 남은 XP를 계산합니다. 최고 레벨은 0입니다."""
    if next_level is None:
        return 0
    return max(0, next_level.level_xp - current_xp)


def _get_acquired_level_rewards(
    *,
    db: Session,
    cube_ownership_id: int,
    level: int,
) -> list[RewardItem]:
    """현재 소유권이 실제 획득한 보상 중 해당 레벨의 보상만 조회합니다."""
    return list(
        db.scalars(
            select(RewardItem)
            .select_from(UserReward)
            .join(UserReward.reward_item)
            .where(
                UserReward.cube_ownership_id == cube_ownership_id,
                RewardItem.reward_level == level,
                RewardItem.deleted_at.is_(None),
            )
            # 같은 보상을 여러 번 획득했어도 목록에는 한 번만 노출합니다.
            .distinct()
            .order_by(RewardItem.id.asc())
        )
    )


def _get_level_rewards(*, db: Session, level: int) -> list[RewardItem]:
    """해당 레벨에서 해금되는 보상을 획득 여부와 무관하게 조회합니다."""
    return list(
        db.scalars(
            select(RewardItem)
            .where(
                RewardItem.reward_level == level,
                RewardItem.deleted_at.is_(None),
            )
            .order_by(RewardItem.id.asc())
        )
    )


def _get_daily_activities(
    *,
    db: Session,
    cube_ownership_id: int,
) -> list[AffinityDailyActivityResponse]:
    """현재 시각에 적용되는 활성 DAILY 미션을 진행 정보와 함께 조회합니다."""
    now = datetime.now(KOREA_TIMEZONE).replace(tzinfo=None)
    missions = list(
        db.scalars(
            select(Mission)
            .where(
                Mission.mission_type == MissionType.DAILY,
                Mission.is_active.is_(True),
                Mission.deleted_at.is_(None),
                # 기간이 없는 미션은 항상 노출합니다.
                or_(Mission.start_at.is_(None), Mission.start_at <= now),
                or_(Mission.end_at.is_(None), Mission.end_at >= now),
            )
            .options(joinedload(Mission.reward_item))
            .order_by(Mission.id.asc())
        )
    )
    if not missions:
        return []

    progresses = db.scalars(
        select(MissionProgress).where(
            MissionProgress.cube_ownership_id == cube_ownership_id,
            MissionProgress.mission_id.in_([mission.id for mission in missions]),
        )
    )
    progress_by_mission_id = {
        progress.mission_id: progress for progress in progresses
    }

    return [
        _build_daily_activity(mission, progress_by_mission_id.get(mission.id))
        for mission in missions
    ]


def _build_daily_activity(
    mission: Mission,
    progress: MissionProgress | None,
) -> AffinityDailyActivityResponse:
    """진행 정보가 없는 미션은 진행 수 0, IN_PROGRESS, 미수령으로 취급합니다."""
    progress_status = (
        progress.status if progress is not None else MissionProgressStatus.IN_PROGRESS
    )

    return AffinityDailyActivityResponse(
        id=mission.id,
        title=mission.title,
        description=mission.description,
        target_action=mission.target_action.value,
        current_count=progress.current_count if progress is not None else 0,
        target_count=mission.target_count,
        status=progress_status.value,
        reward_claimed=progress.reward_claimed if progress is not None else False,
        reward=_build_reward(mission.reward_item),
    )


def _build_level_reward(
    level: Level,
    reward_items: list[RewardItem],
) -> AffinityLevelRewardResponse:
    return AffinityLevelRewardResponse(
        id=level.id,
        level=level.level,
        level_name=level.level_name.value,
        required_xp=level.level_xp,
        rewards=[_build_reward(reward_item) for reward_item in reward_items],
    )


def _build_reward(reward_item: RewardItem) -> AffinityRewardResponse:
    return AffinityRewardResponse(
        id=reward_item.id,
        name=reward_item.name,
        reward_type=reward_item.reward_type.value,
        description=reward_item.description,
        reward_count=reward_item.reward_count,
        reward_level=reward_item.reward_level,
    )


def _resolve_level_status(level: int, current_level: int) -> AffinityLevelStatus:
    if level < current_level:
        return AffinityLevelStatus.COMPLETED
    if level == current_level:
        return AffinityLevelStatus.CURRENT
    return AffinityLevelStatus.LOCKED
