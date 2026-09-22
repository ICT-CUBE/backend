"""다른 도메인의 사용자 행동을 미션 진행도에 반영하는 공통 로직."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.enums import (
    MissionProgressStatus,
    MissionTargetAction,
    MissionType,
    OwnershipStatus,
)
from app.cube.models import CubeOwnership
from app.mission.models import Mission, MissionProgress

KOREA_TIMEZONE = timezone(timedelta(hours=9))


def increase_mission_progress(
    *,
    db: Session,
    current_user_id: int,
    target_action: MissionTargetAction,
) -> None:
    """행동에 해당하는 진행 중 미션의 진행도를 1 올리고 목표에 닿으면 완료 처리합니다.

    호출한 서비스의 트랜잭션과 함께 저장·롤백되도록 commit 하지 않습니다.
    """
    cube_ownership_id = db.scalar(
        select(CubeOwnership.id)
        .where(
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .limit(1)
    )
    if cube_ownership_id is None:
        # 미션은 큐브 소유권 기준이라 소유권이 없으면 원래 API만 처리합니다.
        return

    now = datetime.now(KOREA_TIMEZONE).replace(tzinfo=None, microsecond=0)
    missions = db.scalars(
        select(Mission)
        .where(
            Mission.target_action == target_action,
            Mission.is_active.is_(True),
            Mission.deleted_at.is_(None),
            or_(Mission.start_at.is_(None), Mission.start_at <= now),
            or_(Mission.end_at.is_(None), Mission.end_at >= now),
        )
        .order_by(Mission.id.asc())
    ).all()
    for mission in missions:
        _increase_progress(
            db=db,
            cube_ownership_id=cube_ownership_id,
            mission=mission,
            now=now,
        )


def _increase_progress(
    *,
    db: Session,
    cube_ownership_id: int,
    mission: Mission,
    now: datetime,
) -> None:
    """미션 하나의 진행도를 올리고 목표 횟수에 도달하면 COMPLETED로 바꿉니다."""
    # 같은 행동이 동시에 들어와도 횟수가 유실되지 않도록 진행 행을 잠급니다.
    progress = db.scalar(
        select(MissionProgress)
        .where(
            MissionProgress.cube_ownership_id == cube_ownership_id,
            MissionProgress.mission_id == mission.id,
        )
        .limit(1)
        .with_for_update()
    )
    if progress is None:
        progress = MissionProgress(
            cube_ownership_id=cube_ownership_id,
            mission_id=mission.id,
            current_count=0,
            status=MissionProgressStatus.IN_PROGRESS,
            reward_claimed=False,
            completed_at=None,
            claimed_at=None,
        )
        db.add(progress)
    elif _is_previous_day_daily_progress(mission=mission, progress=progress, now=now):
        _reset_progress(progress)

    # 이미 완료했거나 보상을 받은 미션은 다시 호출돼도 횟수를 올리지 않습니다.
    if progress.status != MissionProgressStatus.IN_PROGRESS:
        return

    progress.current_count += 1
    if progress.current_count >= mission.target_count:
        progress.status = MissionProgressStatus.COMPLETED
        progress.completed_at = now


def _is_previous_day_daily_progress(
    *,
    mission: Mission,
    progress: MissionProgress,
    now: datetime,
) -> bool:
    """데일리 미션 진행 행이 오늘(KST) 이전에 마지막으로 갱신됐는지 확인합니다."""
    # DB 세션 타임존이 KST라 updated_at도 KST naive 값입니다.
    return (
        mission.mission_type == MissionType.DAILY
        and progress.updated_at is not None
        and progress.updated_at.date() < now.date()
    )


def _reset_progress(progress: MissionProgress) -> None:
    """날짜가 바뀐 데일리 미션 진행 행을 처음 상태로 되돌립니다."""
    progress.current_count = 0
    progress.status = MissionProgressStatus.IN_PROGRESS
    progress.reward_claimed = False
    progress.completed_at = None
    progress.claimed_at = None
