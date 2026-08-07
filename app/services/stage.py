"""스테이지 재생 세션 생성 및 상태 저장 로직."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApiError
from app.models.album import Stage, StageSession
from app.models.cube import CubeOwnership
from app.models.enums import OwnershipStatus, PlaybackStatus, ViewMode
from app.schemas.stage import StageSessionCreateResponse, StageSessionResponse


def stage_not_found_error() -> ApiError:
    return ApiError(
        status_code=404,
        code="STAGE_NOT_FOUND",
        message="스테이지 영상을 찾을 수 없습니다.",
    )


def active_cube_ownership_not_found_error() -> ApiError:
    return ApiError(
        status_code=404,
        code="ACTIVE_CUBE_OWNERSHIP_NOT_FOUND",
        message="활성화된 큐브 소유권을 찾을 수 없습니다.",
    )


def stage_session_not_found_error() -> ApiError:
    """세션이 없거나 현재 사용자의 세션이 아닐 때 같은 404를 반환합니다."""
    return ApiError(
        status_code=404,
        code="STAGE_SESSION_NOT_FOUND",
        message="스테이지 재생 세션을 찾을 수 없습니다.",
    )


def stage_session_already_ended_error() -> ApiError:
    return ApiError(
        status_code=409,
        code="STAGE_SESSION_ALREADY_ENDED",
        message="이미 종료된 스테이지 재생 세션입니다.",
    )


async def create_stage_session(
    *,
    session: AsyncSession,
    user_id: int,
    stage_id: int,
    view_mode: ViewMode,
) -> StageSessionCreateResponse:
    """활성 스테이지와 사용자의 활성 소유권을 확인한 뒤 재생 세션을 저장합니다."""
    found_stage_id = await session.scalar(
        select(Stage.id).where(Stage.id == stage_id, Stage.is_active.is_(True))
    )
    if found_stage_id is None:
        raise stage_not_found_error()

    cube_ownership_id = await session.scalar(
        select(CubeOwnership.id)
        .where(
            CubeOwnership.user_id == user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
        )
        .order_by(
            CubeOwnership.is_last_accessed.desc(),
            CubeOwnership.acquired_at.desc(),
        )
        .limit(1)
    )
    if cube_ownership_id is None:
        raise active_cube_ownership_not_found_error()

    stage_session = StageSession(
        cube_ownership_id=cube_ownership_id,
        stage_id=found_stage_id,
        last_position_seconds=0,
        view_mode=view_mode,
        status=PlaybackStatus.PLAYING,
    )
    session.add(stage_session)
    try:
        await session.flush()
        response = StageSessionCreateResponse(
            stage_session=StageSessionResponse(
                id=stage_session.id,
                view_mode=stage_session.view_mode,
            )
        )
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return response


async def update_stage_session(
    *,
    session: AsyncSession,
    user_id: int,
    stage_session_id: int,
    playback_status: PlaybackStatus,
    last_position_seconds: int,
    viewed_seconds: int,
) -> None:
    """현재 사용자의 재생 중 세션을 종료 또는 취소 상태로 갱신합니다."""
    stage_session = await session.scalar(
        select(StageSession)
        .join(
            CubeOwnership,
            CubeOwnership.id == StageSession.cube_ownership_id,
        )
        .where(
            StageSession.id == stage_session_id,
            CubeOwnership.user_id == user_id,
        )
        # 같은 세션에 종료 요청이 동시에 들어와도 한 요청만 성공하도록 행을 잠급니다.
        .with_for_update()
    )
    if stage_session is None:
        raise stage_session_not_found_error()
    if stage_session.status != PlaybackStatus.PLAYING:
        raise stage_session_already_ended_error()

    stage_session.status = playback_status
    stage_session.last_position_seconds = last_position_seconds
    stage_session.viewed_seconds = viewed_seconds
    # MySQL DATETIME 컬럼은 시간대 정보를 저장하지 않으므로 UTC 시각을 naive 값으로 저장합니다.
    stage_session.ended_at = datetime.now(UTC).replace(tzinfo=None)

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise
