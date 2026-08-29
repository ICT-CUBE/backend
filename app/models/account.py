"""사용자 계정 주변 테이블 ORM 매핑."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.cube import Cube, enum_values
from app.models.enums import CubeVerificationStatus, NotificationType
from app.models.user import User


class CubeVerification(Base):
    __tablename__ = "cube_verification"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    cube_id: Mapped[int] = mapped_column(ForeignKey("cube.id"))
    verification_status: Mapped[CubeVerificationStatus] = mapped_column(
        Enum(
            CubeVerificationStatus,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    code_expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="cube_verifications")
    cube: Mapped[Cube] = relationship(back_populates="verifications")


class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(
            NotificationType,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(String(500))
    is_read: Mapped[bool] = mapped_column(Boolean)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="notifications")


class UserSetting(Base):
    __tablename__ = "user_setting"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean)
    new_conversation_enabled: Mapped[bool] = mapped_column(Boolean)
    affinity_change_enabled: Mapped[bool] = mapped_column(Boolean)
    daily_mission_refresh_enabled: Mapped[bool] = mapped_column(Boolean)
    trade_completed_enabled: Mapped[bool] = mapped_column(Boolean)
    trade_offer_enabled: Mapped[bool] = mapped_column(Boolean)
    community_comment_notice_enabled: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="setting")
