"""스테이지 재생 세션 API 테스트."""

from collections.abc import Iterator
from datetime import datetime
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models.cube import CubeOwnership
from app.models.enums import OwnershipStatus, StageSessionStatus, StageViewMode
from app.models.stage import Stage, StageCapture, StageSession


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


def save_stage_capture_request(
    db: Mock,
    *,
    stage_session_id: int = 501,
    content_type: str = "image/png",
    data: dict[str, str] | None = None,
    include_image: bool = True,
    raise_server_exceptions: bool = True,
):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        files = (
            {"image": ("capture.png", b"fake-image", content_type)}
            if include_image
            else None
        )
        with TestClient(
            app, raise_server_exceptions=raise_server_exceptions
        ) as client:
            return client.post(
                f"/api/v1/users/me/stage-sessions/{stage_session_id}/captures",
                files=files,
                data=data
                if data is not None
                else {
                    "capturedPositionSeconds": "74",
                    "capturedAt": "2026-07-29T15:05:20",
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


def test_create_stage_session_does_not_apply_positive_path_validation() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = request_stage_session(db, stage_id=0)

    assert response.status_code == 404
    db.scalar.assert_called_once()


def test_stage_session_swagger_responses() -> None:
    operation = app.openapi()["paths"]["/api/v1/stages/{stageId}/sessions"]["post"]

    assert set(operation["responses"]) == {"201", "404", "409"}
    assert "security" not in operation


def stage_session_result(db: Mock, session: StageSession | None) -> None:
    db.scalar.return_value = session


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


def test_save_stage_session_accepts_unchecked_numeric_values() -> None:
    db = Mock(spec=Session)
    session = playing_session()
    stage_session_result(db, session)

    response = save_stage_session_request(
        db,
        body={
            "status": "COMPLETED",
            "lastPositionSeconds": -10,
            "viewedSeconds": 999999,
        },
    )

    assert response.status_code == 204
    assert session.last_position_seconds == -10
    assert session.viewed_seconds == 999999
    db.commit.assert_called_once()


def test_save_stage_session_returns_common_400_when_field_is_missing() -> None:
    db = Mock(spec=Session)
    response = save_stage_session_request(
        db,
        body={"status": "CANCELLED", "lastPositionSeconds": 74},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    db.scalar.assert_not_called()


def test_save_stage_session_swagger_responses() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/stage-sessions/{stageSessionId}"
    ]["patch"]

    assert set(operation["responses"]) == {"204", "404", "409"}
    assert "security" not in operation


def test_save_stage_capture_uploads_image_and_adds_orm_model() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = playing_session()

    with patch(
        "app.services.stage.upload_stage_capture",
        return_value=(
            "https://haniumstorage.blob.core.windows.net/hanium/"
            "stage_capture/test.png"
        ),
    ) as upload:
        response = save_stage_capture_request(db)

    assert response.status_code == 204
    assert response.content == b""
    upload.assert_called_once()
    assert upload.call_args.kwargs["user_id"] == 1
    assert upload.call_args.kwargs["stage_session_id"] == 501
    capture = db.add.call_args.args[0]
    assert isinstance(capture, StageCapture)
    assert capture.stage_session_id == 501
    assert capture.stage_capture_img_url.endswith("stage_capture/test.png")
    assert capture.captured_position_seconds == 74
    assert capture.captured_at == datetime.fromisoformat("2026-07-29T15:05:20")
    db.commit.assert_called_once()


def test_save_stage_capture_returns_404_for_unknown_or_other_user_session() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    with patch("app.services.stage.upload_stage_capture") as upload:
        response = save_stage_capture_request(db)

    assert response.status_code == 404
    assert response.json()["code"] == "STAGE_SESSION_NOT_FOUND"
    upload.assert_not_called()
    db.add.assert_not_called()


def test_save_stage_capture_returns_400_for_unsupported_content_type() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = playing_session()

    with patch("app.services.stage.upload_stage_capture") as upload:
        response = save_stage_capture_request(db, content_type="image/gif")

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    upload.assert_not_called()


def test_save_stage_capture_accepts_image_jpg_content_type() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = playing_session()

    with patch(
        "app.services.stage.upload_stage_capture",
        return_value="https://cdn.example.com/stage_capture/test.jpg",
    ) as upload:
        response = save_stage_capture_request(db, content_type="image/jpg")

    assert response.status_code == 204
    assert upload.call_args.kwargs["content_type"] == "image/jpg"


def test_save_stage_capture_accepts_uppercase_jpeg_content_type() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = playing_session()

    with patch(
        "app.services.stage.upload_stage_capture",
        return_value="https://cdn.example.com/stage_capture/test.jpg",
    ) as upload:
        response = save_stage_capture_request(db, content_type="IMAGE/JPEG")

    assert response.status_code == 204
    assert upload.call_args.kwargs["content_type"] == "image/jpeg"


def test_save_stage_capture_returns_400_when_required_form_field_is_missing() -> None:
    response = save_stage_capture_request(
        Mock(spec=Session),
        data={"capturedPositionSeconds": "74"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


def test_save_stage_capture_uses_common_500_when_azure_upload_fails() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = playing_session()

    with patch(
        "app.services.stage.upload_stage_capture",
        side_effect=RuntimeError("storage unavailable"),
    ):
        response = save_stage_capture_request(
            db,
            raise_server_exceptions=False,
        )

    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_SERVER_ERROR"
    db.add.assert_not_called()


def test_save_stage_capture_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/stage-sessions/{stageSessionId}/captures"
    ]["post"]

    assert set(operation["responses"]) == {"204", "400", "404"}
    assert "multipart/form-data" in operation["requestBody"]["content"]
    assert "security" not in operation
