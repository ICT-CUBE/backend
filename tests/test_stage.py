"""스테이지 재생 세션 API 테스트."""

from collections.abc import Iterator
from datetime import datetime
from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models.cube import CubeOwnership
from app.models.enums import OwnershipStatus, StageSessionStatus, StageViewMode
from app.models.stage import Stage, StageSession


def request_stage_session(
    db: Mock,
    *,
    stage_id: int = 1,
    body: dict[str, str] | None = None,
):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            return client.post(
                f"/api/v1/stages/{stage_id}/sessions",
                json=body if body is not None else {"viewMode": "AR"},
            )
    finally:
        app.dependency_overrides.clear()


def save_stage_session_request(
    db: Mock,
    *,
    stage_session_id: int = 501,
    body: dict[str, str | int] | None = None,
):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            return client.patch(
                f"/api/v1/users/me/stage-sessions/{stage_session_id}",
                json=body
                if body is not None
                else {
                    "status": "CANCELLED",
                    "lastPositionSeconds": 74,
                    "viewedSeconds": 62,
                },
            )
    finally:
        app.dependency_overrides.clear()


def active_stage() -> Stage:
    return Stage(id=1, is_active=True, duration_seconds=222)


def active_ownership() -> CubeOwnership:
    return CubeOwnership(
        id=12,
        user_id=1,
        ownership_status=OwnershipStatus.ACTIVE,
        is_last_accessed=True,
    )


def playing_session() -> StageSession:
    return StageSession(
        id=501,
        status=StageSessionStatus.PLAYING,
        last_position_seconds=0,
        viewed_seconds=0,
        view_mode=StageViewMode.AR,
    )


def test_create_stage_session_adds_orm_model_with_initial_values() -> None:
    db = Mock(spec=Session)
    db.scalar.side_effect = [active_stage(), active_ownership(), None]

    def assign_generated_id() -> None:
        db.add.call_args.args[0].id = 501

    db.flush.side_effect = assign_generated_id

    response = request_stage_session(db)

    assert response.status_code == 201
    assert response.json() == {"stageSession": {"id": 501, "viewMode": "AR"}}
    inserted = db.add.call_args.args[0]
    assert isinstance(inserted, StageSession)
    assert inserted.cube_ownership_id == 12
    assert inserted.stage_id == 1
    assert inserted.view_mode == StageViewMode.AR
    assert inserted.status == StageSessionStatus.PLAYING
    assert inserted.last_position_seconds == 0
    assert inserted.viewed_seconds == 0
    assert isinstance(inserted.started_at, datetime)
    assert inserted.started_at.tzinfo is None
    db.flush.assert_called_once()
    db.commit.assert_called_once()


def test_create_stage_session_returns_404_for_missing_or_inactive_stage() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = request_stage_session(db)

    assert response.status_code == 404
    assert response.json()["code"] == "STAGE_NOT_FOUND"


def test_create_stage_session_returns_404_without_last_active_ownership() -> None:
    db = Mock(spec=Session)
    db.scalar.side_effect = [active_stage(), None]

    response = request_stage_session(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CUBE_OWNERSHIP_NOT_FOUND",
        "message": "큐브 소유권 정보를 찾을 수 없습니다.",
    }


def test_create_stage_session_returns_409_when_already_playing() -> None:
    db = Mock(spec=Session)
    db.scalar.side_effect = [active_stage(), active_ownership(), 77]

    response = request_stage_session(db)

    assert response.status_code == 409
    assert response.json()["code"] == "STAGE_SESSION_ALREADY_PLAYING"
    db.rollback.assert_called_once()
    db.add.assert_not_called()


def test_create_stage_session_returns_400_for_invalid_view_mode() -> None:
    response = request_stage_session(Mock(spec=Session), body={"viewMode": "INVALID"})

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


def test_create_stage_session_returns_400_for_non_positive_stage_id() -> None:
    response = request_stage_session(Mock(spec=Session), stage_id=0)

    assert response.status_code == 400


def test_stage_session_swagger_responses() -> None:
    operation = app.openapi()["paths"]["/api/v1/stages/{stageId}/sessions"]["post"]

    assert set(operation["responses"]) == {"201", "400", "404", "409"}
    assert "security" not in operation


def stage_session_result(
    db: Mock, session: StageSession | None, duration: int = 222
) -> None:
    db.execute.return_value.one_or_none.return_value = (
        None if session is None else (session, duration)
    )


def test_save_stage_session_updates_orm_model() -> None:
    db = Mock(spec=Session)
    session = playing_session()
    stage_session_result(db, session)

    response = save_stage_session_request(db)

    assert response.status_code == 204
    assert response.content == b""
    assert session.status == StageSessionStatus.CANCELLED
    assert session.last_position_seconds == 74
    assert session.viewed_seconds == 62
    assert isinstance(session.ended_at, datetime)
    assert session.ended_at.tzinfo is None
    db.commit.assert_called_once()


def test_save_stage_session_allows_viewed_seconds_over_video_duration() -> None:
    db = Mock(spec=Session)
    session = playing_session()
    stage_session_result(db, session)

    response = save_stage_session_request(
        db,
        body={
            "status": "COMPLETED",
            "lastPositionSeconds": 222,
            "viewedSeconds": 300,
        },
    )

    assert response.status_code == 204
    assert session.status == StageSessionStatus.COMPLETED
    assert session.viewed_seconds == 300


def test_save_stage_session_returns_404_for_unknown_or_other_user_session() -> None:
    db = Mock(spec=Session)
    stage_session_result(db, None)

    response = save_stage_session_request(db)

    assert response.status_code == 404
    assert response.json()["code"] == "STAGE_SESSION_NOT_FOUND"
    db.commit.assert_not_called()


def test_save_stage_session_returns_409_when_already_ended() -> None:
    db = Mock(spec=Session)
    session = playing_session()
    session.status = StageSessionStatus.COMPLETED
    stage_session_result(db, session)

    response = save_stage_session_request(db)

    assert response.status_code == 409
    assert response.json()["code"] == "STAGE_SESSION_ALREADY_ENDED"
    db.rollback.assert_called_once()


def test_save_stage_session_returns_400_when_position_exceeds_duration() -> None:
    db = Mock(spec=Session)
    session = playing_session()
    stage_session_result(db, session)

    response = save_stage_session_request(
        db,
        body={
            "status": "COMPLETED",
            "lastPositionSeconds": 223,
            "viewedSeconds": 223,
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_save_stage_session_returns_400_for_invalid_body_values() -> None:
    invalid_bodies = [
        {"status": "PLAYING", "lastPositionSeconds": 74, "viewedSeconds": 62},
        {"status": "CANCELLED", "lastPositionSeconds": -1, "viewedSeconds": 62},
        {"status": "CANCELLED", "lastPositionSeconds": 74, "viewedSeconds": -1},
    ]

    for body in invalid_bodies:
        response = save_stage_session_request(Mock(spec=Session), body=body)
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_REQUEST"


def test_save_stage_session_swagger_responses() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/stage-sessions/{stageSessionId}"
    ]["patch"]

    assert set(operation["responses"]) == {"204", "400", "404", "409"}
    assert "security" not in operation
