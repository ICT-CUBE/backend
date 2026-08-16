"""홈 화면에 필요한 사용자·큐브·친밀도 조회 로직."""

from sqlalchemy import case, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ApiError
from app.models.cube import Affinity, CubeOwnership
from app.models.enums import OwnershipStatus
from app.schemas.home import (
    HomeAffinityResponse,
    HomeCubeOwnershipResponse,
    HomeCubeResponse,
    HomeLevelResponse,
    HomeResponse,
    HomeUserResponse,
)


def get_home(*, db: Session, current_user_id: int) -> HomeResponse:
    """현재 사용자의 홈 정보를 ORM으로 조회합니다."""
    # 홈 응답에 필요한 연관 객체를 한 번에 가져옵니다. ACTIVE 소유권이 있으면
    # 우선하고, 없으면 최근 비활성 소유권을 반환해 403과 404를 구분합니다.
    ownership = db.scalars(
        select(CubeOwnership)
        .where(CubeOwnership.user_id == current_user_id)
        .options(
            joinedload(CubeOwnership.user),
            joinedload(CubeOwnership.cube),
            joinedload(CubeOwnership.affinity).joinedload(Affinity.level_info),
        )
        .order_by(
            case(
                (CubeOwnership.ownership_status == OwnershipStatus.ACTIVE, 0),
                else_=1,
            ),
            CubeOwnership.is_last_accessed.desc(),
            CubeOwnership.acquired_at.desc(),
        )
        .limit(1)
    ).first()

    if ownership is None:
        raise ApiError(
            status_code=404,
            code="CUBE_OWNERSHIP_NOT_FOUND",
            message="큐브 소유권 정보를 찾을 수 없습니다.",
        )
    if ownership.ownership_status != OwnershipStatus.ACTIVE:
        raise ApiError(
            status_code=403,
            code="CUBE_OWNERSHIP_FORBIDDEN",
            message="해당 큐브 소유권 정보를 조회할 권한이 없습니다.",
        )

    user = ownership.user
    cube = ownership.cube
    affinity = ownership.affinity
    if affinity is None:
        raise ApiError(
            status_code=404,
            code="CUBE_AFFINITY_NOT_FOUND",
            message="큐브 친밀도 정보를 찾을 수 없습니다.",
        )
    level = affinity.level_info

    return HomeResponse(
        user=HomeUserResponse(
            id=user.id,
            profile_character_img_url=user.profile_character_img_url,
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
