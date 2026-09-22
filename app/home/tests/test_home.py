"""홈 도메인 API 테스트."""

from collections.abc import Iterator
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.affinity.models import Affinity, Level
from app.core.enums import (
    LevelName,
    MissionTargetAction,
    NotificationType,
    OwnershipStatus,
)
from app.core.tests.conftest import api_client
from app.cube.models import Cube, CubeOwnership
from app.home.service import KOREA_TIMEZONE
from app.main import app
from app.user.models import Notification, User


@pytest.fixture(autouse=True)
def mission_progress() -> Iterator[Mock]:
    """미션 진행도 로직은 app/mission/tests 에서 검증하고 여기서는 호출만 기록합니다."""
    with patch("app.home.service.increase_mission_progress") as mocked:
        yield mocked


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


# --- 알림 목록 조회: GET /api/v1/users/me/notifications ---

INVALID_REQUEST_RESPONSE = {
    "code": "INVALID_REQUEST",
    "message": "요청값이 올바르지 않습니다.",
}


def request_notifications(
    db: Mock,
    *,
    type_: str | None = "ALL",
    page: int | str | None = None,
    size: int | str | None = None,
):
    params: dict[str, int | str] = {}
    if type_ is not None:
        params["type"] = type_
    if page is not None:
        params["page"] = page
    if size is not None:
        params["size"] = size
    with api_client(db) as client:
        return client.get("/api/v1/users/me/notifications", params=params)


def make_notification(
    *,
    notification_id: int,
    notification_type: NotificationType = NotificationType.MARKET,
    title: str = "거래 알림",
    content: str = "거래 제안이 도착했어요.",
    is_read: bool = False,
    sent_at: str = "2026-07-28T14:25:00",
) -> Notification:
    return Notification(
        id=notification_id,
        user_id=1,
        notification_type=notification_type,
        title=title,
        content=content,
        is_read=is_read,
        sent_at=datetime.fromisoformat(sent_at),
        read_at=None,
    )


def set_notification_results(db: Mock, *, rows: list | None = None) -> None:
    """서비스가 db.scalars 로 조회한 알림 목록을 지정합니다."""
    db.scalars.return_value.all.return_value = rows or []


def compiled_query(call) -> str:
    return str(call.args[0].compile(compile_kwargs={"literal_binds": True}))


def test_read_notifications_returns_notifications_with_pagination() -> None:
    db = Mock(spec=Session)
    set_notification_results(
        db,
        rows=[
            make_notification(notification_id=4),
            make_notification(
                notification_id=3,
                notification_type=NotificationType.MISSION,
                title="데일리 미션을 완료했어요",
                content="미션 보상을 수령해보세요.",
                is_read=True,
                sent_at="2026-07-28T13:30:00",
            ),
        ],
    )

    response = request_notifications(db)

    assert response.status_code == 200
    assert response.json() == {
        "notifications": [
            {
                "id": 4,
                "notificationType": "MARKET",
                "title": "거래 알림",
                "content": "거래 제안이 도착했어요.",
                "isRead": False,
                "sentAt": "2026-07-28T14:25:00",
            },
            {
                "id": 3,
                "notificationType": "MISSION",
                "title": "데일리 미션을 완료했어요",
                "content": "미션 보상을 수령해보세요.",
                "isRead": True,
                "sentAt": "2026-07-28T13:30:00",
            },
        ],
        "pagination": {"page": 0, "size": 20, "hasNext": False},
    }
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_read_notifications_returns_empty_list_when_no_notification() -> None:
    db = Mock(spec=Session)
    set_notification_results(db, rows=[])

    response = request_notifications(db)

    assert response.status_code == 200
    assert response.json() == {
        "notifications": [],
        "pagination": {"page": 0, "size": 20, "hasNext": False},
    }


def test_read_notifications_returns_has_next_true_when_more_rows_exist() -> None:
    db = Mock(spec=Session)
    set_notification_results(
        db,
        rows=[
            make_notification(notification_id=3),
            make_notification(notification_id=2),
            make_notification(notification_id=1),
        ],
    )

    response = request_notifications(db, page=1, size=2)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["notifications"]] == [3, 2]
    assert response.json()["pagination"] == {"page": 1, "size": 2, "hasNext": True}


def test_read_notifications_queries_all_types_when_type_is_all() -> None:
    db = Mock(spec=Session)
    set_notification_results(db, rows=[])

    response = request_notifications(db, type_="ALL")

    assert response.status_code == 200
    where_clause = compiled_query(db.scalars.call_args).split("WHERE", 1)[1]
    assert "notification.notification_type" not in where_clause


def test_read_notifications_filters_mission_type() -> None:
    db = Mock(spec=Session)
    set_notification_results(db, rows=[])

    response = request_notifications(db, type_="MISSION")

    assert response.status_code == 200
    query = compiled_query(db.scalars.call_args)
    assert "notification.notification_type = 'MISSION'" in query


def test_read_notifications_filters_event_type() -> None:
    db = Mock(spec=Session)
    set_notification_results(db, rows=[])

    response = request_notifications(db, type_="EVENT")

    assert response.status_code == 200
    query = compiled_query(db.scalars.call_args)
    assert "notification.notification_type = 'EVENT'" in query


def test_read_notifications_filters_market_type() -> None:
    db = Mock(spec=Session)
    set_notification_results(db, rows=[])

    response = request_notifications(db, type_="MARKET")

    assert response.status_code == 200
    query = compiled_query(db.scalars.call_args)
    assert "notification.notification_type = 'MARKET'" in query


def test_read_notifications_queries_only_current_user_rows() -> None:
    db = Mock(spec=Session)
    set_notification_results(db, rows=[])

    request_notifications(db)

    query = compiled_query(db.scalars.call_args)
    assert "notification.user_id = 1" in query
    assert "cube_ownership" not in query


def test_read_notifications_orders_by_sent_at_and_id_desc() -> None:
    db = Mock(spec=Session)
    set_notification_results(db, rows=[])

    request_notifications(db, page=2, size=5)

    query = compiled_query(db.scalars.call_args)
    assert "ORDER BY notification.sent_at DESC, notification.id DESC" in query
    assert "LIMIT 6" in query
    assert "OFFSET 10" in query


def test_read_notifications_allows_minimum_page_and_size() -> None:
    db = Mock(spec=Session)
    set_notification_results(db, rows=[])

    response = request_notifications(db, page=0, size=1)

    assert response.status_code == 200
    assert response.json()["pagination"] == {"page": 0, "size": 1, "hasNext": False}


def test_read_notifications_returns_400_when_page_is_negative() -> None:
    db = Mock(spec=Session)

    response = request_notifications(db, page=-1)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalars.assert_not_called()


