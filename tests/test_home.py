"""홈 정보 조회 API의 정상 및 오류 응답 테스트."""

from collections.abc import AsyncIterator
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user_id
from app.db.session import get_db_session
from app.main import app
from app.models.cube import Affinity, Cube, CubeOwnership
from app.models.enums import CubeStatus, LevelName, LoginProvider, OwnershipStatus, UserStatus
from app.models.reward import Level
from app.models.user import User


def make_home_row(
    *, include_affinity: bool = True
) -> tuple[User, CubeOwnership, Cube, Affinity | None, Level | None]:
    user = User(
        id=1,
        email="demo@hanium.local",
        login_provider=LoginProvider.EMAIL,
        status=UserStatus.ACTIVE,
        profile_character_img_code="PROFILE_01",
    )
    ownership = CubeOwnership(
        id=12,
        user_id=1,
        cube_id=15,
        avatar_nickname="젠득이",
        ownership_status=OwnershipStatus.ACTIVE,
        is_last_accessed=True,
        acquired_at=datetime(2026, 3, 19, 10, 30),
    )
    cube = Cube(
        id=15,
        serial_number="TEST-CUBE-001",
        product_name="JENNIE CUBE",
        ownership_code_hash="not-used-in-this-test",
        artist_name="JENNIE",
        status=CubeStatus.OWNED,
    )
    if not include_affinity:
        return user, ownership, cube, None, None

    affinity = Affinity(id=7, cube_ownership_id=12, level_id=3, current_xp=1245)
    level = Level(
        id=3,
        reward_item_id=1,
        level=3,
        level_xp=2000,
        level_name=LevelName.CLOSE,
    )
    return user, ownership, cube, affinity, level


def make_session_returning(row: object | None) -> AsyncMock:
    result = Mock()
    result.one_or_none.return_value = row
    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = result
    return session


def request_home(session: AsyncMock, *, raise_server_exceptions: bool = True):
    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_current_user_id] = lambda: 1
    try:
        with TestClient(app, raise_server_exceptions=raise_server_exceptions) as client:
            return client.get("/api/v1/users/me/home")
    finally:
        app.dependency_overrides.clear()


def test_get_home_returns_database_enum_value() -> None:
    response = request_home(make_session_returning(make_home_row()))

    assert response.status_code == 200
    assert response.json() == {
        "user": {"id": 1, "profileCharacterImgCode": "PROFILE_01"},
        "cubeOwnership": {
            "id": 12,
            "avatarNickname": "젠득이",
            "acquiredAt": "2026-03-19T10:30:00",
        },
        "cube": {"id": 15, "artistName": "JENNIE"},
        "affinity": {
            "id": 7,
            "currentXp": 1245,
            "level": {
                "id": 3,
                "level": 3,
                "levelName": "Close",
                "levelXp": 2000,
            },
        },
    }


def test_get_home_returns_404_without_active_ownership() -> None:
    response = request_home(make_session_returning(None))

    assert response.status_code == 404
    assert response.json() == {
        "code": "CUBE_OWNERSHIP_NOT_FOUND",
        "message": "큐브 소유권 정보를 찾을 수 없습니다.",
    }


def test_get_home_returns_common_500_for_incomplete_data() -> None:
    response = request_home(
        make_session_returning(make_home_row(include_affinity=False)),
        raise_server_exceptions=False,
    )

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "서버 오류가 발생했습니다.",
    }
