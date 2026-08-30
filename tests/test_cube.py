"""큐브 도메인 API 테스트."""

from unittest.mock import Mock, patch

from sqlalchemy.orm import Session

from app.main import app
from app.models.account import CubeVerification
from app.models.cube import Affinity, Cube, CubeOwnership, Level
from app.models.enums import (
    CubeStatus,
    LevelName,
    OwnershipStatus,
    RewardItemType,
)
from app.models.reward import RewardItem, UserReward
from tests.conftest import api_client


def request_cube_verification(
    db: Mock,
    *,
    body: dict[str, int | str] | None = None,
    raise_server_exceptions: bool = True,
    mint: Mock | None = None,
):
    """인증 API를 호출합니다. NFT 발행은 기본적으로 Mock으로 대체합니다."""
    with (
        patch("app.services.cube.mint_cube_nft", mint or Mock()),
        api_client(db, raise_server_exceptions=raise_server_exceptions) as client,
    ):
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


def make_first_level() -> Level:
    return Level(id=7, level=1, level_name=LevelName.INTRO, level_xp=0)


def make_first_level_rewards() -> list[RewardItem]:
    """목데이터와 같은 1레벨 해금 보상 두 건을 만듭니다."""
    return [
        RewardItem(
            id=6,
            name="일일 대화 가능 횟수",
            reward_type=RewardItemType.CONVERSATION_COUNT,
            description="하루에 대화 제한 5회",
            reward_count=5,
            reward_level=1,
            deleted_at=None,
        ),
        RewardItem(
            id=10,
            name="멘트 종류",
            reward_type=RewardItemType.COMMENT_TYPE,
            description="기본 인사",
            reward_count=None,
            reward_level=1,
            deleted_at=None,
        ),
    ]


def assign_created_ids(added_objects: list[object]):
    def _assign_ids() -> None:
        for item in added_objects:
            if isinstance(item, CubeVerification) and item.id is None:
                item.id = 15
            if isinstance(item, CubeOwnership) and item.id is None:
                item.id = 4

    return _assign_ids


def set_verification_results(
    db: Mock,
    *,
    cube: Cube | None,
    existing_ownership_id: int | None = None,
    level: Level | None = None,
    reward_items: list[RewardItem] | None = None,
) -> list[object]:
    """서비스가 db.scalar / db.scalars 로 조회한 결과를 지정하고 저장 객체를 모읍니다."""
    db.scalar.side_effect = [cube, existing_ownership_id, level]
    db.scalars.return_value = reward_items or []
    added_objects: list[object] = []
    db.add.side_effect = added_objects.append
    db.flush.side_effect = assign_created_ids(added_objects)
    return added_objects


def test_create_cube_verification_success_creates_ownership():
    db = Mock(spec=Session)
    added_objects = set_verification_results(
        db,
        cube=make_cube(),
        level=make_first_level(),
    )

    response = request_cube_verification(db)

    assert response.status_code == 201
    assert response.json() == {"cubeOwnershipId": 4}
    assert any(isinstance(item, CubeVerification) for item in added_objects)
    assert any(isinstance(item, CubeOwnership) for item in added_objects)
    db.execute.assert_called_once()
    db.commit.assert_called_once()


def test_create_cube_verification_success_creates_first_level_affinity():
    db = Mock(spec=Session)
    added_objects = set_verification_results(
        db,
        cube=make_cube(),
        level=make_first_level(),
    )

    response = request_cube_verification(db)

    assert response.status_code == 201
    affinities = [item for item in added_objects if isinstance(item, Affinity)]
    assert len(affinities) == 1
    affinity = affinities[0]
    assert affinity.cube_ownership_id == 4
    assert affinity.level_id == 7
    assert affinity.current_xp == 0
    db.commit.assert_called_once()


def test_create_cube_verification_queries_first_level_row():
    db = Mock(spec=Session)
    set_verification_results(db, cube=make_cube(), level=make_first_level())

    request_cube_verification(db)

    query = str(
        db.scalar.call_args.args[0].compile(compile_kwargs={"literal_binds": True})
    )
    assert "FROM level" in query
    assert "level.level = 1" in query


