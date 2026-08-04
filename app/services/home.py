"""홈 화면에 필요한 사용자·큐브·친밀도 조회 로직."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApiError
from app.models.cube import Affinity, Cube, CubeOwnership
from app.models.enums import OwnershipStatus
from app.models.reward import Level
from app.models.user import User
from app.schemas.home import (
    HomeAffinityResponse,
    HomeCubeOwnershipResponse,
    HomeCubeResponse,
    HomeLevelResponse,
    HomeResponse,
    HomeUserResponse,
)


def cube_ownership_not_found_error() -> ApiError:
    """현재 사용자에게 조회할 활성 큐브 소유권이 없을 때 반환합니다."""
    return ApiError(
        status_code=404,
        code="CUBE_OWNERSHIP_NOT_FOUND",
        message="큐브 소유권 정보를 찾을 수 없습니다.",
    )


async def get_home(*, session: AsyncSession, user_id: int) -> HomeResponse:
    """마지막 접근 여부와 취득일을 기준으로 홈에 표시할 활성 큐브를 조회합니다."""
    statement = (
        select(User, CubeOwnership, Cube, Affinity, Level)
        .join(CubeOwnership, CubeOwnership.user_id == User.id)
        .join(Cube, Cube.id == CubeOwnership.cube_id)
        .join(Affinity, Affinity.cube_ownership_id == CubeOwnership.id)
        .join(Level, Level.id == Affinity.level_id)
        .where(
            User.id == user_id,
            User.deleted_at.is_(None),
            Cube.deleted_at.is_(None),
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
        )
        .order_by(
            CubeOwnership.is_last_accessed.desc(),
            CubeOwnership.acquired_at.desc(),
        )
        .limit(1)
    )
    row = (await session.execute(statement)).one_or_none()
    if row is None:
        raise cube_ownership_not_found_error()

    user, ownership, cube, affinity, level = row
    return HomeResponse(
        user=HomeUserResponse(
            id=user.id,
            profile_character_img_code=user.profile_character_img_code,
        ),
        cube_ownership=HomeCubeOwnershipResponse(
            id=ownership.id,
            avatar_nickname=ownership.avatar_nickname,
            acquired_at=ownership.acquired_at,
        ),
        cube=HomeCubeResponse(id=cube.id, artist_name=cube.artist_name),
        affinity=HomeAffinityResponse(
            id=affinity.id,
            current_xp=affinity.current_xp,
            level=HomeLevelResponse(
                id=level.id,
                level=level.level,
                level_name=level.level_name.value,
                level_xp=level.level_xp,
            ),
        ),
    )
