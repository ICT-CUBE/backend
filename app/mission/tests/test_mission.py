"""미션 도메인 API 테스트."""

from datetime import datetime, timedelta
from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.affinity.models import Affinity, Level
from app.core.enums import (
    LevelName,
    MissionProgressStatus,
    MissionTargetAction,
    MissionType,
    OwnershipStatus,
    RewardItemType,
)
from app.core.tests.conftest import api_client
from app.cube.models import CubeOwnership
from app.main import app
from app.mission.models import Mission, MissionProgress, RewardItem
from app.mission.progress import KOREA_TIMEZONE, increase_mission_progress

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


# --- 미션 보상 수령: POST /api/v1/users/me/missions/{missionId}/rewards ---

MISSION_NOT_FOUND_RESPONSE = {
    "code": "MISSION_NOT_FOUND",
    "message": "미션 정보를 찾을 수 없습니다.",
}
CUBE_AFFINITY_NOT_FOUND_RESPONSE = {
    "code": "CUBE_AFFINITY_NOT_FOUND",
    "message": "큐브 친밀도 정보를 찾을 수 없습니다.",
}
MISSION_NOT_COMPLETED_RESPONSE = {
    "code": "MISSION_NOT_COMPLETED",
    "message": "완료되지 않은 미션입니다.",
}
INTERNAL_SERVER_ERROR_RESPONSE = {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "서버 내부 오류가 발생했습니다.",
}
LEVELS = {
    1: Level(id=1, level=1, level_xp=0, level_name=LevelName.INTRO),
    2: Level(id=2, level=2, level_xp=100, level_name=LevelName.FRIEND),
    3: Level(id=3, level=3, level_xp=800, level_name=LevelName.CLOSE),
    4: Level(id=4, level=4, level_xp=2000, level_name=LevelName.SPECIAL),
}


def request_mission_reward(
    db: Mock,
    *,
    mission_id: int | str = 4,
    body: dict | None = None,
    raise_server_exceptions: bool = True,
):
    with api_client(db, raise_server_exceptions=raise_server_exceptions) as client:
        return client.post(
            f"/api/v1/users/me/missions/{mission_id}/rewards",
            json=body if body is not None else {"missionType": "DAILY"},
        )


def make_reward_mission(
    *,
    mission_type: MissionType = MissionType.DAILY,
    reward_item: RewardItem | None = None,
) -> Mission:
    mission = make_daily_mission(reward_item=reward_item)
    mission.mission_type = mission_type
    return mission


def make_progress(
    *,
    status: MissionProgressStatus = MissionProgressStatus.COMPLETED,
) -> MissionProgress:
    return MissionProgress(
        id=10,
        cube_ownership_id=1,
        mission_id=4,
        current_count=3,
        status=status,
        reward_claimed=status == MissionProgressStatus.REWARDED,
        claimed_at=None,
    )


def make_affinity(*, level: int = 1, current_xp: int = 90) -> Affinity:
    return Affinity(
        id=1,
        cube_ownership_id=1,
        level_id=LEVELS[level].id,
        current_xp=current_xp,
    )


def make_level_reward(*, reward_item_id: int, reward_level: int) -> RewardItem:
    reward_item = make_reward_item(
        reward_item_id=reward_item_id,
        name=f"{reward_level}레벨 보상",
        reward_type=RewardItemType.COMMENT_TYPE,
        reward_count=None,
    )
    reward_item.reward_level = reward_level
    return reward_item


def set_mission_reward_results(
    db: Mock,
    *,
    cube_ownership: CubeOwnership | None = None,
    mission: Mission | None = None,
    progress: MissionProgress | None = None,
    affinity: Affinity | None = None,
    current_level: Level | None = None,
    reached_level: Level | None = None,
    level_rewards: list[RewardItem] | None = None,
) -> list:
    """서비스가 조회하는 순서대로 결과를 지정하고 db.add 로 저장한 객체를 모읍니다."""
    db.scalar.side_effect = [
        cube_ownership,
        mission,
        progress,
        affinity,
        current_level,
        reached_level,
    ]
    db.scalars.return_value = level_rewards or []
    added: list = []
    db.add.side_effect = added.append
    return added


