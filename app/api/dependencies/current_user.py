"""인증 없이 사용할 데모 사용자를 식별하는 의존성."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ApiError
from app.db.session import get_db_session
from app.models.enums import UserStatus
from app.models.user import User


async def get_current_user_id(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> int:
    """설정된 이메일의 활성 데모 사용자 ID를 DB에서 조회합니다."""
    settings = get_settings()
    result = await session.execute(
        select(User.id).where(
            User.email == settings.demo_user_email,
            User.status == UserStatus.ACTIVE,
            User.deleted_at.is_(None),
        )
    )
    user_id = result.scalar_one_or_none()
    if user_id is None:
        raise ApiError(
            status_code=500,
            code="DEMO_USER_NOT_FOUND",
            message="데모 사용자 초기화가 필요합니다.",
        )
    return user_id
