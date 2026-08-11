"""user 테이블 ORM 매핑."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    """01-schema.sql에서 생성된 user 테이블에 연결됩니다."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    login_provider: Mapped[str] = mapped_column(String(20))
    provider_user_id: Mapped[str | None] = mapped_column(String(255))
    nickname: Mapped[str | None] = mapped_column(String(8))
    # 프로필 캐릭터 이미지의 접근 URL입니다.
    profile_character_img_url: Mapped[str | None] = mapped_column(String(50))
    chat_violation_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    cube_ownerships: Mapped[list["CubeOwnership"]] = relationship(
        back_populates="user"
    )


from app.models.cube import CubeOwnership
