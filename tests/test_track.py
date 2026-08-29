"""트랙 재생 세션 생성 API 테스트."""

from datetime import datetime
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session

from app.main import app
from app.models.cube import CubeOwnership
from app.models.enums import (
    OwnershipStatus,
    TrackPlayMode,
    TrackSessionStatus,
)
from app.models.track import Track, TrackCapture, TrackSession
from tests.conftest import api_client


def request_track_session(
    db: Mock,
    *,
    track_id: int = 1,
    body: dict[str, str] | None = None,
):
    with api_client(db) as client:
        return client.post(
            f"/api/v1/tracks/{track_id}/sessions",
            json=body if body is not None else {"playMode": "NORMAL"},
        )


def save_track_session_request(
    db: Mock,
    *,
    track_session_id: int = 601,
    body: dict[str, str | int] | None = None,
):
    with api_client(db) as client:
        return client.patch(
            f"/api/v1/users/me/track-sessions/{track_session_id}",
            json=body
            if body is not None
            else {
                "status": "CANCELLED",
                "lastPositionSeconds": 74,
                "viewedSeconds": 62,
            },
        )


def save_track_capture_request(
    db: Mock,
    *,
    track_session_id: int = 601,
    content_type: str = "image/jpeg",
    data: dict[str, str] | None = None,
    include_image: bool = True,
    raise_server_exceptions: bool = True,
):
    files = (
        {"image": ("capture.jpg", b"fake-image", content_type)}
        if include_image
        else None
    )
    with api_client(
        db,
        raise_server_exceptions=raise_server_exceptions,
    ) as client:
        return client.post(
            f"/api/v1/users/me/track-sessions/{track_session_id}/captures",
            files=files,
            data=data
            if data is not None
            else {
                "capturedPositionSeconds": "74",
                "capturedAt": "2026-07-29T15:05:20",
            },
        )


def track() -> Track:
    return Track(id=1, title="First Light")


def ownership() -> CubeOwnership:
    return CubeOwnership(
        id=12,
        user_id=1,
        ownership_status=OwnershipStatus.ACTIVE,
        is_last_accessed=True,
    )


def playing_track_session() -> TrackSession:
    return TrackSession(
        id=601,
        status=TrackSessionStatus.PLAYING,
        last_position_seconds=0,
        viewed_seconds=0,
        play_mode=TrackPlayMode.NORMAL,
    )


def test_create_track_session_adds_orm_model_with_initial_values() -> None:
    db = Mock(spec=Session)
    db.get.return_value = track()
    db.scalar.return_value = ownership()

    def assign_generated_id() -> None:
        db.add.call_args.args[0].id = 601

    db.flush.side_effect = assign_generated_id

    response = request_track_session(db)

    assert response.status_code == 201
    assert response.json() == {
        "trackSession": {"id": 601, "playMode": "NORMAL"}
    }
    inserted = db.add.call_args.args[0]
    assert isinstance(inserted, TrackSession)
    assert inserted.cube_ownership_id == 12
    assert inserted.track_id == 1
    assert inserted.play_mode == TrackPlayMode.NORMAL
    assert inserted.status == TrackSessionStatus.PLAYING
    assert inserted.last_position_seconds == 0
    assert inserted.viewed_seconds == 0
    assert isinstance(inserted.started_at, datetime)
    assert inserted.started_at.tzinfo is None
    assert inserted.ended_at is None
    db.flush.assert_called_once()
    db.commit.assert_called_once()


def test_create_track_session_returns_404_when_track_does_not_exist() -> None:
    db = Mock(spec=Session)
    db.get.return_value = None

    response = request_track_session(db, track_id=-1)

    assert response.status_code == 404
    assert response.json() == {
        "code": "TRACK_NOT_FOUND",
        "message": "앨범 트랙을 찾을 수 없습니다.",
    }
    db.scalar.assert_not_called()


def test_create_track_session_returns_404_without_active_ownership() -> None:
    db = Mock(spec=Session)
    db.get.return_value = track()
    db.scalar.return_value = None

    response = request_track_session(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CUBE_OWNERSHIP_NOT_FOUND",
        "message": "큐브 소유권을 찾을 수 없습니다.",
    }


def test_create_track_session_returns_common_400_when_body_is_missing() -> None:
    db = Mock(spec=Session)

    response = request_track_session(db, body={})

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    db.get.assert_not_called()


def test_track_session_swagger_responses() -> None:
    operation = app.openapi()["paths"]["/api/v1/tracks/{trackId}/sessions"]["post"]

    assert set(operation["responses"]) == {"201", "404"}
    assert operation["security"] == [{"HTTPBearer": []}]


def test_save_track_session_updates_playing_orm_model() -> None:
    db = Mock(spec=Session)
    session = playing_track_session()
    db.scalar.return_value = session

    response = save_track_session_request(db)

    assert response.status_code == 204
    assert response.content == b""
    assert session.status == TrackSessionStatus.CANCELLED
    assert session.last_position_seconds == 74
    assert session.viewed_seconds == 62
    assert isinstance(session.ended_at, datetime)
    assert session.ended_at.tzinfo is None
    db.commit.assert_called_once()