def test_read_notifications_returns_400_when_size_is_zero() -> None:
    db = Mock(spec=Session)

    response = request_notifications(db, size=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalars.assert_not_called()


def test_read_notifications_returns_400_when_type_is_missing() -> None:
    db = Mock(spec=Session)

    response = request_notifications(db, type_=None)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalars.assert_not_called()


def test_read_notifications_returns_400_for_unsupported_type() -> None:
    db = Mock(spec=Session)

    response = request_notifications(db, type_="NOTICE")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalars.assert_not_called()


def test_read_notifications_swagger_contract() -> None:
    operation = app.openapi()["paths"]["/api/v1/users/me/notifications"]["get"]

    assert set(operation["responses"]) == {"200", "400"}
    assert {parameter["name"] for parameter in operation["parameters"]} == {
        "type",
        "page",
        "size",
    }
    assert operation["tags"] == ["home"]
    assert operation["security"] == [{"HTTPBearer": []}]


# --- 개별 알림 읽음 처리: PATCH /api/v1/users/me/notifications/{notificationId}/read ---

NOTIFICATION_NOT_FOUND_RESPONSE = {
    "code": "NOTIFICATION_NOT_FOUND",
    "message": "알림을 찾을 수 없습니다.",
}


def request_notification_read(
    db: Mock,
    *,
    notification_id: int | str = 31,
    raise_server_exceptions: bool = True,
):
    with api_client(db, raise_server_exceptions=raise_server_exceptions) as client:
        return client.patch(f"/api/v1/users/me/notifications/{notification_id}/read")


def test_read_notification_marks_unread_notification_as_read() -> None:
    db = Mock(spec=Session)
    notification = make_notification(notification_id=31, is_read=False)
    db.scalar.return_value = notification

    response = request_notification_read(db)

    assert response.status_code == 204
    assert response.content == b""
    assert notification.is_read is True
    assert notification.read_at is not None
    assert notification.read_at.tzinfo is None
    db.commit.assert_called_once()


def test_read_notification_stores_read_at_in_korea_time() -> None:
    db = Mock(spec=Session)
    notification = make_notification(notification_id=31, is_read=False)
    db.scalar.return_value = notification

    with patch("app.home.service.datetime") as fake_datetime:
        fake_datetime.now.return_value = datetime.fromisoformat(
            "2026-07-28T23:10:00+09:00"
        )
        response = request_notification_read(db)

    assert response.status_code == 204
    assert notification.read_at == datetime.fromisoformat("2026-07-28T23:10:00")
    assert fake_datetime.now.call_args.args[0] == KOREA_TIMEZONE


def test_read_notification_keeps_read_at_when_already_read() -> None:
    db = Mock(spec=Session)
    notification = make_notification(notification_id=31, is_read=True)
    notification.read_at = datetime.fromisoformat("2026-07-28T13:30:00")
    db.scalar.return_value = notification

    response = request_notification_read(db)

    assert response.status_code == 204
    assert notification.is_read is True
    assert notification.read_at == datetime.fromisoformat("2026-07-28T13:30:00")
    db.commit.assert_not_called()


def test_read_notification_returns_404_when_notification_not_found() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = request_notification_read(db)

    assert response.status_code == 404
    assert response.json() == NOTIFICATION_NOT_FOUND_RESPONSE
    db.commit.assert_not_called()


def test_read_notification_queries_only_current_user_row_with_lock() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = make_notification(notification_id=31, is_read=False)

    request_notification_read(db, notification_id=31)

    query = compiled_query(db.scalar.call_args)
    assert "notification.id = 31" in query
    assert "notification.user_id = 1" in query
    assert "FOR UPDATE" in query
    assert "cube_ownership" not in query


def test_read_notification_allows_minimum_notification_id() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = make_notification(notification_id=1, is_read=False)

    response = request_notification_read(db, notification_id=1)

    assert response.status_code == 204


def test_read_notification_returns_400_when_notification_id_is_zero() -> None:
    db = Mock(spec=Session)

    response = request_notification_read(db, notification_id=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_read_notification_returns_400_when_notification_id_is_not_number() -> None:
    db = Mock(spec=Session)

    response = request_notification_read(db, notification_id="abc")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_read_notification_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = make_notification(notification_id=31, is_read=False)
    db.commit.side_effect = RuntimeError("commit failed")

    response = request_notification_read(db, raise_server_exceptions=False)

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_read_notification_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/notifications/{notificationId}/read"
    ]["patch"]

    assert set(operation["responses"]) == {"204", "404"}
    assert {parameter["name"] for parameter in operation["parameters"]} == {
        "notificationId",
    }
    assert operation["tags"] == ["home"]
    assert operation["security"] == [{"HTTPBearer": []}]


# --- 전체 알림 읽음 처리: PATCH /api/v1/users/me/notifications/read-all ---


def request_all_notifications_read(
    db: Mock,
    *,
    raise_server_exceptions: bool = True,
):
    with api_client(db, raise_server_exceptions=raise_server_exceptions) as client:
        return client.patch("/api/v1/users/me/notifications/read-all")


def test_read_all_notifications_updates_unread_rows_in_single_statement() -> None:
    db = Mock(spec=Session)

    response = request_all_notifications_read(db)

    assert response.status_code == 204
    assert response.content == b""
    db.execute.assert_called_once()
    db.commit.assert_called_once()
    db.add.assert_not_called()


def test_read_all_notifications_targets_only_current_user_unread_rows() -> None:
    db = Mock(spec=Session)

    request_all_notifications_read(db)

    query = compiled_query(db.execute.call_args)
    assert query.startswith("UPDATE notification SET")
    assert "notification.user_id = 1" in query
    assert "notification.is_read IS false" in query
    assert "cube_ownership" not in query
    assert "notification_type" not in query


def test_read_all_notifications_stores_same_korea_read_at_for_every_row() -> None:
    db = Mock(spec=Session)

    with patch("app.home.service.datetime") as fake_datetime:
        fake_datetime.now.return_value = datetime.fromisoformat(
            "2026-07-28T23:10:00+09:00"
        )
        response = request_all_notifications_read(db)

    assert response.status_code == 204
    assert fake_datetime.now.call_count == 1
    assert fake_datetime.now.call_args.args[0] == KOREA_TIMEZONE
    query = compiled_query(db.execute.call_args)
    assert "read_at='2026-07-28 23:10:00'" in query.replace(" = ", "=")
    assert "is_read=true" in query.replace(" = ", "=")


def test_read_all_notifications_succeeds_when_no_unread_notification() -> None:
    db = Mock(spec=Session)
    db.execute.return_value.rowcount = 0

    response = request_all_notifications_read(db)

    assert response.status_code == 204
    assert response.content == b""
    db.commit.assert_called_once()


def test_read_all_notifications_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    db.commit.side_effect = RuntimeError("commit failed")

    response = request_all_notifications_read(db, raise_server_exceptions=False)

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_read_all_notifications_swagger_contract() -> None:
    operation = app.openapi()["paths"]["/api/v1/users/me/notifications/read-all"][
        "patch"
    ]

    assert set(operation["responses"]) == {"204"}
    assert "parameters" not in operation
    assert operation["tags"] == ["home"]
    assert operation["security"] == [{"HTTPBearer": []}]


# --- 미션 진행도 반영: GET /api/v1/users/me/home ---


def test_home_increases_home_view_mission_progress_and_commits(
    mission_progress: Mock,
) -> None:
    db = Mock(spec=Session)
    db.scalars.return_value.first.return_value = make_ownership(
        OwnershipStatus.ACTIVE
    )
    db.scalar.return_value = 2000

    response = request_home(db)

    assert response.status_code == 200
    mission_progress.assert_called_once_with(
        db=db,
        current_user_id=1,
        target_action=MissionTargetAction.HOME_VIEW,
    )
    db.commit.assert_called_once()


def test_home_does_not_increase_progress_when_ownership_is_inactive(
    mission_progress: Mock,
) -> None:
    db = Mock(spec=Session)
    db.scalars.return_value.first.return_value = make_ownership(
        OwnershipStatus.TRANSFERRED
    )

    response = request_home(db)

    assert response.status_code == 403
    mission_progress.assert_not_called()
    db.commit.assert_not_called()


def test_home_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    db.scalars.return_value.first.return_value = make_ownership(
        OwnershipStatus.ACTIVE
    )
    db.scalar.return_value = 2000
    db.commit.side_effect = RuntimeError("db failed")

    with api_client(db, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/users/me/home")

    assert response.status_code == 500
    db.rollback.assert_called_once()
