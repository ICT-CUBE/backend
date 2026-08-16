"""스테이지와 재생 세션 테이블 ORM 매핑."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.cube import CubeOwnership, enum_values
from app.models.enums import StageSessionStatus, StageVideoType, StageViewMode

if TYPE_CHECKING:
    from app.models.album import Album


class Stage(Base):
    __tablename__ = "stage"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    album_id: Mapped[int] = mapped_column(ForeignKey("album.id"))
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text)
    video_url: Mapped[str] = mapped_column(String(500))
    video_type: Mapped[StageVideoType] = mapped_column(
        Enum(
            StageVideoType,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    duration_seconds: Mapped[int] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean)
    is_title_video: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    sessions: Mapped[list[StageSession]] = relationship(back_populates="stage")
    album: Mapped[Album] = relationship(back_populates="stages")


class StageSession(Base):
    __tablename__ = "stage_session"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cube_ownership_id: Mapped[int] = mapped_column(ForeignKey("cube_ownership.id"))
    stage_id: Mapped[int] = mapped_column(ForeignKey("stage.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_position_seconds: Mapped[int] = mapped_column(Integer)
    viewed_seconds: Mapped[int | None] = mapped_column(Integer)
    view_mode: Mapped[StageViewMode] = mapped_column(
        Enum(
            StageViewMode,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    status: Mapped[StageSessionStatus] = mapped_column(
        Enum(
            StageSessionStatus,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    # 생성·수정 시각은 DDL에 정의된 MySQL 기본값을 사용합니다.
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    cube_ownership: Mapped[CubeOwnership] = relationship(
        back_populates="stage_sessions"
    )
    stage: Mapped[Stage] = relationship(back_populates="sessions")
    captures: Mapped[list[StageCapture]] = relationship(
        back_populates="stage_session"
    )


class StageCapture(Base):
    """Azure에 저장한 스테이지 캡처의 DB 정보입니다."""

    __tablename__ = "stage_capture"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    stage_session_id: Mapped[int] = mapped_column(ForeignKey("stage_session.id"))
    stage_capture_img_url: Mapped[str] = mapped_column(String(500))
    captured_position_seconds: Mapped[int | None] = mapped_column(Integer)
    captured_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    stage_session: Mapped[StageSession] = relationship(back_populates="captures")
