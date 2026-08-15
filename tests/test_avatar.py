"""아바타 소환 세션 API 테스트."""

from collections.abc import Iterator
from datetime import datetime
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models.album import AlbumImage
from app.models.avatar import AvatarInteractionPicture, AvatarInteractionSession
from app.models.cube import CubeOwnership
from app.models.enums import (
    AlbumImageType,
    AvatarInteractionSessionStatus,
    OwnershipStatus,
)


def create_avatar_interaction_session_request(
    db: Mock,
    *,
    raise_server_exceptions: bool = True,
):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            raise_server_exceptions=raise_server_exceptions,
        ) as client:
            return client.post("/api/v1/users/me/avatar-interaction-sessions")
    finally:
        app.dependency_overrides.clear()


def request_yezul_frames(db: Mock):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            return client.get("/api/v1/users/me/album/yezul-frames")
    finally:
        app.dependency_overrides.clear()


def save_avatar_interaction_session_request(
    db: Mock,
    *,
    avatar_interaction_session_id: int = 1101,
    raise_server_exceptions: bool = True,
):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            raise_server_exceptions=raise_server_exceptions,
        ) as client:
            return client.patch(
                "/api/v1/users/me/avatar-interaction-sessions/"
                f"{avatar_interaction_session_id}"
            )
    finally:
        app.dependency_overrides.clear()


def save_avatar_interaction_picture_request(
    db: Mock,
    *,
    avatar_interaction_session_id: int = 1101,
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
            {"image": ("picture.png", b"fake-image", content_type)}
            if include_image
            else None
        )
        with TestClient(
            app,
            raise_server_exceptions=raise_server_exceptions,
        ) as client:
            return client.post(
                "/api/v1/users/me/avatar-interaction-sessions/"
                f"{avatar_interaction_session_id}/pictures",
                files=files,
                data=data
                if data is not None
                else {"picturedAt": "2026-07-29T15:05:20"},
            )
    finally:
        app.dependency_overrides.clear()


def active_ownership() -> CubeOwnership:
    return CubeOwnership(
        id=12,
        user_id=1,
        ownership_status=OwnershipStatus.ACTIVE,
        is_last_accessed=True,
    )


def yezul_frame(
    *,
    id: int,
    title: str | None,
    image_url: str,
) -> AlbumImage:
    return AlbumImage(
        id=id,
        title=title,
        image_type=AlbumImageType.YEZUL_FRAME,
        album_contents_img_url=image_url,
    )


def active_interaction_session() -> AvatarInteractionSession:
    return AvatarInteractionSession(
        id=1101,
        cube_ownership_id=12,
        started_at=datetime.fromisoformat("2026-08-13T12:00:00"),
        ended_at=None,
        status=AvatarInteractionSessionStatus.ACTIVE,
    )


def test_create_avatar_interaction_session_adds_initial_orm_model() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = active_ownership()

    def assign_generated_id() -> None:
        db.add.call_args.args[0].id = 1101

    db.flush.side_effect = assign_generated_id

    response = create_avatar_interaction_session_request(db)

    assert response.status_code == 201
    assert response.json() == {"avatarInteractionSession": {"id": 1101}}
    inserted = db.add.call_args.args[0]
    assert isinstance(inserted, AvatarInteractionSession)
    assert inserted.cube_ownership_id == 12
    assert isinstance(inserted.started_at, datetime)
    assert inserted.started_at.tzinfo is None
    assert inserted.ended_at is None
    assert inserted.status == AvatarInteractionSessionStatus.ACTIVE
    db.flush.assert_called_once()
    db.commit.assert_called_once()


def test_create_avatar_interaction_session_does_not_check_existing_active_session() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = active_ownership()
    db.flush.side_effect = lambda: setattr(db.add.call_args.args[0], "id", 1102)

    response = create_avatar_interaction_session_request(db)

    assert response.status_code == 201
    assert response.json() == {"avatarInteractionSession": {"id": 1102}}
    db.scalar.assert_called_once()


def test_create_avatar_interaction_session_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = active_ownership()
    db.commit.side_effect = RuntimeError("db failed")

    response = create_avatar_interaction_session_request(
        db,
        raise_server_exceptions=False,
    )

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_create_avatar_interaction_session_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/avatar-interaction-sessions"
    ]["post"]

    assert set(operation["responses"]) == {"201"}
    assert "security" not in operation


