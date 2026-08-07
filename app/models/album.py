"""앨범, 영상·음원 재생 세션 및 캡처 모델."""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    false,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin
from app.models.enums import (
    AlbumImageType,
    PlaybackStatus,
    PlayMode,
    VideoType,
    ViewMode,
    enum_type,
)


class Album(TimestampMixin, Base):
    """아티스트 앨범 메타데이터."""

    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    artist_name: Mapped[str] = mapped_column(String(100), nullable=False)
    artist_company: Mapped[str] = mapped_column(String(100), nullable=False)
    track_count: Mapped[int] = mapped_column(Integer, nullable=False)
    track_total_second: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    release_date: Mapped[date] = mapped_column(Date, nullable=False)


class Stage(TimestampMixin, Base):
    """앨범에 포함된 뮤직비디오·공연 영상."""

    __tablename__ = "stages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    album_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("albums.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str] = mapped_column(String(500), nullable=False)
    video_type: Mapped[VideoType] = mapped_column(
        enum_type(VideoType, name="video_type", length=20),
        nullable=False,
    )
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    is_title_video: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )


class StageSession(TimestampMixin, Base):
    """사용자의 영상 재생 세션."""

    __tablename__ = "stage_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cube_ownership_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cube_ownerships.id"), nullable=False, index=True
    )
    stage_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stages.id"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_position_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    viewed_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    view_mode: Mapped[ViewMode] = mapped_column(
        enum_type(ViewMode, name="stage_view_mode", length=20),
        nullable=False,
    )
    status: Mapped[PlaybackStatus] = mapped_column(
        enum_type(PlaybackStatus, name="stage_session_status", length=20),
        nullable=False,
        default=PlaybackStatus.PLAYING,
        server_default=PlaybackStatus.PLAYING.value,
    )


class StageCapture(TimestampMixin, SoftDeleteMixin, Base):
    """영상 재생 중 저장한 캡처."""

    __tablename__ = "stage_captures"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    stage_session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stage_sessions.id"), nullable=False, index=True
    )
    stage_capture_img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    captured_position_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Track(TimestampMixin, Base):
    """앨범에 포함된 음원 트랙."""

    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    album_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("albums.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    artist_name: Mapped[str] = mapped_column(String(100), nullable=False)
    audio_url: Mapped[str] = mapped_column(String(500), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    lyrics: Mapped[str] = mapped_column(String(5000), nullable=False)
    track_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_title_track: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )


class TrackSession(TimestampMixin, Base):
    """사용자의 음원 재생 세션."""

    __tablename__ = "track_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cube_ownership_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cube_ownerships.id"), nullable=False, index=True
    )
    track_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tracks.id"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_position_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    viewed_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    play_mode: Mapped[PlayMode] = mapped_column(
        enum_type(PlayMode, name="track_play_mode", length=20),
        nullable=False,
    )
    status: Mapped[PlaybackStatus] = mapped_column(
        enum_type(PlaybackStatus, name="track_session_status", length=20),
        nullable=False,
        default=PlaybackStatus.PLAYING,
        server_default=PlaybackStatus.PLAYING.value,
    )


class TrackCapture(TimestampMixin, SoftDeleteMixin, Base):
    """음원 재생 화면에서 저장한 캡처."""

    __tablename__ = "track_captures"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    track_session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("track_sessions.id"), nullable=False, index=True
    )
    track_capture_img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    captured_position_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class AlbumImage(TimestampMixin, Base):
    """앨범 갤러리에 노출되는 이미지."""

    __tablename__ = "album_images"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    album_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("albums.id"), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    image_type: Mapped[AlbumImageType] = mapped_column(
        enum_type(AlbumImageType, name="album_image_type", length=30),
        nullable=False,
    )
    album_contents_img_url: Mapped[str] = mapped_column(String(500), nullable=False)
