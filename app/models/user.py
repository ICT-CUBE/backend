"""사용자, 인증 세션, 알림 및 사용자 설정 모델."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, false, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin
from app.models.enums import (
    AuthSessionStatus,
    LoginProvider,
    NotificationType,
    UserStatus,
    enum_type,
)


class User(TimestampMixin, SoftDeleteMixin, Base):
    """서비스 사용자 계정."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    login_provider: Mapped[LoginProvider] = mapped_column(
        enum_type(LoginProvider, name="login_provider", length=20),
        nullable=False,
    )
    provider_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(8), nullable=True)
    profile_character_img_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    chat_violation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    status: Mapped[UserStatus] = mapped_column(
        enum_type(UserStatus, name="user_status", length=20),
        nullable=False,
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
    )


class AuthSession(TimestampMixin, SoftDeleteMixin, Base):
    """Refresh token 단위의 로그인 세션."""

    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    token_jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[AuthSessionStatus] = mapped_column(
        enum_type(AuthSessionStatus, name="auth_session_status", length=20),
        nullable=False,
        default=AuthSessionStatus.ACTIVE,
        server_default=AuthSessionStatus.ACTIVE.value,
    )
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Notification(TimestampMixin, Base):
    """사용자에게 발송된 알림."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        enum_type(NotificationType, name="notification_type", length=30),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(String(500), nullable=False)
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class UserSetting(TimestampMixin, Base):
    """사용자별 알림 수신 설정."""

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
    )
    push_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    new_conversation_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    affinity_change_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    daily_mission_refresh_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    trade_completed_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    trade_offer_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    community_comment_notice_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
