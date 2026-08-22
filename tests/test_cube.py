"""큐브 코드 인증 API 테스트."""

from collections.abc import Iterator
from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models.account import CubeVerification
from app.models.cube import Cube, CubeOwnership
from app.models.enums import CubeStatus


def request_cube_verification(
    db: Mock,
    *,
    body: dict[str, int | str] | None = None,
):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            return client.post(
                "/api/v1/cubes/verification",
                json=body
                if body is not None
                else {"cubeId": 2, "ownershipCode": "1234"},
            )
    finally:
        app.dependency_overrides.clear()


def make_cube(
    *,
    cube_id: int = 2,
    ownership_code_hash: str = "1234",
    status: CubeStatus = CubeStatus.UNREGISTERED,
) -> Cube:
    return Cube(
        id=cube_id,
        serial_number="ARZ-CUBE-0002",
        product_name="NO.0027",
        ownership_code_hash=ownership_code_hash,
        artist_name="Jennie",
        status=status,
        deleted_at=None,
    )


def assign_created_ids(added_objects: list[object]):
    def _assign_ids() -> None:
        for item in added_objects:
            if isinstance(item, CubeVerification) and item.id is None:
                item.id = 15
            if isinstance(item, CubeOwnership) and item.id is None:
                item.id = 4

    return _assign_ids


def test_create_cube_verification_success_creates_ownership():
    db = Mock()
    cube = make_cube()
    added_objects: list[object] = []
    db.scalar.side_effect = [cube, None]
    db.add.side_effect = added_objects.append
    db.flush.side_effect = assign_created_ids(added_objects)

    response = request_cube_verification(db)

    assert response.status_code == 201
    assert response.json() == {"cubeOwnershipId": 4}
    assert any(isinstance(item, CubeVerification) for item in added_objects)
    assert any(isinstance(item, CubeOwnership) for item in added_objects)
    db.execute.assert_called_once()
    db.commit.assert_called_once()


def test_create_cube_verification_returns_404_when_cube_not_found():
    db = Mock()
    db.scalar.return_value = None

    response = request_cube_verification(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CUBE_NOT_FOUND",
        "message": "큐브 정보를 찾을 수 없습니다.",
    }
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_cube_verification_returns_409_when_cube_already_owned():
    db = Mock()
    db.scalar.side_effect = [make_cube(), 10]

    response = request_cube_verification(db)

    assert response.status_code == 409
    assert response.json() == {
        "code": "CUBE_NOT_REGISTRABLE",
        "message": "소유권을 등록할 수 없는 큐브입니다.",
    }
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_cube_verification_returns_409_when_cube_status_is_not_unregistered():
    db = Mock()
    db.scalar.return_value = make_cube(status=CubeStatus.OWNED)

    response = request_cube_verification(db)

    assert response.status_code == 409
    assert response.json() == {
        "code": "CUBE_NOT_REGISTRABLE",
        "message": "소유권을 등록할 수 없는 큐브입니다.",
    }
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_cube_verification_returns_400_when_code_invalid():
    db = Mock()
    cube = make_cube(ownership_code_hash="1234")
    added_objects: list[object] = []
    db.scalar.side_effect = [cube, None]
    db.add.side_effect = added_objects.append
    db.flush.side_effect = assign_created_ids(added_objects)

    response = request_cube_verification(
        db,
        body={"cubeId": 2, "ownershipCode": "9999"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_CUBE_CODE",
        "message": "큐브 인증번호가 올바르지 않습니다.",
    }
    assert len(added_objects) == 1
    assert isinstance(added_objects[0], CubeVerification)
    assert added_objects[0].verification_status == "FAILED"
    db.commit.assert_called_once()


def test_create_cube_verification_returns_400_when_required_body_missing():
    db = Mock()

    response = request_cube_verification(db, body={"cubeId": 2})

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
