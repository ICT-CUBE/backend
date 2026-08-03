"""큐브 등록, 소유권과 친밀도 모델."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, false
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin
from app.models.enums import CubeStatus, OwnershipStatus, VerificationStatus, enum_type


class Cube(TimestampMixin, SoftDeleteMixin, Base):
    """실물 큐브 제품 정보."""

    __tablename__ = "cubes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    serial_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    product_name: Mapped[str] = mapped_column(String(150), nullable=False)
    ownership_code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    artist_name: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[CubeStatus] = mapped_column(
        enum_type(CubeStatus, name="cube_status", length=20),
        nullable=False,
        default=CubeStatus.UNREGISTERED,
        server_default=CubeStatus.UNREGISTERED.value,
    )


class CubeVerification(TimestampMixin, Base):
    """사용자의 큐브 소유 코드 검증 시도."""

    __tablename__ = "cube_verifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    cube_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cubes.id"), nullable=False, index=True
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, name="verification_status", length=20),
        nullable=False,
        default=VerificationStatus.PENDING,
        server_default=VerificationStatus.PENDING.value,
    )
    code_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CubeOwnership(TimestampMixin, Base):
    """큐브의 현재·과거 사용자 소유 이력."""

    __tablename__ = "cube_ownerships"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    cube_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cubes.id"), nullable=False, index=True
    )
    avatar_nickname: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ownership_status: Mapped[OwnershipStatus] = mapped_column(
        enum_type(OwnershipStatus, name="ownership_status", length=20),
        nullable=False,
        default=OwnershipStatus.ACTIVE,
        server_default=OwnershipStatus.ACTIVE.value,
    )
    is_last_accessed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    acquired_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    transferred_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Affinity(TimestampMixin, Base):
    """큐브 소유권별 아바타 친밀도 상태."""

    __tablename__ = "affinities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cube_ownership_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cube_ownerships.id"),
        nullable=False,
        unique=True,
    )
    level_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("levels.id"), nullable=False, index=True
    )
    current_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
