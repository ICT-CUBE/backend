"""큐브, 큐브 소유권, 친밀도, 레벨 테이블 ORM 매핑."""

from datetime import datetime
from enum import Enum as PythonEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import CubeStatus, LevelName, OwnershipStatus

if TYPE_CHECKING:
    from app.models.account import CubeVerification
    from app.models.avatar import AvatarInteractionSession
    from app.models.conversation import AvatarConversationSession
    from app.models.market import MarketProduct
    from app.models.reward import MissionProgress, RewardItem, UserReward
    from app.models.stage import StageSession
    from app.models.track import TrackSession
    from app.models.user import User


def enum_values(enum_class: type[PythonEnum]) -> list[str]:
    """SQLAlchemy가 Enum 이름이 아니라 DDL의 실제 문자열 값을 사용하게 합니다."""
    return [str(item.value) for item in enum_class.__members__.values()]


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
    market_products: Mapped[list["MarketProduct"]] = relationship(
        back_populates="cube"
    )


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


class Level(Base):
    __tablename__ = "level"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reward_item_id: Mapped[int] = mapped_column(ForeignKey("reward_item.id"))
    level: Mapped[int] = mapped_column(Integer)
    level_xp: Mapped[int] = mapped_column(Integer)
    level_name: Mapped[LevelName] = mapped_column(
        Enum(
            LevelName,
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

    affinities: Mapped[list["Affinity"]] = relationship(back_populates="level_info")
    reward_item: Mapped["RewardItem"] = relationship(back_populates="levels")


class Affinity(Base):
    __tablename__ = "affinity"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cube_ownership_id: Mapped[int] = mapped_column(
        ForeignKey("cube_ownership.id"), unique=True
    )
    level_id: Mapped[int] = mapped_column(ForeignKey("level.id"))
    current_xp: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    cube_ownership: Mapped[CubeOwnership] = relationship(back_populates="affinity")
    level_info: Mapped[Level] = relationship(back_populates="affinities")
