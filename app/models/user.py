"""user 테이블 ORM 매핑."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.cube import enum_values
from app.models.enums import LoginProvider, UserStatus

if TYPE_CHECKING:
    from app.models.account import CubeVerification, Notification, UserSetting
    from app.models.community import Comment, CommentLike, Post, PostLike
    from app.models.market import SellingListLike, SellListing, Trade


class User(Base):
    """01-schema.sql에서 생성된 user 테이블에 연결됩니다."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    login_provider: Mapped[LoginProvider] = mapped_column(
        Enum(
            LoginProvider,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    provider_user_id: Mapped[str | None] = mapped_column(String(255))
    nickname: Mapped[str | None] = mapped_column(String(20))
    # 프로필 캐릭터 이미지의 접근 URL입니다.
    profile_character_img_url: Mapped[str | None] = mapped_column(String(500))
    chat_violation_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[UserStatus] = mapped_column(
        Enum(
            UserStatus,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    cube_ownerships: Mapped[list[CubeOwnership]] = relationship(
        back_populates="user"
    )
    cube_verifications: Mapped[list[CubeVerification]] = relationship(
        back_populates="user"
    )
    notifications: Mapped[list[Notification]] = relationship(back_populates="user")
    setting: Mapped[UserSetting] = relationship(back_populates="user", uselist=False)
    posts: Mapped[list[Post]] = relationship(back_populates="user")
    comments: Mapped[list[Comment]] = relationship(back_populates="user")
    post_likes: Mapped[list[PostLike]] = relationship(back_populates="user")
    comment_likes: Mapped[list[CommentLike]] = relationship(back_populates="user")
    sell_listings: Mapped[list[SellListing]] = relationship(back_populates="user")
    selling_list_likes: Mapped[list[SellingListLike]] = relationship(
        back_populates="user"
    )
    bought_trades: Mapped[list[Trade]] = relationship(back_populates="buyer")


from app.models.cube import CubeOwnership
