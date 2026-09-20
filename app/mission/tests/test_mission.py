"""미션 도메인 API 테스트."""

from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.core.enums import (
    MissionTargetAction,
    MissionType,
    OwnershipStatus,
    RewardItemType,
)
from app.core.tests.conftest import api_client
from app.cube.models import CubeOwnership
from app.main import app
from app.mission.models import Mission, RewardItem

INVALID_REQUEST_RESPONSE = {
    "code": "INVALID_REQUEST",
    "message": "요청값이 올바르지 않습니다.",
}

# --- 데일리 미션 상세 조회: GET /api/v1/users/me/daily-missions/{missionId} ---

CUBE_OWNERSHIP_NOT_FOUND_RESPONSE = {
    "code": "CUBE_OWNERSHIP_NOT_FOUND",
    "message": "큐브 소유권 정보를 찾을 수 없습니다.",
}
DAILY_MISSION_NOT_FOUND_RESPONSE = {
    "code": "DAILY_MISSION_NOT_FOUND",
    "message": "데일리 미션 정보를 찾을 수 없습니다.",
}


def request_daily_mission(db: Mock, *, mission_id: int | str = 4):
    with api_client(db) as client:
        return client.get(f"/api/v1/users/me/daily-missions/{mission_id}")


def make_cube_ownership() -> CubeOwnership:
    return CubeOwnership(
        id=1,
        user_id=1,
        ownership_status=OwnershipStatus.ACTIVE,
        is_last_accessed=True,
    )


def make_reward_item(
    *,
    reward_item_id: int = 5,
    name: str = "친밀도 포인트",
    reward_type: RewardItemType = RewardItemType.AFFINITY_POINT,
    reward_count: int | None = 30,
) -> RewardItem:
    return RewardItem(
        id=reward_item_id,
        name=name,
        reward_type=reward_type,
        reward_count=reward_count,
        deleted_at=None,
    )


def make_daily_mission(
    *,
    mission_id: int = 4,
    title: str = "아바타 현실 소환하기",
    mission_info: str | None = (
        "아바타를 현실에 소환해 예절샷을 남겨보세요. "
        "AR 카메라로 3회 촬영하면 미션이 완료돼요!"
    ),
    reward_item: RewardItem | None = None,
) -> Mission:
    return Mission(
        id=mission_id,
        mission_type=MissionType.DAILY,
        title=title,
        mission_info=mission_info,
        target_action=MissionTargetAction.SUMMON_AVATAR,
        target_count=3,
        is_active=True,
        deleted_at=None,
        reward_item=reward_item if reward_item is not None else make_reward_item(),
    )


def set_daily_mission_results(
    db: Mock,
    *,
    cube_ownership: CubeOwnership | None = None,
    mission: Mission | None = None,
) -> None:
    """서비스가 조회하는 순서대로 큐브 소유권과 데일리 미션을 지정합니다."""
    db.scalar.side_effect = [cube_ownership, mission]


def compiled_query(call) -> str:
    return str(call.args[0].compile(compile_kwargs={"literal_binds": True}))


def test_read_daily_mission_returns_mission_with_reward_item() -> None:
    db = Mock(spec=Session)
    set_daily_mission_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_daily_mission(),
    )

    response = request_daily_mission(db)

    assert response.status_code == 200
    assert response.json() == {
        "mission": {
            "id": 4,
            "missionType": "DAILY",
            "title": "아바타 현실 소환하기",
            "missionInfo": (
                "아바타를 현실에 소환해 예절샷을 남겨보세요. "
                "AR 카메라로 3회 촬영하면 미션이 완료돼요!"
            ),
            "rewardItem": {
                "id": 5,
                "name": "친밀도 포인트",
                "rewardType": "AFFINITY_POINT",
                "rewardCount": 30,
            },
        }
    }
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_read_daily_mission_does_not_expose_target_action() -> None:
    db = Mock(spec=Session)
    set_daily_mission_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_daily_mission(),
    )

    response = request_daily_mission(db)

    assert response.status_code == 200
    assert "targetAction" not in response.json()["mission"]
    assert "targetCount" not in response.json()["mission"]