def test_yezul_frames_return_all_frames_ordered_by_id() -> None:
    db = Mock(spec=Session)
    db.scalars.return_value.all.return_value = [
        yezul_frame(
            id=31,
            title="미니멀",
            image_url="https://cdn.example.com/frames/YEZUL_FRAME_01.png",
        ),
        yezul_frame(
            id=32,
            title=None,
            image_url="https://cdn.example.com/frames/YEZUL_FRAME_02.png",
        ),
    ]

    response = request_yezul_frames(db)

    assert response.status_code == 200
    assert response.json() == {
        "yezulFrames": [
            {
                "id": 31,
                "title": "미니멀",
                "imageUrl": "https://cdn.example.com/frames/YEZUL_FRAME_01.png",
            },
            {
                "id": 32,
                "title": None,
                "imageUrl": "https://cdn.example.com/frames/YEZUL_FRAME_02.png",
            },
        ]
    }
    db.scalars.assert_called_once()


def test_yezul_frames_return_empty_list() -> None:
    db = Mock(spec=Session)
    db.scalars.return_value.all.return_value = []

    response = request_yezul_frames(db)

    assert response.status_code == 200
    assert response.json() == {"yezulFrames": []}


def test_yezul_frames_swagger_contract() -> None:
    operation = app.openapi()["paths"]["/api/v1/users/me/album/yezul-frames"]["get"]

    assert set(operation["responses"]) == {"200"}
    assert "security" not in operation


def test_save_avatar_interaction_session_updates_active_session() -> None:
    db = Mock(spec=Session)
    interaction_session = active_interaction_session()
    db.scalar.return_value = interaction_session

    response = save_avatar_interaction_session_request(db)

    assert response.status_code == 204
    assert response.content == b""
    assert interaction_session.status == AvatarInteractionSessionStatus.COMPLETED
    assert isinstance(interaction_session.ended_at, datetime)
    assert interaction_session.ended_at.tzinfo is None
    db.commit.assert_called_once()


def test_save_avatar_interaction_session_returns_404_for_unknown_session() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = save_avatar_interaction_session_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "AVATAR_INTERACTION_SESSION_NOT_FOUND",
        "message": "아바타 소환 세션을 찾을 수 없습니다.",
    }
    db.commit.assert_not_called()


def test_save_avatar_interaction_session_returns_409_when_status_completed() -> None:
    db = Mock(spec=Session)
    interaction_session = active_interaction_session()
    interaction_session.status = AvatarInteractionSessionStatus.COMPLETED
    db.scalar.return_value = interaction_session

    response = save_avatar_interaction_session_request(db)

    assert response.status_code == 409
    assert response.json() == {
        "code": "AVATAR_INTERACTION_SESSION_ALREADY_COMPLETED",
        "message": "이미 종료된 아바타 소환 세션입니다.",
    }
    db.commit.assert_not_called()


def test_save_avatar_interaction_session_returns_409_when_ended_at_exists() -> None:
    db = Mock(spec=Session)
    interaction_session = active_interaction_session()
    interaction_session.ended_at = datetime.fromisoformat("2026-08-13T12:05:00")
    db.scalar.return_value = interaction_session

    response = save_avatar_interaction_session_request(db)

    assert response.status_code == 409
    assert response.json()["code"] == "AVATAR_INTERACTION_SESSION_ALREADY_COMPLETED"
    db.commit.assert_not_called()


def test_save_avatar_interaction_session_rejects_invalid_path_with_common_400() -> None:
    db = Mock(spec=Session)

    response = save_avatar_interaction_session_request(
        db,
        avatar_interaction_session_id=0,
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.scalar.assert_not_called()


def test_save_avatar_interaction_session_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = active_interaction_session()
    db.commit.side_effect = RuntimeError("db failed")

    response = save_avatar_interaction_session_request(
        db,
        raise_server_exceptions=False,
    )

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_save_avatar_interaction_session_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/avatar-interaction-sessions/{avatarInteractionSessionId}"
    ]["patch"]

    assert set(operation["responses"]) == {"204", "404", "409"}
    assert "security" not in operation


