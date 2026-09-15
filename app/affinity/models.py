"""친밀도, 레벨 테이블 ORM 매핑."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, enum_values
from app.core.enums import LevelName
from app.cube.models import CubeOwnership


class Level(Base):
    __tablename__ = "level"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
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
