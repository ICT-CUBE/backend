"""레벨, 보상, 미션 진행 모델."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    false,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin
from app.models.enums import (
    LevelName,
    MissionProgressStatus,
    MissionType,
    RewardType,
    TargetAction,
    enum_type,
)


class RewardItem(TimestampMixin, SoftDeleteMixin, Base):
    """레벨·미션으로 획득할 수 있는 보상 정의."""

    __tablename__ = "reward_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    reward_type: Mapped[RewardType] = mapped_column(
        enum_type(RewardType, name="reward_type", length=30),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reward_count: Mapped[int] = mapped_column(Integer, nullable=False)


class Level(TimestampMixin, Base):
    """친밀도 레벨 및 달성 보상 정의."""

    __tablename__ = "levels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reward_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("reward_items.id"), nullable=False, index=True
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    level_xp: Mapped[int] = mapped_column(Integer, nullable=False)
    level_name: Mapped[LevelName] = mapped_column(
        enum_type(LevelName, name="level_name", length=30),
        nullable=False,
    )


class Mission(TimestampMixin, SoftDeleteMixin, Base):
    """일일·이벤트 미션 정의."""

    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reward_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("reward_items.id"), nullable=False, index=True
    )
    mission_type: Mapped[MissionType] = mapped_column(
        enum_type(MissionType, name="mission_type", length=20),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mission_info: Mapped[str | None] = mapped_column(String(500), nullable=True)
    target_action: Mapped[TargetAction] = mapped_column(
        enum_type(TargetAction, name="mission_target_action", length=50),
        nullable=False,
    )
    target_count: Mapped[int] = mapped_column(Integer, nullable=False)
    start_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )


class MissionProgress(TimestampMixin, Base):
    """큐브 소유권별 미션 진행 상태."""

    __tablename__ = "mission_progresses"
    __table_args__ = (
        UniqueConstraint(
            "cube_ownership_id",
            "mission_id",
            name="uq_mission_progresses_ownership_mission",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cube_ownership_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cube_ownerships.id"), nullable=False, index=True
    )
    mission_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("missions.id"), nullable=False, index=True
    )
    current_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    status: Mapped[MissionProgressStatus] = mapped_column(
        enum_type(MissionProgressStatus, name="mission_progress_status", length=20),
        nullable=False,
        default=MissionProgressStatus.IN_PROGRESS,
        server_default=MissionProgressStatus.IN_PROGRESS.value,
    )
    reward_claimed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class UserReward(TimestampMixin, Base):
    """큐브 소유권 단위로 실제 획득한 보상."""

    __tablename__ = "user_rewards"
    __table_args__ = (
        UniqueConstraint(
            "cube_ownership_id",
            "reward_item_id",
            name="uq_user_rewards_ownership_reward",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cube_ownership_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cube_ownerships.id"), nullable=False, index=True
    )
    reward_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("reward_items.id"), nullable=False, index=True
    )
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )
