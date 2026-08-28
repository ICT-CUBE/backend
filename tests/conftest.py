"""테스트 공용 헬퍼."""

from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app


@contextmanager
def api_client(
    db: Session,
    *,
    raise_server_exceptions: bool = True,
) -> Iterator[TestClient]:
    """Mock DB 세션을 주입한 TestClient를 열고, 종료 시 의존성 오버라이드를 되돌립니다."""

    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            raise_server_exceptions=raise_server_exceptions,
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
