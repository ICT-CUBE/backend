"""아바타 인터랙션 테이블 ORM 매핑."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.cube import CubeOwnership, enum_values
from app.models.enums import AvatarInteractionSessionStatus


class AvatarInteractionSession(Base):
    __tablename__ = "avatar_interaction_session"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cube_ownership_id: Mapped[int] = mapped_column(ForeignKey("cube_ownership.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[AvatarInteractionSessionStatus] = mapped_column(
        Enum(
            AvatarInteractionSessionStatus,
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

    cube_ownership: Mapped[CubeOwnership] = relationship(
        back_populates="avatar_interaction_sessions"
    )
    pictures: Mapped[list["AvatarInteractionPicture"]] = relationship(
        back_populates="interaction_session"
    )


class AvatarInteractionPicture(Base):
    __tablename__ = "avatar_interaction_picture"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    interaction_session_id: Mapped[int] = mapped_column(
        ForeignKey("avatar_interaction_session.id")
    )
    picture_img_url: Mapped[str] = mapped_column(String(500))
    pictured_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    interaction_session: Mapped[AvatarInteractionSession] = relationship(
        back_populates="pictures"
    )
