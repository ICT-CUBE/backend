"""트랙과 트랙 재생 세션 테이블 ORM 매핑."""

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
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.cube import CubeOwnership, enum_values
from app.models.enums import TrackPlayMode, TrackSessionStatus

if TYPE_CHECKING:
    from app.models.album import Album


class Track(Base):
    __tablename__ = "track"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    album_id: Mapped[int] = mapped_column(ForeignKey("album.id"))
    title: Mapped[str] = mapped_column(String(150))
    artist_name: Mapped[str] = mapped_column(String(100))
    audio_url: Mapped[str] = mapped_column(String(500))
    duration_seconds: Mapped[int] = mapped_column(Integer)
    lyrics: Mapped[str] = mapped_column(String(5000))
    track_number: Mapped[int] = mapped_column(Integer)
    is_title_track: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    sessions: Mapped[list[TrackSession]] = relationship(back_populates="track")
    album: Mapped[Album] = relationship(back_populates="tracks")


class TrackSession(Base):
    __tablename__ = "track_session"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cube_ownership_id: Mapped[int] = mapped_column(ForeignKey("cube_ownership.id"))
    track_id: Mapped[int] = mapped_column(ForeignKey("track.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_position_seconds: Mapped[int] = mapped_column(Integer)
    viewed_seconds: Mapped[int] = mapped_column(Integer)
    play_mode: Mapped[TrackPlayMode] = mapped_column(
        Enum(
            TrackPlayMode,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    status: Mapped[TrackSessionStatus] = mapped_column(
        Enum(
            TrackSessionStatus,
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
        back_populates="track_sessions"
    )
    track: Mapped[Track] = relationship(back_populates="sessions")
    captures: Mapped[list[TrackCapture]] = relationship(
        back_populates="track_session"
    )


class TrackCapture(Base):
    """Azure에 저장한 트랙 캡처의 DB 정보입니다."""

    __tablename__ = "track_capture"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    track_session_id: Mapped[int] = mapped_column(ForeignKey("track_session.id"))
    track_capture_img_url: Mapped[str] = mapped_column(String(500))
    captured_position_seconds: Mapped[int | None] = mapped_column(Integer)
    captured_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    track_session: Mapped[TrackSession] = relationship(back_populates="captures")
