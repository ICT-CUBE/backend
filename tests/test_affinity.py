"""친밀도 도메인 API 테스트."""

from datetime import datetime
from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.main import app
from app.models.cube import Affinity, CubeOwnership, Level
from app.models.enums import (
    LevelName,
    MissionProgressStatus,
    MissionTargetAction,
    MissionType,
    OwnershipStatus,
    RewardItemType,
)
from app.models.reward import Mission, MissionProgress, RewardItem
from tests.conftest import api_client

OWNERSHIP_NOT_FOUND_RESPONSE = {
    "code": "CUBE_OWNERSHIP_NOT_FOUND",
    "message": "큐브 소유권 정보를 찾을 수 없습니다.",
}
AFFINITY_NOT_FOUND_RESPONSE = {
    "code": "CUBE_AFFINITY_NOT_FOUND",
    "message": "큐브 친밀도 정보를 찾을 수 없습니다.",
}


def request_affinity(db: Mock):
    with api_client(db) as client:
        return client.get("/api/v1/users/me/affinity")


def make_level(
    *,
    level_id: int,
    level: int,
    level_name: LevelName,
    level_xp: int,
) -> Level:
    return Level(
        id=level_id,
        level=level,
        level_name=level_name,
        level_xp=level_xp,
    )


def make_levels() -> list[Level]:
    return [
        make_level(level_id=1, level=1, level_name=LevelName.INTRO, level_xp=0),
        make_level(level_id=2, level=2, level_name=LevelName.FRIEND, level_xp=100),
        make_level(level_id=3, level=3, level_name=LevelName.CLOSE, level_xp=800),
        make_level(level_id=4, level=4, level_name=LevelName.SPECIAL, level_xp=2000),
    ]


def make_ownership(
    *,
    current_xp: int = 1245,
    current_level: Level | None = None,
    with_affinity: bool = True,
) -> CubeOwnership:
    level = current_level or make_level(
        level_id=3,
        level=3,
        level_name=LevelName.CLOSE,
        level_xp=800,
    )
    affinity = (
        Affinity(id=1, current_xp=current_xp, level_info=level)
        if with_affinity
        else None
    )
    return CubeOwnership(
        id=1,
        user_id=1,
        ownership_status=OwnershipStatus.ACTIVE,
        is_last_accessed=True,
        affinity=affinity,
    )


def make_reward_item(
    *,
    reward_item_id: int,
    name: str = "일일 대화 가능 횟수",
    reward_type: RewardItemType = RewardItemType.CONVERSATION_COUNT,
    description: str | None = "하루에 대화 제한 100회",
    reward_count: int | None = 100,
    reward_level: int | None = 3,
) -> RewardItem:
    return RewardItem(
        id=reward_item_id,
        name=name,
        reward_type=reward_type,
        description=description,
        reward_count=reward_count,
        reward_level=reward_level,
        deleted_at=None,
    )


def make_mission(
    *,
    mission_id: int = 1,
    title: str = "홈 화면 방문하기",
    description: str | None = "AR ZONE 접속",
    target_action: MissionTargetAction = MissionTargetAction.HOME_VIEW,
    target_count: int = 1,
    reward_item: RewardItem | None = None,
) -> Mission:
    return Mission(
        id=mission_id,
        mission_type=MissionType.DAILY,
        title=title,
        description=description,
        target_action=target_action,
        target_count=target_count,
        is_active=True,
        deleted_at=None,
        reward_item=reward_item
        or make_reward_item(
            reward_item_id=2,
            name="친밀도 포인트",
            reward_type=RewardItemType.AFFINITY_POINT,
            description="친밀도 5포인트 제공",
            reward_count=5,
            reward_level=None,
        ),
    )


def make_progress(
    *,
    mission_id: int = 1,
    current_count: int = 1,
    status: MissionProgressStatus = MissionProgressStatus.REWARDED,
    reward_claimed: bool = True,
) -> MissionProgress:
    return MissionProgress(
        id=1,
        cube_ownership_id=1,
        mission_id=mission_id,
        current_count=current_count,
        status=status,
        reward_claimed=reward_claimed,
        completed_at=datetime.fromisoformat("2026-08-28T10:00:00"),
        claimed_at=datetime.fromisoformat("2026-08-28T10:00:01"),
    )


def set_query_results(db: Mock, results: list[list[object]]) -> None:
    """서비스가 db.scalars를 호출하는 순서대로 결과를 지정합니다."""
    db.scalars.side_effect = results