def set_point_reward_results(
    db: Mock,
    *,
    reward_count: int | None = 30,
    progress: MissionProgress | None = None,
    affinity: Affinity | None = None,
    reached_level: int = 1,
    level_rewards: list[RewardItem] | None = None,
) -> list:
    """친밀도 포인트 보상 미션을 수령하는 기본 조회 결과를 지정합니다."""
    affinity = affinity if affinity is not None else make_affinity()
    return set_mission_reward_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_reward_mission(
            reward_item=make_reward_item(reward_count=reward_count)
        ),
        progress=progress if progress is not None else make_progress(),
        affinity=affinity,
        current_level=LEVELS[
            next(key for key, lv in LEVELS.items() if lv.id == affinity.level_id)
        ],
        reached_level=LEVELS[reached_level],
        level_rewards=level_rewards,
    )


def test_create_mission_reward_grants_point_without_level_up() -> None:
    db = Mock(spec=Session)
    progress = make_progress()
    affinity = make_affinity(level=1, current_xp=40)
    added = set_point_reward_results(
        db,
        reward_count=30,
        progress=progress,
        affinity=affinity,
        reached_level=1,
    )

    response = request_mission_reward(db)

    assert response.status_code == 200
    assert response.json() == {"levelUp": None}
    assert [(row.cube_ownership_id, row.reward_item_id) for row in added] == [(1, 5)]
    assert affinity.current_xp == 70
    assert affinity.level_id == 1
    assert progress.status == MissionProgressStatus.REWARDED
    assert progress.reward_claimed is True
    assert progress.claimed_at is not None
    assert progress.claimed_at.tzinfo is None
    db.scalars.assert_not_called()
    db.commit.assert_called_once()


def test_create_mission_reward_grants_level_reward_when_level_up() -> None:
    db = Mock(spec=Session)
    affinity = make_affinity(level=1, current_xp=90)
    added = set_point_reward_results(
        db,
        reward_count=30,
        affinity=affinity,
        reached_level=2,
        level_rewards=[make_level_reward(reward_item_id=12, reward_level=2)],
    )

    response = request_mission_reward(db)

    assert response.status_code == 200
    assert response.json() == {"levelUp": {"level": 2, "levelName": "Friend"}}
    assert [row.reward_item_id for row in added] == [5, 12]
    assert affinity.current_xp == 120
    assert affinity.level_id == 2
    db.commit.assert_called_once()


def test_create_mission_reward_grants_every_passed_level_reward() -> None:
    db = Mock(spec=Session)
    affinity = make_affinity(level=1, current_xp=90)
    added = set_point_reward_results(
        db,
        reward_count=1000,
        affinity=affinity,
        reached_level=3,
        level_rewards=[
            make_level_reward(reward_item_id=12, reward_level=2),
            make_level_reward(reward_item_id=13, reward_level=3),
        ],
    )

    response = request_mission_reward(db)

    assert response.status_code == 200
    assert response.json() == {"levelUp": {"level": 3, "levelName": "Close"}}
    assert [row.reward_item_id for row in added] == [5, 12, 13]
    assert affinity.current_xp == 1090
    assert affinity.level_id == 3
    query = compiled_query(db.scalars.call_args)
    assert "reward_item.reward_level > 1" in query
    assert "reward_item.reward_level <= 3" in query
    assert "reward_item.deleted_at IS NULL" in query
    assert "ORDER BY reward_item.reward_level ASC, reward_item.id ASC" in query


def test_create_mission_reward_uses_same_time_for_all_rewards_and_progress() -> None:
    db = Mock(spec=Session)
    progress = make_progress()
    added = set_point_reward_results(
        db,
        progress=progress,
        reached_level=2,
        level_rewards=[make_level_reward(reward_item_id=12, reward_level=2)],
    )

    request_mission_reward(db)

    assert {row.acquired_at for row in added} == {progress.claimed_at}


def test_create_mission_reward_keeps_max_level_and_accumulates_xp() -> None:
    db = Mock(spec=Session)
    affinity = make_affinity(level=4, current_xp=2500)
    set_point_reward_results(db, affinity=affinity, reached_level=4)

    response = request_mission_reward(db)

    assert response.status_code == 200
    assert response.json() == {"levelUp": None}
    assert affinity.current_xp == 2530
    assert affinity.level_id == 4
    db.scalars.assert_not_called()


def test_create_mission_reward_grants_non_point_reward_only() -> None:
    db = Mock(spec=Session)
    progress = make_progress()
    added = set_mission_reward_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_reward_mission(
            reward_item=make_reward_item(
                reward_item_id=7,
                name="배지",
                reward_type=RewardItemType.BADGE,
                reward_count=None,
            )
        ),
        progress=progress,
    )

    response = request_mission_reward(db)

    assert response.status_code == 200
    assert response.json() == {"levelUp": None}
    assert [row.reward_item_id for row in added] == [7]
    assert progress.status == MissionProgressStatus.REWARDED
    # 포인트가 아니면 친밀도와 레벨을 조회하지 않습니다.
    assert db.scalar.call_count == 3
    db.scalars.assert_not_called()
    db.commit.assert_called_once()


def test_create_mission_reward_grants_again_when_already_rewarded() -> None:
    db = Mock(spec=Session)
    progress = make_progress(status=MissionProgressStatus.REWARDED)
    added = set_point_reward_results(db, progress=progress)

    response = request_mission_reward(db)

    assert response.status_code == 200
    assert [row.reward_item_id for row in added] == [5]
    assert progress.status == MissionProgressStatus.REWARDED
    assert progress.claimed_at is not None
    db.commit.assert_called_once()


def test_create_mission_reward_accepts_event_mission() -> None:
    db = Mock(spec=Session)
    set_mission_reward_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_reward_mission(
            mission_type=MissionType.EVENT,
            reward_item=make_reward_item(reward_type=RewardItemType.BADGE),
        ),
        progress=make_progress(),
    )

    response = request_mission_reward(db, body={"missionType": "EVENT"})

    assert response.status_code == 200
    query = compiled_query(db.scalar.call_args_list[1])
    assert "mission.mission_type = 'EVENT'" in query


def test_create_mission_reward_returns_404_when_cube_ownership_not_found() -> None:
    db = Mock(spec=Session)
    set_mission_reward_results(db, cube_ownership=None)

    response = request_mission_reward(db)

    assert response.status_code == 404
    assert response.json() == CUBE_OWNERSHIP_NOT_FOUND_RESPONSE
    assert db.scalar.call_count == 1
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_mission_reward_returns_404_when_mission_not_found() -> None:
    db = Mock(spec=Session)
    set_mission_reward_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=None,
    )

    response = request_mission_reward(db)

    assert response.status_code == 404
    assert response.json() == MISSION_NOT_FOUND_RESPONSE
    assert db.scalar.call_count == 2
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_mission_reward_returns_404_when_affinity_not_found() -> None:
    db = Mock(spec=Session)
    set_mission_reward_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_reward_mission(),
        progress=make_progress(),
        affinity=None,
    )

    response = request_mission_reward(db)

    assert response.status_code == 404
    assert response.json() == CUBE_AFFINITY_NOT_FOUND_RESPONSE
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_mission_reward_returns_409_when_mission_in_progress() -> None:
    db = Mock(spec=Session)
    progress = make_progress(status=MissionProgressStatus.IN_PROGRESS)
    set_mission_reward_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_reward_mission(),
        progress=progress,
    )

    response = request_mission_reward(db)

    assert response.status_code == 409
    assert response.json() == MISSION_NOT_COMPLETED_RESPONSE
    assert progress.status == MissionProgressStatus.IN_PROGRESS
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_mission_reward_returns_409_when_progress_not_found() -> None:
    db = Mock(spec=Session)
    set_mission_reward_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_reward_mission(),
        progress=None,
    )

    response = request_mission_reward(db)

    assert response.status_code == 409
    assert response.json() == MISSION_NOT_COMPLETED_RESPONSE
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_mission_reward_returns_500_when_point_reward_count_is_null() -> None:
    db = Mock(spec=Session)
    set_point_reward_results(db, reward_count=None)

    response = request_mission_reward(db, raise_server_exceptions=False)

    assert response.status_code == 500
    assert response.json() == INTERNAL_SERVER_ERROR_RESPONSE
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_mission_reward_returns_500_when_point_reward_count_is_zero() -> None:
    db = Mock(spec=Session)
    set_point_reward_results(db, reward_count=0)

    response = request_mission_reward(db, raise_server_exceptions=False)

    assert response.status_code == 500
    assert response.json() == INTERNAL_SERVER_ERROR_RESPONSE
    db.commit.assert_not_called()


def test_create_mission_reward_returns_500_when_current_level_not_found() -> None:
    db = Mock(spec=Session)
    set_mission_reward_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_reward_mission(),
        progress=make_progress(),
        affinity=make_affinity(),
        current_level=None,
        reached_level=LEVELS[1],
    )

    response = request_mission_reward(db, raise_server_exceptions=False)

    assert response.status_code == 500
    assert response.json() == INTERNAL_SERVER_ERROR_RESPONSE
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_mission_reward_returns_500_when_reached_level_not_found() -> None:
    db = Mock(spec=Session)
    set_mission_reward_results(
        db,
        cube_ownership=make_cube_ownership(),
        mission=make_reward_mission(),
        progress=make_progress(),
        affinity=make_affinity(),
        current_level=LEVELS[1],
        reached_level=None,
    )

    response = request_mission_reward(db, raise_server_exceptions=False)

    assert response.status_code == 500
    assert response.json() == INTERNAL_SERVER_ERROR_RESPONSE
    db.commit.assert_not_called()


def test_create_mission_reward_queries_active_last_accessed_ownership() -> None:
    db = Mock(spec=Session)
    set_point_reward_results(db)

    request_mission_reward(db)

    query = compiled_query(db.scalar.call_args_list[0])
    assert "cube_ownership.user_id = 1" in query
    assert "cube_ownership.ownership_status = 'ACTIVE'" in query
    assert "cube_ownership.is_last_accessed IS true" in query


def test_create_mission_reward_queries_active_mission_of_requested_type() -> None:
    db = Mock(spec=Session)
    set_point_reward_results(db)

    request_mission_reward(db, mission_id=4)

    query = compiled_query(db.scalar.call_args_list[1])
    assert "JOIN reward_item ON reward_item.id = mission.reward_item_id" in query
    assert "mission.id = 4" in query
    assert "mission.mission_type = 'DAILY'" in query
    assert "mission.is_active IS true" in query
    assert "mission.deleted_at IS NULL" in query
    assert "reward_item.deleted_at IS NULL" in query


def test_create_mission_reward_queries_progress_of_current_ownership() -> None:
    db = Mock(spec=Session)
    set_point_reward_results(db)

    request_mission_reward(db)

    query = compiled_query(db.scalar.call_args_list[2])
    assert "mission_progress.cube_ownership_id = 1" in query
    assert "mission_progress.mission_id = 4" in query


def test_create_mission_reward_locks_affinity_and_finds_reached_level() -> None:
    db = Mock(spec=Session)
    set_point_reward_results(
        db,
        reward_count=30,
        affinity=make_affinity(current_xp=90),
        reached_level=2,
    )

    request_mission_reward(db)

    affinity_query = compiled_query(db.scalar.call_args_list[3])
    assert "affinity.cube_ownership_id = 1" in affinity_query
    assert "FOR UPDATE" in affinity_query
    level_query = compiled_query(db.scalar.call_args_list[5])
    assert "level.level_xp <= 120" in level_query
    assert "ORDER BY level.level DESC" in level_query


def test_create_mission_reward_allows_minimum_mission_id() -> None:
    db = Mock(spec=Session)
    set_point_reward_results(db)

    response = request_mission_reward(db, mission_id=1)

    assert response.status_code == 200


def test_create_mission_reward_returns_400_when_mission_id_is_zero() -> None:
    db = Mock(spec=Session)

    response = request_mission_reward(db, mission_id=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_create_mission_reward_returns_400_when_mission_id_is_not_number() -> None:
    db = Mock(spec=Session)

    response = request_mission_reward(db, mission_id="abc")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_create_mission_reward_returns_400_when_mission_type_is_missing() -> None:
    db = Mock(spec=Session)

    response = request_mission_reward(db, body={})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_create_mission_reward_returns_400_for_unsupported_mission_type() -> None:
    db = Mock(spec=Session)

    response = request_mission_reward(db, body={"missionType": "WEEKLY"})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_create_mission_reward_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    set_point_reward_results(db)
    db.commit.side_effect = RuntimeError("db failed")

    response = request_mission_reward(db, raise_server_exceptions=False)

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_create_mission_reward_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/missions/{missionId}/rewards"
    ]["post"]

    assert set(operation["responses"]) == {"200", "404", "409"}
    assert {parameter["name"] for parameter in operation["parameters"]} == {
        "missionId",
    }
    assert "requestBody" in operation
    assert operation["tags"] == ["mission"]
    assert operation["security"] == [{"HTTPBearer": []}]


# --- 미션 진행도 반영: app/mission/progress.py increase_mission_progress ---


def kst_now() -> datetime:
    return datetime.now(KOREA_TIMEZONE).replace(tzinfo=None, microsecond=0)


def make_action_mission(
    *,
    mission_id: int = 2,
    mission_type: MissionType = MissionType.DAILY,
    target_action: MissionTargetAction = MissionTargetAction.CONVERSATION,
    target_count: int = 3,
) -> Mission:
    return Mission(
        id=mission_id,
        mission_type=mission_type,
        target_action=target_action,
        target_count=target_count,
        is_active=True,
        deleted_at=None,
    )


def make_action_progress(
    *,
    mission_id: int = 2,
    current_count: int = 0,
    status: MissionProgressStatus = MissionProgressStatus.IN_PROGRESS,
    updated_at: datetime | None = None,
) -> MissionProgress:
    rewarded = status == MissionProgressStatus.REWARDED
    completed = status != MissionProgressStatus.IN_PROGRESS
    return MissionProgress(
        id=20 + mission_id,
        cube_ownership_id=1,
        mission_id=mission_id,
        current_count=current_count,
        status=status,
        reward_claimed=rewarded,
        completed_at=kst_now() if completed else None,
        claimed_at=kst_now() if rewarded else None,
        updated_at=updated_at if updated_at is not None else kst_now(),
    )


def set_progress_results(
    db: Mock,
    *,
    cube_ownership_id: int | None = 1,
    missions: list[Mission] | None = None,
    progresses: list[MissionProgress | None] | None = None,
) -> list:
    """조회 순서대로 소유권 id, 미션 목록, 미션별 진행 행을 지정합니다."""
    db.scalar.side_effect = [cube_ownership_id, *(progresses or [])]
    db.scalars.return_value.all.return_value = missions or []
    added: list = []
    db.add.side_effect = added.append
    return added


def run_increase_mission_progress(
    db: Mock,
    *,
    target_action: MissionTargetAction = MissionTargetAction.CONVERSATION,
) -> None:
    increase_mission_progress(db=db, current_user_id=1, target_action=target_action)


def test_increase_mission_progress_skips_when_cube_ownership_not_found() -> None:
    db = Mock(spec=Session)
    added = set_progress_results(db, cube_ownership_id=None)

    run_increase_mission_progress(db)

    assert db.scalar.call_count == 1
    db.scalars.assert_not_called()
    assert added == []


def test_increase_mission_progress_creates_progress_when_no_history() -> None:
    db = Mock(spec=Session)
    added = set_progress_results(
        db,
        missions=[make_action_mission(target_count=3)],
        progresses=[None],
    )

    run_increase_mission_progress(db)

    assert len(added) == 1
    progress = added[0]
    assert (progress.cube_ownership_id, progress.mission_id) == (1, 2)
    assert progress.current_count == 1
    assert progress.status == MissionProgressStatus.IN_PROGRESS
    assert progress.reward_claimed is False
    assert progress.completed_at is None


def test_increase_mission_progress_completes_new_progress_when_target_is_one() -> None:
    db = Mock(spec=Session)
    added = set_progress_results(
        db,
        missions=[
            make_action_mission(
                mission_id=3,
                target_action=MissionTargetAction.ALBUM_PLAY,
                target_count=1,
            )
        ],
        progresses=[None],
    )

    run_increase_mission_progress(db, target_action=MissionTargetAction.ALBUM_PLAY)

    progress = added[0]
    assert progress.current_count == 1
    assert progress.status == MissionProgressStatus.COMPLETED
    assert progress.completed_at is not None
    assert progress.completed_at.tzinfo is None


def test_increase_mission_progress_increments_in_progress_count() -> None:
    db = Mock(spec=Session)
    progress = make_action_progress(current_count=1)
    added = set_progress_results(
        db,
        missions=[make_action_mission(target_count=3)],
        progresses=[progress],
    )

    run_increase_mission_progress(db)

    assert progress.current_count == 2
    assert progress.status == MissionProgressStatus.IN_PROGRESS
    assert progress.completed_at is None
    assert added == []


def test_increase_mission_progress_completes_when_reaching_target_count() -> None:
    db = Mock(spec=Session)
    progress = make_action_progress(current_count=2)
    set_progress_results(
        db,
        missions=[make_action_mission(target_count=3)],
        progresses=[progress],
    )

    run_increase_mission_progress(db)

    assert progress.current_count == 3
    assert progress.status == MissionProgressStatus.COMPLETED
    assert progress.completed_at is not None


def test_increase_mission_progress_keeps_completed_progress() -> None:
    db = Mock(spec=Session)
    progress = make_action_progress(
        current_count=3,
        status=MissionProgressStatus.COMPLETED,
    )
    completed_at = progress.completed_at
    set_progress_results(
        db,
        missions=[make_action_mission(target_count=3)],
        progresses=[progress],
    )

    run_increase_mission_progress(db)

    assert progress.current_count == 3
    assert progress.status == MissionProgressStatus.COMPLETED
    assert progress.completed_at == completed_at


def test_increase_mission_progress_keeps_rewarded_progress() -> None:
    db = Mock(spec=Session)
    progress = make_action_progress(
        current_count=3,
        status=MissionProgressStatus.REWARDED,
    )
    set_progress_results(
        db,
        missions=[make_action_mission(target_count=3)],
        progresses=[progress],
    )

    run_increase_mission_progress(db)

    assert progress.current_count == 3
    assert progress.status == MissionProgressStatus.REWARDED
    assert progress.reward_claimed is True


def test_increase_mission_progress_resets_daily_progress_of_previous_day() -> None:
    db = Mock(spec=Session)
    progress = make_action_progress(
        current_count=3,
        status=MissionProgressStatus.REWARDED,
        updated_at=kst_now() - timedelta(days=1),
    )
    set_progress_results(
        db,
        missions=[make_action_mission(target_count=3)],
        progresses=[progress],
    )

    run_increase_mission_progress(db)

    assert progress.current_count == 1
    assert progress.status == MissionProgressStatus.IN_PROGRESS
    assert progress.reward_claimed is False
    assert progress.completed_at is None
    assert progress.claimed_at is None