def test_read_daily_mission_returns_null_mission_info() -> None:
    db = Mock(spec=Session)
    set_daily_mission_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_daily_mission(mission_info=None),
    )

    response = request_daily_mission(db)

    assert response.status_code == 200
    assert response.json()["mission"]["missionInfo"] is None


def test_read_daily_mission_returns_null_reward_count() -> None:
    db = Mock(spec=Session)
    set_daily_mission_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_daily_mission(
            reward_item=make_reward_item(
                name="첫 대화 배지",
                reward_type=RewardItemType.BADGE,
                reward_count=None,
            )
        ),
    )

    response = request_daily_mission(db)

    assert response.status_code == 200
    assert response.json()["mission"]["rewardItem"] == {
        "id": 5,
        "name": "첫 대화 배지",
        "rewardType": "BADGE",
        "rewardCount": None,
    }


def test_read_daily_mission_returns_404_when_cube_ownership_not_found() -> None:
    db = Mock(spec=Session)
    set_daily_mission_results(db, cube_ownership=None)

    response = request_daily_mission(db)

    assert response.status_code == 404
    assert response.json() == CUBE_OWNERSHIP_NOT_FOUND_RESPONSE
    assert db.scalar.call_count == 1


def test_read_daily_mission_returns_404_when_daily_mission_not_found() -> None:
    db = Mock(spec=Session)
    set_daily_mission_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=None,
    )

    response = request_daily_mission(db)

    assert response.status_code == 404
    assert response.json() == DAILY_MISSION_NOT_FOUND_RESPONSE
    db.commit.assert_not_called()


def test_read_daily_mission_queries_active_last_accessed_ownership() -> None:
    db = Mock(spec=Session)
    set_daily_mission_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_daily_mission(),
    )

    request_daily_mission(db)

    query = compiled_query(db.scalar.call_args_list[0])
    assert "cube_ownership.user_id = 1" in query
    assert "cube_ownership.ownership_status = 'ACTIVE'" in query
    assert "cube_ownership.is_last_accessed IS true" in query


def test_read_daily_mission_queries_only_active_daily_mission() -> None:
    db = Mock(spec=Session)
    set_daily_mission_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_daily_mission(),
    )

    request_daily_mission(db, mission_id=4)

    query = compiled_query(db.scalar.call_args_list[1])
    assert "mission.id = 4" in query
    assert "mission.mission_type = 'DAILY'" in query
    assert "mission.is_active IS true" in query
    assert "mission.deleted_at IS NULL" in query


def test_read_daily_mission_excludes_deleted_reward_item() -> None:
    db = Mock(spec=Session)
    set_daily_mission_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_daily_mission(),
    )

    request_daily_mission(db)

    query = compiled_query(db.scalar.call_args_list[1])
    assert "JOIN reward_item ON reward_item.id = mission.reward_item_id" in query
    assert "reward_item.deleted_at IS NULL" in query


def test_read_daily_mission_does_not_filter_by_mission_progress() -> None:
    db = Mock(spec=Session)
    set_daily_mission_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_daily_mission(),
    )

    response = request_daily_mission(db)

    assert response.status_code == 200
    assert "mission_progress" not in compiled_query(db.scalar.call_args_list[1])
    assert db.scalar.call_count == 2


def test_read_daily_mission_allows_minimum_mission_id() -> None:
    db = Mock(spec=Session)
    set_daily_mission_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_daily_mission(mission_id=1),
    )

    response = request_daily_mission(db, mission_id=1)

    assert response.status_code == 200
    assert response.json()["mission"]["id"] == 1


def test_read_daily_mission_returns_400_when_mission_id_is_zero() -> None:
    db = Mock(spec=Session)

    response = request_daily_mission(db, mission_id=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_read_daily_mission_returns_400_when_mission_id_is_not_number() -> None:
    db = Mock(spec=Session)

    response = request_daily_mission(db, mission_id="abc")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_read_daily_mission_swagger_contract() -> None:
    operation = app.openapi()["paths"]["/api/v1/users/me/daily-missions/{missionId}"][
        "get"
    ]

    assert set(operation["responses"]) == {"200", "404"}
    assert {parameter["name"] for parameter in operation["parameters"]} == {
        "missionId",
    }
    assert operation["tags"] == ["mission"]
    assert operation["security"] == [{"HTTPBearer": []}]