def test_read_affinity_returns_full_detail():
    db = Mock(spec=Session)
    db.scalar.return_value = make_ownership()
    current_reward = make_reward_item(reward_item_id=8)
    next_reward = make_reward_item(
        reward_item_id=9,
        description="하루에 대화 제한 없음",
        reward_count=None,
        reward_level=4,
    )
    mission = make_mission()
    set_query_results(
        db,
        [
            make_levels(),
            [current_reward],
            [next_reward],
            [mission],
            [make_progress()],
        ],
    )

    response = request_affinity(db)

    assert response.status_code == 200
    assert response.json() == {
        "affinity": {
            "id": 1,
            "currentXp": 1245,
            "progressPercent": 62,
            "remainingXp": 755,
            "currentLevel": {
                "id": 3,
                "level": 3,
                "levelName": "Close",
                "requiredXp": 800,
                "rewards": [
                    {
                        "id": 8,
                        "name": "일일 대화 가능 횟수",
                        "rewardType": "CONVERSATION_COUNT",
                        "description": "하루에 대화 제한 100회",
                        "rewardCount": 100,
                        "rewardLevel": 3,
                    }
                ],
            },
            "nextLevel": {
                "id": 4,
                "level": 4,
                "levelName": "Special",
                "requiredXp": 2000,
                "rewards": [
                    {
                        "id": 9,
                        "name": "일일 대화 가능 횟수",
                        "rewardType": "CONVERSATION_COUNT",
                        "description": "하루에 대화 제한 없음",
                        "rewardCount": None,
                        "rewardLevel": 4,
                    }
                ],
            },
        },
        "dailyActivities": [
            {
                "id": 1,
                "title": "홈 화면 방문하기",
                "description": "AR ZONE 접속",
                "targetAction": "HOME_VIEW",
                "currentCount": 1,
                "targetCount": 1,
                "status": "REWARDED",
                "rewardClaimed": True,
                "reward": {
                    "id": 2,
                    "name": "친밀도 포인트",
                    "rewardType": "AFFINITY_POINT",
                    "description": "친밀도 5포인트 제공",
                    "rewardCount": 5,
                    "rewardLevel": None,
                },
            }
        ],
        "levels": [
            {
                "id": 1,
                "level": 1,
                "levelName": "Intro",
                "requiredXp": 0,
                "status": "COMPLETED",
            },
            {
                "id": 2,
                "level": 2,
                "levelName": "Friend",
                "requiredXp": 100,
                "status": "COMPLETED",
            },
            {
                "id": 3,
                "level": 3,
                "levelName": "Close",
                "requiredXp": 800,
                "status": "CURRENT",
            },
            {
                "id": 4,
                "level": 4,
                "levelName": "Special",
                "requiredXp": 2000,
                "status": "LOCKED",
            },
        ],
    }
    db.commit.assert_not_called()


def test_read_affinity_returns_null_next_level_at_maximum_level():
    db = Mock(spec=Session)
    top_level = make_level(
        level_id=4,
        level=4,
        level_name=LevelName.SPECIAL,
        level_xp=2000,
    )
    db.scalar.return_value = make_ownership(current_xp=2500, current_level=top_level)
    # 최고 레벨에서는 다음 레벨 보상 조회를 건너뜁니다.
    set_query_results(db, [make_levels(), [], [], []])

    response = request_affinity(db)

    assert response.status_code == 200
    body = response.json()["affinity"]
    assert body["nextLevel"] is None
    assert body["progressPercent"] == 100
    assert body["remainingXp"] == 0
    assert [level["status"] for level in response.json()["levels"]] == [
        "COMPLETED",
        "COMPLETED",
        "COMPLETED",
        "CURRENT",
    ]


def test_read_affinity_truncates_progress_percent():
    db = Mock(spec=Session)
    db.scalar.return_value = make_ownership(current_xp=1999)
    set_query_results(db, [make_levels(), [], [], [], []])

    response = request_affinity(db)

    assert response.status_code == 200
    # 1999 / 2000 * 100 = 99.95 -> 99
    assert response.json()["affinity"]["progressPercent"] == 99
    assert response.json()["affinity"]["remainingXp"] == 1


def test_read_affinity_returns_zero_progress_when_no_xp_earned():
    db = Mock(spec=Session)
    first_level = make_level(
        level_id=1,
        level=1,
        level_name=LevelName.INTRO,
        level_xp=0,
    )
    db.scalar.return_value = make_ownership(current_xp=0, current_level=first_level)
    set_query_results(db, [make_levels(), [], [], [], []])

    response = request_affinity(db)

    assert response.status_code == 200
    assert response.json()["affinity"]["progressPercent"] == 0
    assert response.json()["affinity"]["remainingXp"] == 100


def test_read_affinity_caps_progress_percent_at_100_when_xp_exceeds_next_level():
    db = Mock(spec=Session)
    db.scalar.return_value = make_ownership(current_xp=99999)
    set_query_results(db, [make_levels(), [], [], [], []])

    response = request_affinity(db)

    assert response.status_code == 200
    assert response.json()["affinity"]["progressPercent"] == 100
    assert response.json()["affinity"]["remainingXp"] == 0


