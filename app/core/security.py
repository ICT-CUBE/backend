"""비밀번호 해시와 JWT Access Token 발급·검증."""

from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import get_settings

KOREA_TIMEZONE = timezone(timedelta(hours=9))
_password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    """비밀번호를 무작위 Salt가 포함된 Argon2id 해시로 변환합니다."""
    return _password_hash.hash(password)


def verify_password(*, password: str, password_hash: str) -> bool:
    """입력한 비밀번호가 저장된 Argon2id 해시와 일치하는지 검증합니다."""
    return _password_hash.verify(password, password_hash)


def create_access_token(*, user_id: int) -> tuple[str, int, datetime]:
    """Access Token과 유효시간(초), KST 기준 만료 시각을 함께 반환합니다."""
    settings = get_settings()
    expires_in = timedelta(days=settings.jwt_access_token_expire_days)
    issued_at = datetime.now(timezone.utc).replace(microsecond=0)
    expires_at = issued_at + expires_in
    access_token = jwt.encode(
        {"sub": str(user_id), "iat": issued_at, "exp": expires_at},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return (
        access_token,
        int(expires_in.total_seconds()),
        expires_at.astimezone(KOREA_TIMEZONE).replace(tzinfo=None),
    )