def test_save_avatar_interaction_picture_uploads_image_and_adds_orm_model() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = active_interaction_session()

    with patch(
        "app.services.avatar.upload_avatar_interaction_picture",
        return_value=(
            "https://cdn.example.com/avatar_interaction_picture/1/1101/test.png"
        ),
    ) as upload:
        response = save_avatar_interaction_picture_request(db)

    assert response.status_code == 204
    assert response.content == b""
    upload.assert_called_once()
    assert upload.call_args.kwargs["user_id"] == 1
    assert upload.call_args.kwargs["avatar_interaction_session_id"] == 1101
    picture = db.add.call_args.args[0]
    assert isinstance(picture, AvatarInteractionPicture)
    assert picture.interaction_session_id == 1101
    assert picture.picture_img_url.endswith(
        "avatar_interaction_picture/1/1101/test.png"
    )
    assert picture.pictured_at == datetime.fromisoformat("2026-07-29T15:05:20")
    assert picture.deleted_at is None
    db.commit.assert_called_once()


def test_save_avatar_interaction_picture_returns_404_for_unknown_session() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    with patch("app.services.avatar.upload_avatar_interaction_picture") as upload:
        response = save_avatar_interaction_picture_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "AVATAR_INTERACTION_SESSION_NOT_FOUND",
        "message": "아바타 소환 세션을 찾을 수 없습니다.",
    }
    upload.assert_not_called()
    db.add.assert_not_called()


def test_save_avatar_interaction_picture_allows_completed_session() -> None:
    db = Mock(spec=Session)
    interaction_session = active_interaction_session()
    interaction_session.status = AvatarInteractionSessionStatus.COMPLETED
    interaction_session.ended_at = datetime.fromisoformat("2026-08-13T12:05:00")
    db.scalar.return_value = interaction_session

    with patch(
        "app.services.avatar.upload_avatar_interaction_picture",
        return_value="https://cdn.example.com/avatar_interaction_picture/test.png",
    ):
        response = save_avatar_interaction_picture_request(db)

    assert response.status_code == 204
    assert db.add.call_args.args[0].interaction_session_id == 1101


def test_save_avatar_interaction_picture_returns_400_for_unsupported_content_type() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = active_interaction_session()

    with patch("app.services.avatar.upload_avatar_interaction_picture") as upload:
        response = save_avatar_interaction_picture_request(
            db,
            content_type="image/gif",
        )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    upload.assert_not_called()


def test_save_avatar_interaction_picture_accepts_image_jpg_content_type() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = active_interaction_session()

    with patch(
        "app.services.avatar.upload_avatar_interaction_picture",
        return_value="https://cdn.example.com/avatar_interaction_picture/test.jpg",
    ) as upload:
        response = save_avatar_interaction_picture_request(
            db,
            content_type="image/jpg",
        )

    assert response.status_code == 204
    assert upload.call_args.kwargs["content_type"] == "image/jpg"


def test_save_avatar_interaction_picture_accepts_uppercase_jpeg_content_type() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = active_interaction_session()

    with patch(
        "app.services.avatar.upload_avatar_interaction_picture",
        return_value="https://cdn.example.com/avatar_interaction_picture/test.jpg",
    ) as upload:
        response = save_avatar_interaction_picture_request(
            db,
            content_type="IMAGE/JPEG",
        )

    assert response.status_code == 204
    assert upload.call_args.kwargs["content_type"] == "image/jpeg"


def test_save_avatar_interaction_picture_returns_400_when_required_field_missing() -> None:
    db = Mock(spec=Session)

    response = save_avatar_interaction_picture_request(db, data={})

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.scalar.assert_not_called()


def test_save_avatar_interaction_picture_uses_common_500_when_upload_fails() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = active_interaction_session()

    with patch(
        "app.services.avatar.upload_avatar_interaction_picture",
        side_effect=RuntimeError("azure failed"),
    ):
        response = save_avatar_interaction_picture_request(
            db,
            raise_server_exceptions=False,
        )

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "서버 내부 오류가 발생했습니다.",
    }
    db.add.assert_not_called()


def test_save_avatar_interaction_picture_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/avatar-interaction-sessions/{avatarInteractionSessionId}/pictures"
    ]["post"]

    assert set(operation["responses"]) == {"204", "400", "404"}
    assert "security" not in operation
