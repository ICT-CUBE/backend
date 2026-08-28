"""큐브 도메인 API 테스트."""

from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.main import app
from app.models.account import CubeVerification
from app.models.cube import Cube, CubeOwnership
from app.models.enums import CubeStatus, OwnershipStatus
from tests.conftest import api_client


def request_cube_verification(
    db: Mock,
    *,
    body: dict[str, int | str] | None = None,
):
    with api_client(db) as client:
        return client.post(
            "/api/v1/cubes/verification",
            json=body
            if body is not None
            else {"cubeId": 2, "ownershipCode": "1234"},
        )


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
    db = Mock(spec=Session)
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
    db = Mock(spec=Session)
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
    db = Mock(spec=Session)
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
    db = Mock(spec=Session)
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
    db = Mock(spec=Session)
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
    db = Mock(spec=Session)

    response = request_cube_verification(db, body={"cubeId": 2})

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }


# --- 아바타 닉네임 설정: PATCH /api/v1/users/me/cube-ownerships/{id}/avatar-nickname ---

OWNERSHIP_NOT_FOUND_RESPONSE = {
    "code": "CUBE_OWNERSHIP_NOT_FOUND",
    "message": "큐브 소유권 정보를 찾을 수 없습니다.",
}
INVALID_REQUEST_RESPONSE = {
    "code": "INVALID_REQUEST",
    "message": "요청값이 올바르지 않습니다.",
}


def request_avatar_nickname_update(
    db: Mock,
    *,
    cube_ownership_id: int | str = 12,
    body: dict[str, object] | None = None,
    raise_server_exceptions: bool = True,
):
    with api_client(db, raise_server_exceptions=raise_server_exceptions) as client:
        return client.patch(
            f"/api/v1/users/me/cube-ownerships/{cube_ownership_id}/avatar-nickname",
            json=body if body is not None else {"avatarNickname": "젠득이"},
        )


def make_cube_ownership(
    *,
    cube_ownership_id: int = 12,
    avatar_nickname: str | None = None,
) -> CubeOwnership:
    return CubeOwnership(
        id=cube_ownership_id,
        user_id=1,
        cube_id=2,
        avatar_nickname=avatar_nickname,
        ownership_status=OwnershipStatus.ACTIVE,
        is_last_accessed=True,
        transferred_at=None,
    )


def test_update_avatar_nickname_success_saves_nickname():
    db = Mock(spec=Session)
    cube_ownership = make_cube_ownership()
    db.scalar.return_value = cube_ownership

    response = request_avatar_nickname_update(db)

    assert response.status_code == 204
    assert response.content == b""
    assert cube_ownership.avatar_nickname == "젠득이"
    db.commit.assert_called_once()


def test_update_avatar_nickname_trims_surrounding_whitespace():
    db = Mock(spec=Session)
    cube_ownership = make_cube_ownership()
    db.scalar.return_value = cube_ownership

    response = request_avatar_nickname_update(
        db,
        body={"avatarNickname": "  젠득이  "},
    )

    assert response.status_code == 204
    assert cube_ownership.avatar_nickname == "젠득이"
    db.commit.assert_called_once()


def test_update_avatar_nickname_overwrites_existing_nickname():
    db = Mock(spec=Session)
    cube_ownership = make_cube_ownership(avatar_nickname="이전닉네임")
    db.scalar.return_value = cube_ownership

    response = request_avatar_nickname_update(
        db,
        body={"avatarNickname": "새닉네임"},
    )

    assert response.status_code == 204
    assert cube_ownership.avatar_nickname == "새닉네임"
    db.commit.assert_called_once()


def test_update_avatar_nickname_allows_same_nickname_as_current():
    db = Mock(spec=Session)
    cube_ownership = make_cube_ownership(avatar_nickname="젠득이")
    db.scalar.return_value = cube_ownership

    response = request_avatar_nickname_update(
        db,
        body={"avatarNickname": "젠득이"},
    )

    assert response.status_code == 204
    assert cube_ownership.avatar_nickname == "젠득이"
    db.commit.assert_called_once()


def test_update_avatar_nickname_allows_special_characters_and_inner_space():
    db = Mock(spec=Session)
    cube_ownership = make_cube_ownership()
    db.scalar.return_value = cube_ownership

    response = request_avatar_nickname_update(
        db,
        body={"avatarNickname": "Jennie 젠득 01 ♥!"},
    )

    assert response.status_code == 204
    assert cube_ownership.avatar_nickname == "Jennie 젠득 01 ♥!"
    db.commit.assert_called_once()


def test_update_avatar_nickname_allows_minimum_length_nickname():
    db = Mock(spec=Session)
    cube_ownership = make_cube_ownership()
    db.scalar.return_value = cube_ownership

    response = request_avatar_nickname_update(db, body={"avatarNickname": "젠"})

    assert response.status_code == 204
    assert cube_ownership.avatar_nickname == "젠"
    db.commit.assert_called_once()


