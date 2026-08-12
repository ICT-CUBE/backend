"""앨범과 앨범 이미지 테이블 ORM 매핑."""

from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.cube import enum_values
from app.models.enums import AlbumImageType


class Album(Base):
    __tablename__ = "album"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    artist_name: Mapped[str] = mapped_column(String(100))
    artist_company: Mapped[str] = mapped_column(String(100))
    track_count: Mapped[int] = mapped_column(Integer)
    track_total_second: Mapped[int] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    cover_image_url: Mapped[str] = mapped_column(String(500))
    release_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    images: Mapped[list["AlbumImage"]] = relationship(back_populates="album")


class AlbumImage(Base):
    __tablename__ = "album_image"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    album_id: Mapped[int] = mapped_column(ForeignKey("album.id"))
    title: Mapped[str | None] = mapped_column(String(150))
    image_type: Mapped[AlbumImageType] = mapped_column(
        Enum(
            AlbumImageType,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    album_contents_img_url: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    album: Mapped[Album] = relationship(back_populates="images")
