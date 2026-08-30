"""큐브 코드 인증과 큐브 소유권·친밀도·해금 보상 생성 로직."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.exceptions import ApiError
from app.models.account import CubeVerification
from app.models.cube import Affinity, Cube, CubeOwnership, Level
from app.models.enums import CubeStatus, CubeVerificationStatus, OwnershipStatus
from app.models.reward import RewardItem, UserReward
from app.schemas.cube import CubeVerificationRequest, CubeVerificationResponse
from app.services.blockchain.mint import mint_cube_nft

KOREA_TIMEZONE = timezone(timedelta(hours=9))
# 새 큐브 소유권은 항상 1레벨에서 시작하며, 1레벨 해금 보상도 함께 지급합니다.
INITIAL_LEVEL = 1
INITIAL_AFFINITY_XP = 0


def verify_cube_code(
    *,
    db: Session,
    current_user_id: int,
    body: CubeVerificationRequest,
) -> CubeVerificationResponse:
    """4자리 큐브 인증번호를 확인하고 성공 시 큐브 소유권을 생성합니다."""
    cube = db.scalar(
        select(Cube)
        .where(
            Cube.id == body.cube_id,
            Cube.deleted_at.is_(None),
        )
        .limit(1)
        .with_for_update()
    )
    if cube is None:
        raise ApiError(
            status_code=404,
            code="CUBE_NOT_FOUND",
            message="큐브 정보를 찾을 수 없습니다.",
        )

    if cube.status != CubeStatus.UNREGISTERED:
        _raise_cube_not_registrable()

    existing_ownership_id = db.scalar(
        select(CubeOwnership.id)
        .where(CubeOwnership.cube_id == cube.id)
        .limit(1)
        .with_for_update()
    )
    if existing_ownership_id is not None:
        _raise_cube_not_registrable()

    now = datetime.now(KOREA_TIMEZONE).replace(tzinfo=None)
    verification_status = (
        CubeVerificationStatus.SUCCESS
        if _matches_ownership_code(body.ownership_code, cube.ownership_code_hash)
        else CubeVerificationStatus.FAILED
    )
    cube_verification = CubeVerification(
        user_id=current_user_id,
        cube_id=cube.id,
        verification_status=verification_status,
        code_expires_at=None,
        verified_at=now if verification_status == CubeVerificationStatus.SUCCESS else None,
    )
    db.add(cube_verification)
    db.flush()

    if verification_status == CubeVerificationStatus.FAILED:
        db.commit()
        raise ApiError(
            status_code=400,
            code="INVALID_CUBE_CODE",
            message="큐브 인증번호가 올바르지 않습니다.",
        )

    db.execute(
        update(CubeOwnership)
        .where(CubeOwnership.user_id == current_user_id)
        .values(is_last_accessed=False)
    )
    cube_ownership = CubeOwnership(
        user_id=current_user_id,
        cube_id=cube.id,
        avatar_nickname=None,
        ownership_status=OwnershipStatus.ACTIVE,
        is_last_accessed=True,
        acquired_at=now,
        transferred_at=None,
    )
    db.add(cube_ownership)
    try:
        # 친밀도에 넣을 소유권 id를 먼저 발급받습니다.
        db.flush()
        cube_ownership_id = cube_ownership.id
        db.add(_create_initial_affinity(db=db, cube_ownership_id=cube_ownership_id))
        for user_reward in _create_initial_rewards(
            db=db,
            cube_ownership_id=cube_ownership_id,
            acquired_at=now,
        ):
            db.add(user_reward)
        db.commit()
    except Exception:
        db.rollback()
        raise

    # 인증·소유권 저장을 마친 뒤 별도로 NFT를 발행합니다. 실패는 기록만 남깁니다.
    mint_cube_nft(
        db=db,
        user_id=current_user_id,
        cube_id=cube.id,
        serial_number=cube.serial_number,
    )
    return CubeVerificationResponse(cube_ownership_id=cube_ownership_id)


def _create_initial_affinity(*, db: Session, cube_ownership_id: int) -> Affinity:
    """새 큐브 소유권의 1레벨·경험치 0 친밀도를 만듭니다."""
    level = db.scalar(
        select(Level)
        .where(Level.level == INITIAL_LEVEL)
        .limit(1)
    )
    if level is None:
        # 레벨 기준 데이터가 없는 것은 서버 데이터 구성 오류이므로 공통 500으로 반환합니다.
        raise ApiError(
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="서버 내부 오류가 발생했습니다.",
        )

    return Affinity(
        cube_ownership_id=cube_ownership_id,
        level_id=level.id,
        current_xp=INITIAL_AFFINITY_XP,
    )


def _create_initial_rewards(
    *,
    db: Session,
    cube_ownership_id: int,
    acquired_at: datetime,
) -> list[UserReward]:
    """1레벨에 해금되는 보상을 새 큐브 소유권에 지급할 데이터로 만듭니다."""
    reward_items = db.scalars(
        select(RewardItem)
        .where(
            RewardItem.reward_level == INITIAL_LEVEL,
            RewardItem.deleted_at.is_(None),
        )
        .order_by(RewardItem.id.asc())
    )
    return [
        UserReward(
            cube_ownership_id=cube_ownership_id,
            reward_item_id=reward_item.id,
            acquired_at=acquired_at,
        )
        for reward_item in reward_items
    ]


def save_avatar_nickname(
    *,
    db: Session,
    current_user_id: int,
    cube_ownership_id: int,
    avatar_nickname: str,
) -> None:
    """현재 사용자의 활성 마지막 접근 소유권에 아바타 닉네임을 저장합니다."""
    # 소유권 행을 잠가 같은 소유권에 대한 동시 변경 요청을 직렬화합니다.
    cube_ownership = db.scalar(
        select(CubeOwnership)
        .where(
            CubeOwnership.id == cube_ownership_id,
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .limit(1)
        .with_for_update()
    )
    if cube_ownership is None:
        raise ApiError(
            status_code=404,
            code="CUBE_OWNERSHIP_NOT_FOUND",
            message="큐브 소유권 정보를 찾을 수 없습니다.",
        )

    cube_ownership.avatar_nickname = avatar_nickname
    try:
        # 조회한 ORM 객체의 변경 사항은 commit 시 UPDATE로 반영됩니다.
        db.commit()
    except Exception:
        db.rollback()
        raise


def _raise_cube_not_registrable() -> None:
    raise ApiError(
        status_code=409,
        code="CUBE_NOT_REGISTRABLE",
        message="소유권을 등록할 수 없는 큐브입니다.",
    )


def _matches_ownership_code(ownership_code: str, ownership_code_hash: str) -> bool:
    """현재는 DB에 저장된 4자리 문자열과 요청값을 그대로 비교합니다."""
    return ownership_code == ownership_code_hash
