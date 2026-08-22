"""큐브 코드 인증과 큐브 소유권 생성 로직."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.exceptions import ApiError
from app.models.account import CubeVerification
from app.models.cube import Cube, CubeOwnership
from app.models.enums import CubeStatus, CubeVerificationStatus, OwnershipStatus
from app.schemas.cube import CubeVerificationRequest, CubeVerificationResponse

KOREA_TIMEZONE = timezone(timedelta(hours=9))


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
    db.flush()
    db.commit()

    return CubeVerificationResponse(cube_ownership_id=cube_ownership.id)


def _raise_cube_not_registrable() -> None:
    raise ApiError(
        status_code=409,
        code="CUBE_NOT_REGISTRABLE",
        message="소유권을 등록할 수 없는 큐브입니다.",
    )


def _matches_ownership_code(ownership_code: str, ownership_code_hash: str) -> bool:
    """현재는 DB에 저장된 4자리 문자열과 요청값을 그대로 비교합니다."""
    return ownership_code == ownership_code_hash