def test_update_avatar_nickname_allows_maximum_length_nickname():
    db = Mock(spec=Session)
    cube_ownership = make_cube_ownership()
    db.scalar.return_value = cube_ownership

    response = request_avatar_nickname_update(db, body={"avatarNickname": "가" * 30})

    assert response.status_code == 204
    assert cube_ownership.avatar_nickname == "가" * 30
    db.commit.assert_called_once()


def test_update_avatar_nickname_allows_maximum_length_after_trimming():
    db = Mock(spec=Session)
    cube_ownership = make_cube_ownership()
    db.scalar.return_value = cube_ownership

    response = request_avatar_nickname_update(
        db,
        body={"avatarNickname": "  " + "가" * 30 + "  "},
    )

    assert response.status_code == 204
    assert cube_ownership.avatar_nickname == "가" * 30
    db.commit.assert_called_once()


def test_update_avatar_nickname_returns_400_when_nickname_exceeds_maximum_length():
    db = Mock(spec=Session)
    db.scalar.return_value = make_cube_ownership()

    response = request_avatar_nickname_update(db, body={"avatarNickname": "가" * 31})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.commit.assert_not_called()


def test_update_avatar_nickname_returns_400_when_nickname_is_empty():
    db = Mock(spec=Session)
    db.scalar.return_value = make_cube_ownership()

    response = request_avatar_nickname_update(db, body={"avatarNickname": ""})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.commit.assert_not_called()


def test_update_avatar_nickname_returns_400_when_nickname_is_only_whitespace():
    db = Mock(spec=Session)
    db.scalar.return_value = make_cube_ownership()

    response = request_avatar_nickname_update(db, body={"avatarNickname": "   "})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.commit.assert_not_called()


def test_update_avatar_nickname_returns_400_when_nickname_is_null():
    db = Mock(spec=Session)
    db.scalar.return_value = make_cube_ownership()

    response = request_avatar_nickname_update(db, body={"avatarNickname": None})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.commit.assert_not_called()


def test_update_avatar_nickname_returns_400_when_nickname_is_missing():
    db = Mock(spec=Session)
    db.scalar.return_value = make_cube_ownership()

    response = request_avatar_nickname_update(db, body={})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.commit.assert_not_called()


def test_update_avatar_nickname_returns_400_when_nickname_type_is_invalid():
    db = Mock(spec=Session)
    db.scalar.return_value = make_cube_ownership()

    response = request_avatar_nickname_update(db, body={"avatarNickname": 1234})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.commit.assert_not_called()


def test_update_avatar_nickname_returns_400_when_ownership_id_is_zero():
    db = Mock(spec=Session)
    db.scalar.return_value = make_cube_ownership()

    response = request_avatar_nickname_update(db, cube_ownership_id=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.commit.assert_not_called()


def test_update_avatar_nickname_returns_400_when_ownership_id_is_not_a_number():
    db = Mock(spec=Session)
    db.scalar.return_value = make_cube_ownership()

    response = request_avatar_nickname_update(db, cube_ownership_id="abc")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.commit.assert_not_called()


def test_update_avatar_nickname_allows_minimum_ownership_id():
    db = Mock(spec=Session)
    cube_ownership = make_cube_ownership(cube_ownership_id=1)
    db.scalar.return_value = cube_ownership

    response = request_avatar_nickname_update(db, cube_ownership_id=1)

    assert response.status_code == 204
    assert cube_ownership.avatar_nickname == "젠득이"
    db.commit.assert_called_once()


def test_update_avatar_nickname_returns_404_when_ownership_not_found():
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = request_avatar_nickname_update(db)

    assert response.status_code == 404
    assert response.json() == OWNERSHIP_NOT_FOUND_RESPONSE
    db.commit.assert_not_called()


def test_update_avatar_nickname_queries_only_own_active_last_accessed_ownership():
    """다른 사용자·비활성·마지막 접근이 아닌 소유권이 조회에서 제외되는지 확인합니다."""
    db = Mock(spec=Session)
    db.scalar.return_value = make_cube_ownership()

    request_avatar_nickname_update(db, cube_ownership_id=12)

    statement = db.scalar.call_args.args[0]
    where_clause = str(
        statement.compile(compile_kwargs={"literal_binds": True})
    ).split("WHERE")[1]
    assert "cube_ownership.id = 12" in where_clause
    assert "cube_ownership.user_id = 1" in where_clause
    assert "cube_ownership.ownership_status = 'ACTIVE'" in where_clause
    assert "cube_ownership.is_last_accessed IS true" in where_clause
    assert "FOR UPDATE" in where_clause


def test_update_avatar_nickname_rolls_back_when_commit_fails():
    db = Mock(spec=Session)
    db.scalar.return_value = make_cube_ownership()
    db.commit.side_effect = RuntimeError("commit failed")

    response = request_avatar_nickname_update(db, raise_server_exceptions=False)

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_update_avatar_nickname_swagger_contract():
    operation = app.openapi()["paths"][
        "/api/v1/users/me/cube-ownerships/{cubeOwnershipId}/avatar-nickname"
    ]["patch"]

    assert set(operation["responses"]) == {"204", "400", "404"}
    assert "security" not in operation
