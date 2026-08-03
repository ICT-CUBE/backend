"""모든 SQLAlchemy 모델이 공유하는 Base와 공통 컬럼 Mixin."""

from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Alembic이 자동 생성하는 제약조건 이름이 실행 환경마다 달라지지 않게 고정합니다.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """새 모델은 이 클래스를 상속해야 Alembic이 변경을 감지합니다."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    """생성·수정 시각이 필요한 테이블의 공통 컬럼."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


class SoftDeleteMixin:
    """실제 행 삭제 대신 삭제 시각을 기록하는 테이블의 공통 컬럼."""

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

