"""SQLAlchemy 비동기 엔진과 요청 단위 세션."""

import ssl
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

# Azure Database for MySQL은 TLS 연결을 사용합니다. 로컬 MySQL은 DB_SSL=false입니다.
connect_args = {"ssl": ssl.create_default_context()} if settings.db_ssl else {}
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args=connect_args,
)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI Depends에서 사용하며 요청 종료 시 세션을 자동 반환합니다."""
    async with SessionFactory() as session:
        yield session


async def dispose_engine() -> None:
    """애플리케이션 종료 시 DB 연결 풀을 정리합니다."""
    await engine.dispose()

