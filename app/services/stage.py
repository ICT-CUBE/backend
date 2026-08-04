"""스테이지 재생 세션 생성 및 조회 로직."""

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
