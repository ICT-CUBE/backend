"""테스트 공용 헬퍼."""

from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.main import app

TEST_USER_ID = 1


@contextmanager
def api_client(
    db: Session,
    *,
    raise_server_exceptions: bool = True,
    authenticate: bool = True,
) -> Iterator[TestClient]:
    """Mock DB 세션을 주입한 TestClient를 열고, 종료 시 의존성 오버라이드를 되돌립니다.

    `authenticate=False`면 JWT 검증 의존성을 그대로 두어 인증 자체를 테스트할 수 있습니다.
    """

    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    if authenticate:
        app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    try:
        with TestClient(
            app,
            raise_server_exceptions=raise_server_exceptions,
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
