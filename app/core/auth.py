"""인증 의존성.

Authorization 헤더의 Bearer Access Token을 검증해 현재 사용자 id를 돌려줍니다.
"""

from typing import Annotated, NoReturn

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import ApiError
from app.models.enums import UserStatus
from app.models.user import User

# 인증 실패는 모두 같은 401로 처리하므로 FastAPI 기본 오류 응답을 쓰지 않습니다.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> int:
    """Access Token을 검증하고 활성 사용자 id를 반환합니다."""
    if credentials is None:
        _raise_invalid_access_token()

    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError:
        _raise_invalid_access_token()

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        _raise_invalid_access_token()

    active_user_id = db.scalar(
        select(User.id)
        .where(
            User.id == user_id,
            User.status == UserStatus.ACTIVE,
            User.deleted_at.is_(None),
        )
        .limit(1)
    )
    if active_user_id is None:
        _raise_invalid_access_token()
    return active_user_id


def _raise_invalid_access_token() -> NoReturn:
    raise ApiError(
        status_code=401,
        code="INVALID_ACCESS_TOKEN",
        message="유효하지 않거나 만료된 액세스 토큰입니다.",
    )
