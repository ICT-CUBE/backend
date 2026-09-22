"""미션 목록·데일리 미션 상세 조회와 미션 보상 수령 서비스 로직."""

from datetime import datetime, time, timedelta, timezone
from typing import NoReturn

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.affinity.models import Affinity, Level
from app.core.enums import (
    MissionProgressStatus,
    MissionType,
    OwnershipStatus,
    RewardItemType,
)
from app.core.exceptions import ApiError
from app.cube.models import CubeOwnership
from app.mission.models import Mission, MissionProgress, RewardItem, UserReward
from app.mission.schemas import (
    MissionAffinityResponse,
    MissionDailyDetailItemResponse,
    MissionDailyDetailResponse,
    MissionDailyRewardItemResponse,
    MissionItemResponse,
    MissionLevelResponse,
    MissionLevelUpResponse,
    MissionListResponse,
    MissionRewardClaimResponse,
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
            code="CUBE_OWNERSHIP_NOT_FOUND",
            message="큐브 소유권 정보를 찾을 수 없습니다.",
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


def get_daily_mission(
    *,
    db: Session,
    current_user_id: int,
    mission_id: int,
) -> MissionDailyDetailResponse:
    """현재 사용자의 마지막 접근 큐브 소유권 기준으로 데일리 미션 상세를 조회합니다."""
    cube_ownership = db.scalar(
        select(CubeOwnership)
        .where(
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .limit(1)
    )
    if cube_ownership is None:
        raise ApiError(
            status_code=404,
            code="CUBE_OWNERSHIP_NOT_FOUND",
            message="큐브 소유권 정보를 찾을 수 없습니다.",
        )

    # 보상 아이템이 없거나 삭제된 미션도 조회 대상에서 빼야 해서 inner join으로 거릅니다.
    mission = db.scalar(
        select(Mission)
        .join(Mission.reward_item)
        .where(
            Mission.id == mission_id,
            Mission.mission_type == MissionType.DAILY,
            Mission.is_active.is_(True),
            Mission.deleted_at.is_(None),
            RewardItem.deleted_at.is_(None),
        )
        .options(joinedload(Mission.reward_item))
        .limit(1)
    )
    if mission is None:
        raise ApiError(
            status_code=404,
            code="DAILY_MISSION_NOT_FOUND",
            message="데일리 미션 정보를 찾을 수 없습니다.",
        )

    reward_item = mission.reward_item
    return MissionDailyDetailResponse(
        mission=MissionDailyDetailItemResponse(
            id=mission.id,
            mission_type=mission.mission_type.value,
            title=mission.title,
            mission_info=mission.mission_info,
            reward_item=MissionDailyRewardItemResponse(
                id=reward_item.id,
                name=reward_item.name,
                reward_type=reward_item.reward_type.value,
                reward_count=reward_item.reward_count,
            ),
        )
    )


def claim_mission_reward(
    *,
    db: Session,
    current_user_id: int,
    mission_id: int,
    mission_type: MissionType,
) -> MissionRewardClaimResponse:
    """완료한 미션의 보상과 레벨 상승 보상을 마지막 접근 큐브 소유권에 지급합니다."""
    cube_ownership = db.scalar(
        select(CubeOwnership)
        .where(
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .limit(1)
    )
    if cube_ownership is None:
        raise ApiError(
            status_code=404,
            code="CUBE_OWNERSHIP_NOT_FOUND",
            message="큐브 소유권 정보를 찾을 수 없습니다.",
        )

    # 보상 아이템이 없거나 삭제된 미션은 지급하지 않도록 inner join으로 거릅니다.
    mission = db.scalar(
        select(Mission)
        .join(Mission.reward_item)
        .where(
            Mission.id == mission_id,
            Mission.mission_type == mission_type,
            Mission.is_active.is_(True),
            Mission.deleted_at.is_(None),
            RewardItem.deleted_at.is_(None),
        )
        .options(joinedload(Mission.reward_item))
        .limit(1)
    )
    if mission is None:
        raise ApiError(
            status_code=404,
            code="MISSION_NOT_FOUND",
            message="미션 정보를 찾을 수 없습니다.",
        )

    progress = db.scalar(
        select(MissionProgress)
        .where(
            MissionProgress.cube_ownership_id == cube_ownership.id,
            MissionProgress.mission_id == mission.id,
        )
        .limit(1)
    )
    if progress is None or progress.status not in (
        MissionProgressStatus.COMPLETED,
        MissionProgressStatus.REWARDED,
    ):
        raise ApiError(
            status_code=409,
            code="MISSION_NOT_COMPLETED",
            message="완료되지 않은 미션입니다.",
        )

    reward_item = mission.reward_item
    reward_items = [reward_item]
    level_up = None
    affinity = None
    new_xp = 0
    if reward_item.reward_type == RewardItemType.AFFINITY_POINT:
        affinity, new_xp, reached_level, level_rewards = _calculate_affinity_reward(
            db=db,
            cube_ownership_id=cube_ownership.id,
            reward_count=reward_item.reward_count,
        )
        reward_items.extend(level_rewards)
        if reached_level is not None:
            level_up = MissionLevelUpResponse(
                level=reached_level.level,
                level_name=reached_level.level_name.value,
            )

    # 모든 보상과 진행 상태에 같은 수령 시각을 기록합니다.
    claimed_at = datetime.now(KST).replace(tzinfo=None, microsecond=0)
    try:
        for item in reward_items:
            db.add(
                UserReward(
                    cube_ownership_id=cube_ownership.id,
                    reward_item_id=item.id,
                    acquired_at=claimed_at,
                )
            )
        if affinity is not None:
            affinity.current_xp = new_xp
            if level_up is not None:
                affinity.level_id = reached_level.id
        progress.status = MissionProgressStatus.REWARDED
        progress.reward_claimed = True
        progress.claimed_at = claimed_at
        db.commit()
    except Exception:
        db.rollback()
        raise

    return MissionRewardClaimResponse(level_up=level_up)


def _calculate_affinity_reward(
    *,
    db: Session,
    cube_ownership_id: int,
    reward_count: int | None,
) -> tuple[Affinity, int, Level | None, list[RewardItem]]:
    """친밀도 포인트 지급 후의 누적 XP와 상승한 레벨, 지급할 레벨 보상을 계산합니다."""
    # 동시 보상 수령으로 포인트가 유실되지 않도록 친밀도 행을 잠급니다.
    affinity = db.scalar(
        select(Affinity)
        .where(Affinity.cube_ownership_id == cube_ownership_id)
        .limit(1)
        .with_for_update()
    )
    if affinity is None:
        raise ApiError(
            status_code=404,
            code="CUBE_AFFINITY_NOT_FOUND",
            message="큐브 친밀도 정보를 찾을 수 없습니다.",
        )
    if reward_count is None or reward_count <= 0:
        _raise_invalid_reference_data()

    current_level = db.scalar(
        select(Level).where(Level.id == affinity.level_id).limit(1)
    )
    new_xp = affinity.current_xp + reward_count
    reached_level = db.scalar(
        select(Level)
        .where(Level.level_xp <= new_xp)
        .order_by(Level.level.desc())
        .limit(1)
    )
    if current_level is None or reached_level is None:
        _raise_invalid_reference_data()

    if reached_level.level <= current_level.level:
        return affinity, new_xp, None, []

    # 한 번에 여러 레벨을 통과해도 중간 레벨 보상까지 빠짐없이 지급합니다.
    level_rewards = list(
        db.scalars(
            select(RewardItem)
            .where(
                RewardItem.reward_level > current_level.level,
                RewardItem.reward_level <= reached_level.level,
                RewardItem.deleted_at.is_(None),
            )
            .order_by(RewardItem.reward_level.asc(), RewardItem.id.asc())
        )
    )
    return affinity, new_xp, reached_level, level_rewards


def _raise_invalid_reference_data() -> NoReturn:
    # 보상·레벨 기준 데이터 오류라 클라이언트 오류가 아닌 공통 500으로 처리합니다.
    raise ApiError(
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="서버 내부 오류가 발생했습니다.",
    )