def test_read_affinity_returns_defaults_for_mission_without_progress():
    db = Mock(spec=Session)
    db.scalar.return_value = make_ownership()
    set_query_results(db, [make_levels(), [], [], [make_mission()], []])

    response = request_affinity(db)

    assert response.status_code == 200
    activity = response.json()["dailyActivities"][0]
    assert activity["currentCount"] == 0
    assert activity["status"] == "IN_PROGRESS"
    assert activity["rewardClaimed"] is False


def test_read_affinity_returns_empty_daily_activities_when_no_mission():
    db = Mock(spec=Session)
    db.scalar.return_value = make_ownership()
    # 미션이 없으면 진행 정보 조회를 하지 않습니다.
    set_query_results(db, [make_levels(), [], [], []])

    response = request_affinity(db)

    assert response.status_code == 200
    assert response.json()["dailyActivities"] == []
    assert db.scalars.call_count == 4


def test_read_affinity_returns_empty_rewards_when_none_acquired():
    db = Mock(spec=Session)
    db.scalar.return_value = make_ownership()
    set_query_results(db, [make_levels(), [], [], [], []])

    response = request_affinity(db)

    assert response.status_code == 200
    assert response.json()["affinity"]["currentLevel"]["rewards"] == []
    assert response.json()["affinity"]["nextLevel"]["rewards"] == []


def test_read_affinity_returns_404_when_ownership_not_found():
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = request_affinity(db)

    assert response.status_code == 404
    assert response.json() == OWNERSHIP_NOT_FOUND_RESPONSE
    db.scalars.assert_not_called()


def test_read_affinity_returns_404_when_affinity_not_found():
    db = Mock(spec=Session)
    db.scalar.return_value = make_ownership(with_affinity=False)

    response = request_affinity(db)

    assert response.status_code == 404
    assert response.json() == AFFINITY_NOT_FOUND_RESPONSE
    db.scalars.assert_not_called()


def test_read_affinity_queries_only_own_active_last_accessed_ownership():
    db = Mock(spec=Session)
    db.scalar.return_value = make_ownership()
    set_query_results(db, [make_levels(), [], [], [], []])

    request_affinity(db)

    where_clause = compiled_where(db.scalar.call_args.args[0])
    assert "cube_ownership.user_id = 1" in where_clause
    assert "cube_ownership.ownership_status = 'ACTIVE'" in where_clause
    assert "cube_ownership.is_last_accessed IS true" in where_clause


def test_read_affinity_excludes_deleted_reward_items_and_orders_by_id():
    db = Mock(spec=Session)
    db.scalar.return_value = make_ownership()
    set_query_results(db, [make_levels(), [], [], [], []])

    request_affinity(db)

    acquired_rewards_query = str(db.scalars.call_args_list[1].args[0])
    level_rewards_query = str(db.scalars.call_args_list[2].args[0])
    for query in (acquired_rewards_query, level_rewards_query):
        assert "reward_item.deleted_at IS NULL" in query
        assert "ORDER BY reward_item.id ASC" in query
    assert "user_reward" in acquired_rewards_query
    assert "DISTINCT" in acquired_rewards_query
    assert "user_reward" not in level_rewards_query


def test_read_affinity_filters_daily_missions_by_active_state_and_period():
    db = Mock(spec=Session)
    db.scalar.return_value = make_ownership()
    set_query_results(db, [make_levels(), [], [], [], []])

    request_affinity(db)

    mission_query = str(db.scalars.call_args_list[3].args[0])
    assert "mission.mission_type = " in mission_query
    assert "mission.is_active IS true" in mission_query
    assert "mission.deleted_at IS NULL" in mission_query
    assert "mission.start_at IS NULL" in mission_query
    assert "mission.end_at IS NULL" in mission_query
    assert "ORDER BY mission.id ASC" in mission_query


def test_read_affinity_orders_levels_by_level_number():
    db = Mock(spec=Session)
    db.scalar.return_value = make_ownership()
    set_query_results(db, [make_levels(), [], [], [], []])

    request_affinity(db)

    assert "ORDER BY level.level ASC" in str(db.scalars.call_args_list[0].args[0])


def test_read_affinity_swagger_contract():
    operation = app.openapi()["paths"]["/api/v1/users/me/affinity"]["get"]

    assert set(operation["responses"]) == {"200", "404"}
    assert "security" not in operation


def compiled_where(statement) -> str:
    return str(statement.compile(compile_kwargs={"literal_binds": True})).split(
        "WHERE"
    )[1]