def test_create_cube_verification_rolls_back_when_first_level_is_missing():
    db = Mock(spec=Session)
    added_objects = set_verification_results(db, cube=make_cube(), level=None)

    response = request_cube_verification(db, raise_server_exceptions=False)

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "서버 내부 오류가 발생했습니다.",
    }
    assert not any(isinstance(item, Affinity) for item in added_objects)
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_create_cube_verification_rolls_back_when_commit_fails():
    db = Mock(spec=Session)
    set_verification_results(db, cube=make_cube(), level=make_first_level())
    db.commit.side_effect = RuntimeError("db failed")

    response = request_cube_verification(db, raise_server_exceptions=False)

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_create_cube_verification_success_grants_first_level_rewards():
    db = Mock(spec=Session)
    added_objects = set_verification_results(
        db,
        cube=make_cube(),
        level=make_first_level(),
        reward_items=make_first_level_rewards(),
    )

    response = request_cube_verification(db)

    assert response.status_code == 201
    user_rewards = [item for item in added_objects if isinstance(item, UserReward)]
    assert len(user_rewards) == 2
    assert [reward.reward_item_id for reward in user_rewards] == [6, 10]
    assert all(reward.cube_ownership_id == 4 for reward in user_rewards)
    db.commit.assert_called_once()


def test_create_cube_verification_uses_same_acquired_at_for_rewards():
    db = Mock(spec=Session)
    added_objects = set_verification_results(
        db,
        cube=make_cube(),
        level=make_first_level(),
        reward_items=make_first_level_rewards(),
    )

    request_cube_verification(db)

    cube_ownership = next(
        item for item in added_objects if isinstance(item, CubeOwnership)
    )
    user_rewards = [item for item in added_objects if isinstance(item, UserReward)]
    assert all(
        reward.acquired_at == cube_ownership.acquired_at for reward in user_rewards
    )


def test_create_cube_verification_queries_only_first_level_rewards():
    db = Mock(spec=Session)
    set_verification_results(
        db,
        cube=make_cube(),
        level=make_first_level(),
        reward_items=make_first_level_rewards(),
    )

    request_cube_verification(db)

    query = str(
        db.scalars.call_args.args[0].compile(compile_kwargs={"literal_binds": True})
    )
    assert "reward_item.reward_level = 1" in query
    assert "reward_item.deleted_at IS NULL" in query
    assert "ORDER BY reward_item.id ASC" in query


def test_create_cube_verification_rolls_back_when_reward_query_fails():
    db = Mock(spec=Session)
    added_objects = set_verification_results(
        db,
        cube=make_cube(),
        level=make_first_level(),
    )
    db.scalars.side_effect = RuntimeError("db failed")

    response = request_cube_verification(db, raise_server_exceptions=False)

    assert response.status_code == 500
    assert not any(isinstance(item, UserReward) for item in added_objects)
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_create_cube_verification_requests_mint_after_commit():
    db = Mock(spec=Session)
    set_verification_results(
        db,
        cube=make_cube(),
        level=make_first_level(),
        reward_items=make_first_level_rewards(),
    )
    mint = Mock()

    response = request_cube_verification(db, mint=mint)

    assert response.status_code == 201
    mint.assert_called_once()
    assert mint.call_args.kwargs["user_id"] == 1
    assert mint.call_args.kwargs["cube_id"] == 2
    assert mint.call_args.kwargs["serial_number"] == "ARZ-CUBE-0002"
    db.commit.assert_called_once()


def test_create_cube_verification_does_not_request_mint_when_code_invalid():
    db = Mock(spec=Session)
    set_verification_results(db, cube=make_cube(), level=make_first_level())
    mint = Mock()

    response = request_cube_verification(
        db,
        body={"cubeId": 2, "ownershipCode": "9999"},
        mint=mint,
    )

    assert response.status_code == 400
    mint.assert_not_called()


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
    assert not any(isinstance(item, Affinity) for item in added_objects)
    assert not any(isinstance(item, CubeOwnership) for item in added_objects)
    assert not any(isinstance(item, UserReward) for item in added_objects)
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
    assert operation["security"] == [{"HTTPBearer": []}]
