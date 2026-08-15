from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args=settings.database_connect_args,
    pool_pre_ping=True,
    pool_recycle=3600,
)


@event.listens_for(engine, "connect")
def set_mysql_session_time_zone(
    dbapi_connection: Any,
    _connection_record: Any,
) -> None:
    """DB가 찍는 CURRENT_TIMESTAMP도 KST naive 값이 되도록 세션 타임존을 고정합니다."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SET time_zone = '+09:00'")
    finally:
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ping_database() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