def test_increase_mission_progress_resets_and_completes_daily_target_one() -> None:
    db = Mock(spec=Session)
    progress = make_action_progress(
        mission_id=1,
        current_count=1,
        status=MissionProgressStatus.COMPLETED,
        updated_at=kst_now() - timedelta(days=3),
    )
    set_progress_results(
        db,
        missions=[
            make_action_mission(
                mission_id=1,
                target_action=MissionTargetAction.HOME_VIEW,
                target_count=1,
            )
        ],
        progresses=[progress],
    )

    run_increase_mission_progress(db, target_action=MissionTargetAction.HOME_VIEW)

    assert progress.current_count == 1
    assert progress.status == MissionProgressStatus.COMPLETED
    assert progress.reward_claimed is False
    assert progress.completed_at.date() == kst_now().date()


def test_increase_mission_progress_does_not_reset_event_progress() -> None:
    db = Mock(spec=Session)
    progress = make_action_progress(
        mission_id=7,
        current_count=5,
        status=MissionProgressStatus.REWARDED,
        updated_at=kst_now() - timedelta(days=1),
    )
    set_progress_results(
        db,
        missions=[
            make_action_mission(
                mission_id=7,
                mission_type=MissionType.EVENT,
                target_action=MissionTargetAction.PLAY_MUSIC_VIDEO,
                target_count=5,
            )
        ],
        progresses=[progress],
    )

    run_increase_mission_progress(
        db,
        target_action=MissionTargetAction.PLAY_MUSIC_VIDEO,
    )

    assert progress.current_count == 5
    assert progress.status == MissionProgressStatus.REWARDED


def test_increase_mission_progress_updates_every_mission_of_action() -> None:
    db = Mock(spec=Session)
    first = make_action_progress(mission_id=2, current_count=0)
    added = set_progress_results(
        db,
        missions=[
            make_action_mission(mission_id=2, target_count=3),
            make_action_mission(mission_id=8, target_count=1),
        ],
        progresses=[first, None],
    )

    run_increase_mission_progress(db)

    assert first.current_count == 1
    assert [(row.mission_id, row.status) for row in added] == [
        (8, MissionProgressStatus.COMPLETED)
    ]


def test_increase_mission_progress_does_nothing_when_no_matching_mission() -> None:
    db = Mock(spec=Session)
    added = set_progress_results(db, missions=[])

    run_increase_mission_progress(db)

    assert db.scalar.call_count == 1
    assert added == []


def test_increase_mission_progress_does_not_commit() -> None:
    db = Mock(spec=Session)
    set_progress_results(db, missions=[make_action_mission()], progresses=[None])

    run_increase_mission_progress(db)

    db.commit.assert_not_called()
    db.rollback.assert_not_called()


def test_increase_mission_progress_queries_active_last_accessed_ownership() -> None:
    db = Mock(spec=Session)
    set_progress_results(db)

    run_increase_mission_progress(db)

    query = compiled_query(db.scalar.call_args_list[0])
    assert "cube_ownership.user_id = 1" in query
    assert "cube_ownership.ownership_status = 'ACTIVE'" in query
    assert "cube_ownership.is_last_accessed IS true" in query


def test_increase_mission_progress_queries_active_missions_in_period() -> None:
    db = Mock(spec=Session)
    set_progress_results(db)

    run_increase_mission_progress(db, target_action=MissionTargetAction.OPEN_GALLERY)

    query = compiled_query(db.scalars.call_args)
    assert "mission.target_action = 'OPEN_GALLERY'" in query
    assert "mission.is_active IS true" in query
    assert "mission.deleted_at IS NULL" in query
    assert "mission.start_at IS NULL OR mission.start_at <=" in query
    assert "mission.end_at IS NULL OR mission.end_at >=" in query


def test_increase_mission_progress_locks_progress_row() -> None:
    db = Mock(spec=Session)
    set_progress_results(
        db,
        missions=[make_action_mission(mission_id=2)],
        progresses=[None],
    )

    run_increase_mission_progress(db)

    query = compiled_query(db.scalar.call_args_list[1])
    assert "mission_progress.cube_ownership_id = 1" in query
    assert "mission_progress.mission_id = 2" in query
    assert "FOR UPDATE" in query
