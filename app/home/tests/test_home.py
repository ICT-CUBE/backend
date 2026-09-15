"""홈 정보 조회 API 테스트."""

from datetime import datetime
from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.affinity.models import Affinity, Level
from app.core.enums import LevelName, OwnershipStatus
from app.core.tests.conftest import api_client
from app.cube.models import Cube, CubeOwnership
from app.main import app
from app.user.models import User


def request_home(db: Mock):
    with api_client(db) as client:
        return client.get("/api/v1/users/me/home")


def make_ownership(status: OwnershipStatus) -> CubeOwnership:
    user = User(id=1, profile_character_img_url="CHAR_MINA")
    cube = Cube(id=1, artist_name="ARZONE")
    level = Level(
        id=3,
        level=3,
        level_name=LevelName.CLOSE,
        level_xp=800,
    )
    affinity = Affinity(id=1, current_xp=1245, level_info=level)
    return CubeOwnership(
        id=1,
        user_id=1,
        avatar_nickname="루미",
        ownership_status=status,
        is_last_accessed=True,
        acquired_at=datetime.fromisoformat("2026-08-07T09:20:00"),
        user=user,
        cube=cube,
        affinity=affinity,
    )


def test_home_returns_orm_values_in_korea_time() -> None:
    db = Mock(spec=Session)
    db.scalars.return_value.first.return_value = make_ownership(
        OwnershipStatus.ACTIVE
    )
    db.scalar.return_value = 2000

    response = request_home(db)

    assert response.status_code == 200
    assert response.json() == {
        "user": {"id": 1, "profileCharacterImgUrl": "CHAR_MINA"},
        "cubeOwnership": {
            "id": 1,
            "avatarNickname": "루미",
            "acquiredAt": "2026-08-07T09:20:00",
        },
        "cube": {"id": 1, "artistName": "ARZONE"},
        "affinity": {
            "id": 1,
            "currentXp": 1245,
            "level": {
                "id": 3,
                "level": 3,
                "levelName": "Close",
                "levelXp": 2000,
            },
        },
    }
    db.scalars.assert_called_once()
    db.scalar.assert_called_once()
    db.execute.assert_not_called()


def test_home_returns_404_when_ownership_does_not_exist() -> None:
    db = Mock(spec=Session)
    db.scalars.return_value.first.return_value = None

    response = request_home(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CUBE_OWNERSHIP_NOT_FOUND",
        "message": "큐브 소유권 정보를 찾을 수 없습니다.",
    }


def test_home_returns_404_when_affinity_does_not_exist() -> None:
    db = Mock(spec=Session)
    ownership = make_ownership(OwnershipStatus.ACTIVE)
    ownership.affinity = None
    db.scalars.return_value.first.return_value = ownership

    response = request_home(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CUBE_AFFINITY_NOT_FOUND",
        "message": "큐브 친밀도 정보를 찾을 수 없습니다.",
    }


def test_home_returns_403_when_only_inactive_ownership_exists() -> None:
    db = Mock(spec=Session)
    db.scalars.return_value.first.return_value = make_ownership(
        OwnershipStatus.REVOKED
    )

    response = request_home(db)

    assert response.status_code == 403
    assert response.json() == {
        "code": "CUBE_OWNERSHIP_FORBIDDEN",
        "message": "해당 큐브 소유권 정보를 조회할 권한이 없습니다.",
    }


def test_home_swagger_contains_only_endpoint_specific_errors() -> None:
    operation = app.openapi()["paths"]["/api/v1/users/me/home"]["get"]

    assert set(operation["responses"]) == {"200", "403", "404"}
    assert operation["security"] == [{"HTTPBearer": []}]