def test_save_track_session_accepts_unchecked_numeric_values() -> None:
    db = Mock(spec=Session)
    session = playing_track_session()
    db.scalar.return_value = session

    response = save_track_session_request(
        db,
        body={
            "status": "COMPLETED",
            "lastPositionSeconds": -10,
            "viewedSeconds": 999999,
        },
    )

    assert response.status_code == 204
    assert session.status == TrackSessionStatus.COMPLETED
    assert session.last_position_seconds == -10
    assert session.viewed_seconds == 999999


def test_save_track_session_returns_404_for_unknown_or_other_user_session() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = save_track_session_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "TRACK_SESSION_NOT_FOUND",
        "message": "트랙 재생 세션을 찾을 수 없습니다.",
    }
    db.commit.assert_not_called()


def test_save_track_session_returns_409_when_already_ended() -> None:
    db = Mock(spec=Session)
    session = playing_track_session()
    session.status = TrackSessionStatus.COMPLETED
    db.scalar.return_value = session

    response = save_track_session_request(db)

    assert response.status_code == 409
    assert response.json() == {
        "code": "TRACK_SESSION_ALREADY_ENDED",
        "message": "이미 종료된 트랙 재생 세션입니다.",
    }
    db.commit.assert_not_called()


def test_save_track_session_returns_common_400_when_field_is_missing() -> None:
    db = Mock(spec=Session)

    response = save_track_session_request(
        db,
        body={
            "status": "COMPLETED",
            "lastPositionSeconds": 74,
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    db.scalar.assert_not_called()


def test_save_track_session_swagger_responses() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/track-sessions/{trackSessionId}"
    ]["patch"]

    assert set(operation["responses"]) == {"204", "404", "409"}
    assert operation["security"] == [{"HTTPBearer": []}]


def test_save_track_capture_uploads_image_and_adds_orm_model() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = playing_track_session()

    with patch(
        "app.services.album.upload_track_capture",
        return_value=(
            "https://haniumstorage.blob.core.windows.net/hanium/"
            "track_capture/1/601/test.jpg"
        ),
    ) as upload:
        response = save_track_capture_request(db)

    assert response.status_code == 204
    assert response.content == b""
    assert upload.call_args.kwargs["user_id"] == 1
    assert upload.call_args.kwargs["track_session_id"] == 601
    capture = db.add.call_args.args[0]
    assert isinstance(capture, TrackCapture)
    assert capture.track_session_id == 601
    assert capture.track_capture_img_url.endswith("track_capture/1/601/test.jpg")
    assert capture.captured_position_seconds == 74
    assert capture.captured_at == datetime.fromisoformat("2026-07-29T15:05:20")
    db.commit.assert_called_once()


def test_save_track_capture_returns_404_for_unknown_or_other_user_session() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    with patch("app.services.album.upload_track_capture") as upload:
        response = save_track_capture_request(db)

    assert response.status_code == 404
    assert response.json()["code"] == "TRACK_SESSION_NOT_FOUND"
    upload.assert_not_called()
    db.add.assert_not_called()


def test_save_track_capture_returns_400_for_unsupported_content_type() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = playing_track_session()

    with patch("app.services.album.upload_track_capture") as upload:
        response = save_track_capture_request(db, content_type="image/gif")

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    upload.assert_not_called()


def test_save_track_capture_accepts_image_jpg_content_type() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = playing_track_session()

    with patch(
        "app.services.album.upload_track_capture",
        return_value="https://cdn.example.com/track_capture/test.jpg",
    ) as upload:
        response = save_track_capture_request(db, content_type="image/jpg")

    assert response.status_code == 204
    assert upload.call_args.kwargs["content_type"] == "image/jpg"


def test_save_track_capture_accepts_uppercase_jpeg_content_type() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = playing_track_session()

    with patch(
        "app.services.album.upload_track_capture",
        return_value="https://cdn.example.com/track_capture/test.jpg",
    ) as upload:
        response = save_track_capture_request(db, content_type="IMAGE/JPEG")

    assert response.status_code == 204
    assert upload.call_args.kwargs["content_type"] == "image/jpeg"


def test_save_track_capture_returns_400_when_required_field_is_missing() -> None:
    response = save_track_capture_request(
        Mock(spec=Session),
        data={"capturedPositionSeconds": "74"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


def test_save_track_capture_uses_common_500_when_azure_upload_fails() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = playing_track_session()

    with patch(
        "app.services.album.upload_track_capture",
        side_effect=RuntimeError("storage unavailable"),
    ):
        response = save_track_capture_request(
            db,
            raise_server_exceptions=False,
        )

    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_SERVER_ERROR"
    db.add.assert_not_called()


def test_save_track_capture_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/track-sessions/{trackSessionId}/captures"
    ]["post"]

    assert set(operation["responses"]) == {"204", "400", "404"}
    assert "multipart/form-data" in operation["requestBody"]["content"]
    assert operation["security"] == [{"HTTPBearer": []}]
