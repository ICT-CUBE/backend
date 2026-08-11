"""스테이지 재생 세션 생성·저장 로직."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ApiError
from app.models.cube import CubeOwnership
from app.models.enums import OwnershipStatus, StageSessionStatus
from app.models.stage import Stage, StageSession
from app.schemas.stage import (
    StageSessionCreateResponse,
    StageSessionEndStatus,
    StageSessionResponse,
    StageViewMode,
)

CURRENT_USER_ID = 1
KOREA_TIMEZONE = timezone(timedelta(hours=9))


def create_stage_session(
    *,
    db: Session,
    stage_id: int,
    view_mode: StageViewMode,
) -> StageSessionCreateResponse:
    """활성 스테이지와 현재 사용자의 마지막 활성 소유권으로 세션을 만듭니다."""
    stage = db.scalar(
        select(Stage).where(Stage.id == stage_id, Stage.is_active.is_(True))
    )
    if stage is None:
        raise ApiError(
            status_code=404,
            code="STAGE_NOT_FOUND",
            message="스테이지 영상을 찾을 수 없습니다.",
        )

    # 소유권 행을 잠가 같은 사용자의 동시 생성 요청을 직렬화합니다.
    ownership = db.scalar(
        select(CubeOwnership)
        .where(
            CubeOwnership.user_id == CURRENT_USER_ID,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .limit(1)
        .with_for_update()
    )
    if ownership is None:
        raise ApiError(
            status_code=404,
            code="ACTIVE_CUBE_OWNERSHIP_NOT_FOUND",
            message="활성화된 큐브 소유권을 찾을 수 없습니다.",
        )

    playing_session_id = db.scalar(
        select(StageSession.id)
        .where(
            StageSession.cube_ownership_id == ownership.id,
            StageSession.stage_id == stage.id,
            StageSession.status == StageSessionStatus.PLAYING,
        )
        .limit(1)
    )
    if playing_session_id is not None:
        db.rollback()
        raise ApiError(
            status_code=409,
            code="STAGE_SESSION_ALREADY_PLAYING",
            message="이미 재생 중인 스테이지 세션이 있습니다.",
        )

    stage_session = StageSession(
        cube_ownership_id=ownership.id,
        stage_id=stage.id,
        started_at=datetime.now(KOREA_TIMEZONE).replace(tzinfo=None),
        ended_at=None,
        last_position_seconds=0,
        viewed_seconds=0,
        view_mode=view_mode,
        status=StageSessionStatus.PLAYING,
    )
    try:
        db.add(stage_session)
        # INSERT를 실행해 DB가 만든 AUTO_INCREMENT id를 객체에 채웁니다.
        db.flush()
        stage_session_id = stage_session.id
        db.commit()
    except Exception:
        db.rollback()
        raise

    return StageSessionCreateResponse(
        stageSession=StageSessionResponse(id=stage_session_id, viewMode=view_mode)
    )


def save_stage_session(
    *,
    db: Session,
    stage_session_id: int,
    end_status: StageSessionEndStatus,
    last_position_seconds: int,
    viewed_seconds: int,
) -> None:
    """현재 사용자의 PLAYING 세션을 종료 상태로 갱신합니다."""
    result = db.execute(
        select(StageSession, Stage.duration_seconds)
        .join(StageSession.cube_ownership)
        .join(StageSession.stage)
        .where(
            StageSession.id == stage_session_id,
            CubeOwnership.user_id == CURRENT_USER_ID,
        )
        .limit(1)
        .with_for_update()
    ).one_or_none()

    if result is None:
        raise ApiError(
            status_code=404,
            code="STAGE_SESSION_NOT_FOUND",
            message="스테이지 재생 세션을 찾을 수 없습니다.",
        )

    stage_session, duration_seconds = result
    if stage_session.status != StageSessionStatus.PLAYING:
        db.rollback()
        raise ApiError(
            status_code=409,
            code="STAGE_SESSION_ALREADY_ENDED",
            message="이미 종료된 스테이지 재생 세션입니다.",
        )
    if last_position_seconds > duration_seconds:
        db.rollback()
        raise ApiError(
            status_code=400,
            code="INVALID_REQUEST",
            message="요청값이 올바르지 않습니다.",
        )

    stage_session.status = StageSessionStatus(end_status.value)
    stage_session.last_position_seconds = last_position_seconds
    stage_session.viewed_seconds = viewed_seconds
    stage_session.ended_at = datetime.now(KOREA_TIMEZONE).replace(tzinfo=None)

    try:
        # 조회한 ORM 객체의 변경 사항은 commit 시 UPDATE로 반영됩니다.
        db.commit()
    except Exception:
        db.rollback()
        raise
