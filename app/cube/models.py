"""큐브, 큐브 소유권, 큐브 인증 테이블 ORM 매핑."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, enum_values
from app.core.enums import CubeStatus, CubeVerificationStatus, OwnershipStatus

if TYPE_CHECKING:
    from app.affinity.models import Affinity
    from app.album.models import TrackSession
    from app.avatar.models import AvatarInteractionSession
    from app.conversation.models import AvatarConversationSession
    from app.market.models import SellListing
    from app.mission.models import MissionProgress, UserReward
    from app.stage.models import StageSession
    from app.user.models import User


class Cube(Base):
    __tablename__ = "cube"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    serial_number: Mapped[str] = mapped_column(String(100))
    product_name: Mapped[str] = mapped_column(String(150))
    ownership_code_hash: Mapped[str] = mapped_column(String(255))
    artist_name: Mapped[str] = mapped_column(String(20))
    status: Mapped[CubeStatus] = mapped_column(
        Enum(
            CubeStatus,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    product_image_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    ownerships: Mapped[list["CubeOwnership"]] = relationship(back_populates="cube")
    verifications: Mapped[list["CubeVerification"]] = relationship(
        back_populates="cube"
    )
    sell_listings: Mapped[list["SellListing"]] = relationship(back_populates="cube")


class CubeOwnership(Base):
    __tablename__ = "cube_ownership"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    cube_id: Mapped[int] = mapped_column(ForeignKey("cube.id"))
    avatar_nickname: Mapped[str | None] = mapped_column(String(30))
    ownership_status: Mapped[OwnershipStatus] = mapped_column(
        Enum(
            OwnershipStatus,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    is_last_accessed: Mapped[bool] = mapped_column(Boolean)
    acquired_at: Mapped[datetime] = mapped_column(DateTime)
    transferred_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="cube_ownerships")
    cube: Mapped[Cube] = relationship(back_populates="ownerships")
    affinity: Mapped["Affinity"] = relationship(
        back_populates="cube_ownership", uselist=False
    )
    stage_sessions: Mapped[list["StageSession"]] = relationship(
        back_populates="cube_ownership"
    )
    track_sessions: Mapped[list["TrackSession"]] = relationship(
        back_populates="cube_ownership"
    )
    mission_progresses: Mapped[list["MissionProgress"]] = relationship(
        back_populates="cube_ownership"
    )
    user_rewards: Mapped[list["UserReward"]] = relationship(
        back_populates="cube_ownership"
    )
    avatar_conversation_sessions: Mapped[list["AvatarConversationSession"]] = (
        relationship(back_populates="cube_ownership")
    )
    avatar_interaction_sessions: Mapped[list["AvatarInteractionSession"]] = (
        relationship(back_populates="cube_ownership")
    )


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

    user: Mapped["User"] = relationship(back_populates="cube_verifications")
    cube: Mapped[Cube] = relationship(back_populates="verifications")
