"""이메일 회원가입·로그인 로직."""

from datetime import datetime
from typing import NoReturn

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.schemas import (
    AuthResponse,
    AuthTokenResponse,
    AuthUserResponse,
)
from app.core.enums import LoginProvider, UserStatus
from app.core.exceptions import ApiError
from app.core.security import create_access_token, hash_password, verify_password
from app.user.models import User, UserSetting
from app.user.profile import ProfileCharacterCode, to_profile_image_url

TOKEN_TYPE = "Bearer"


def signup_with_email(
    *,
    db: Session,
    email: str,
    password: str,
    nickname: str,
    profile_character_code: ProfileCharacterCode,
) -> AuthResponse:
    """이메일 사용자를 기본 알림 설정과 함께 만들고 Access Token을 발급합니다."""
    existing_user_id = db.scalar(select(User.id).where(User.email == email).limit(1))
    if existing_user_id is not None:
        _raise_email_already_exists()

    user = User(
        email=email,
        password_hash=hash_password(password),
        login_provider=LoginProvider.EMAIL,
        provider_user_id=None,
        nickname=nickname,
        profile_character_img_url=to_profile_image_url(profile_character_code),
        chat_violation_count=0,
        status=UserStatus.ACTIVE,
        deleted_at=None,
    )
    try:
        db.add(user)
        # 기본 알림 설정 행에 넣을 사용자 id를 먼저 발급받습니다.
        db.flush()
        user_id = user.id
        db.add(_default_user_setting(user_id=user_id))
        access_token, expires_in, expires_at = create_access_token(user_id=user_id)
        db.commit()
    except IntegrityError:
        # 동시 가입으로 이메일 UNIQUE 제약을 위반한 경우도 같은 409로 처리합니다.
        db.rollback()
        _raise_email_already_exists()
    except Exception:
        db.rollback()
        raise

    return _auth_response(
        user_id=user_id,
        access_token=access_token,
        expires_in=expires_in,
        expires_at=expires_at,
    )


def login_with_email(*, db: Session, email: str, password: str) -> AuthResponse:
    """이메일 사용자의 비밀번호를 확인하고 Access Token을 새로 발급합니다."""
    user = db.scalar(
        select(User)
        .where(
            User.email == email,
            User.login_provider == LoginProvider.EMAIL,
            User.password_hash.is_not(None),
            User.status == UserStatus.ACTIVE,
            User.deleted_at.is_(None),
        )
        .limit(1)
    )
    # 사용자 없음과 비밀번호 불일치를 구분해서 알려주지 않습니다.
    if user is None or not verify_password(
        password=password,
        password_hash=user.password_hash,
    ):
        raise ApiError(
            status_code=401,
            code="INVALID_CREDENTIALS",
            message="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    access_token, expires_in, expires_at = create_access_token(user_id=user.id)
    return _auth_response(
        user_id=user.id,
        access_token=access_token,
        expires_in=expires_in,
        expires_at=expires_at,
    )


def _auth_response(
    *,
    user_id: int,
    access_token: str,
    expires_in: int,
    expires_at: datetime,
) -> AuthResponse:
    """사용자 id와 발급된 토큰 정보를 공통 응답으로 만듭니다."""
    return AuthResponse(
        user=AuthUserResponse(id=user_id),
        auth=AuthTokenResponse(
            access_token=access_token,
            token_type=TOKEN_TYPE,
            expires_in=expires_in,
            expires_at=expires_at,
        ),
    )


def _default_user_setting(*, user_id: int) -> UserSetting:
    """모든 알림을 켠 기본 사용자 설정을 만듭니다."""
    return UserSetting(
        user_id=user_id,
        push_enabled=True,
        new_conversation_enabled=True,
        affinity_change_enabled=True,
        daily_mission_refresh_enabled=True,
        trade_completed_enabled=True,
        trade_offer_enabled=True,
        community_comment_notice_enabled=True,
    )


def _raise_email_already_exists() -> NoReturn:
    raise ApiError(
        status_code=409,
        code="EMAIL_ALREADY_EXISTS",
        message="이미 사용 중인 이메일입니다.",
    )
