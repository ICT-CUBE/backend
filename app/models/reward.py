"""리워드, 미션, 미션 진행, 사용자 보상 ORM 매핑."""

from datetime import datetime

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
from app.models.cube import CubeOwnership, enum_values
from app.models.enums import (
    MissionProgressStatus,
    MissionTargetAction,
    MissionType,
    RewardItemType,
)


class RewardItem(Base):
    __tablename__ = "reward_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    reward_type: Mapped[RewardItemType] = mapped_column(
        Enum(
            RewardItemType,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    description: Mapped[str | None] = mapped_column(String(255))
    reward_count: Mapped[int | None] = mapped_column(Integer)
    reward_level: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    missions: Mapped[list["Mission"]] = relationship(back_populates="reward_item")
    user_rewards: Mapped[list["UserReward"]] = relationship(
        back_populates="reward_item"
    )


class Mission(Base):
    __tablename__ = "mission"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reward_item_id: Mapped[int] = mapped_column(ForeignKey("reward_item.id"))
    mission_type: Mapped[MissionType] = mapped_column(
        Enum(
            MissionType,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(255))
    mission_info: Mapped[str | None] = mapped_column(String(500))
    target_action: Mapped[MissionTargetAction] = mapped_column(
        Enum(
            MissionTargetAction,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    target_count: Mapped[int] = mapped_column(Integer)
    start_at: Mapped[datetime | None] = mapped_column(DateTime)
    end_at: Mapped[datetime | None] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    reward_item: Mapped[RewardItem] = relationship(back_populates="missions")
    progresses: Mapped[list["MissionProgress"]] = relationship(
        back_populates="mission"
    )


class MissionProgress(Base):
    __tablename__ = "mission_progress"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cube_ownership_id: Mapped[int] = mapped_column(ForeignKey("cube_ownership.id"))
    mission_id: Mapped[int] = mapped_column(ForeignKey("mission.id"))
    current_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[MissionProgressStatus] = mapped_column(
        Enum(
            MissionProgressStatus,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    reward_claimed: Mapped[bool] = mapped_column(Boolean)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    cube_ownership: Mapped[CubeOwnership] = relationship(
        back_populates="mission_progresses"
    )
    mission: Mapped[Mission] = relationship(back_populates="progresses")


class UserReward(Base):
    __tablename__ = "user_reward"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cube_ownership_id: Mapped[int] = mapped_column(ForeignKey("cube_ownership.id"))
    reward_item_id: Mapped[int] = mapped_column(ForeignKey("reward_item.id"))
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    cube_ownership: Mapped[CubeOwnership] = relationship(
        back_populates="user_rewards"
    )
    reward_item: Mapped[RewardItem] = relationship(back_populates="user_rewards")
