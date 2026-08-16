"""갤러리 조회 API 테스트."""

from collections.abc import Iterator
from datetime import date, datetime
from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models.avatar import AvatarInteractionPicture
from app.models.stage import Stage, StageCapture, StageSession
from app.models.track import Track, TrackCapture, TrackSession


def delete_gallery_item_request(
    db: Mock,
    source_type: str = "STAGE_CAPTURE",
    gallery_item_id: int = 1,
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
            return client.delete(
                f"/api/v1/users/me/gallery/{source_type}/{gallery_item_id}"
            )
    finally:
        app.dependency_overrides.clear()


def request_gallery_ar_experience(
    db: Mock,
    source_type: str = "STAGE_CAPTURE",
    gallery_item_id: int = 1,
):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            return client.get(
                "/api/v1/users/me/gallery/"
                f"{source_type}/{gallery_item_id}/ar-experience"
            )
    finally:
        app.dependency_overrides.clear()


def request_gallery(db: Mock, query: str = ""):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            return client.get(f"/api/v1/users/me/gallery{query}")
    finally:
        app.dependency_overrides.clear()


def gallery_rows(*rows: dict):
    result = Mock()
    result.mappings.return_value.all.return_value = list(rows)
    return result


def make_row(
    *,
    id: int,
    source_type: str,
    category: str,
    image_url: str,
    display_date: date,
    sort_at: datetime | date,
):
    return {
        "id": id,
        "source_type": source_type,
        "category": category,
        "image_url": image_url,
        "display_date": display_date,
        "sort_at": sort_at,
        "sort_id": id,
    }


def test_gallery_returns_merged_items_sorted_by_date_and_id() -> None:
    db = Mock(spec=Session)
    db.execute.return_value = gallery_rows(
        make_row(
            id=1,
            source_type="STAGE_CAPTURE",
            category="CAPTURE",
            image_url="stage_capture_001",
            display_date=date(2026, 8, 7),
            sort_at=datetime(2026, 8, 7, 10, 30),  # noqa: DTZ001
        ),
        make_row(
            id=2,
            source_type="TRACK_CAPTURE",
            category="CAPTURE",
            image_url="track_capture_002",
            display_date=date(2026, 8, 7),
            sort_at=datetime(2026, 8, 7, 11, 10),  # noqa: DTZ001
        ),
        make_row(
            id=3,
            source_type="ALBUM_IMAGE",
            category="CONCERT_STILLCUT",
            image_url="album_image_003",
            display_date=date(2026, 8, 1),
            sort_at=date(2026, 8, 1),
        ),
    )

    response = request_gallery(db)

    assert response.status_code == 200
    assert response.json() == {
        "galleryItems": [
            {
                "id": 2,
                "sourceType": "TRACK_CAPTURE",
                "category": "CAPTURE",
                "imageUrl": "track_capture_002",
                "displayDate": "2026-08-07",
            },
            {
                "id": 1,
                "sourceType": "STAGE_CAPTURE",
                "category": "CAPTURE",
                "imageUrl": "stage_capture_001",
                "displayDate": "2026-08-07",
            },
            {
                "id": 3,
                "sourceType": "ALBUM_IMAGE",
                "category": "CONCERT_STILLCUT",
                "imageUrl": "album_image_003",
                "displayDate": "2026-08-01",
            },
        ],
        "pagination": {"page": 0, "size": 20, "hasNext": False},
    }
    db.execute.assert_called_once()


def test_gallery_uses_requested_size_and_has_next() -> None:
    db = Mock(spec=Session)
    db.execute.return_value = gallery_rows(
        *[
            make_row(
                id=index,
                source_type="ALBUM_IMAGE",
                category="ALBUM",
                image_url=f"album_image_{index}",
                display_date=date(2026, 8, 1),
                sort_at=date(2026, 8, 1),
            )
            for index in range(1, 22)
        ]
    )

    response = request_gallery(db, "?category=ALBUM&page=0&size=10")

    assert response.status_code == 200
    body = response.json()
    assert len(body["galleryItems"]) == 10
    assert body["pagination"] == {"page": 0, "size": 10, "hasNext": True}


def test_gallery_requested_size_changes_page_offset() -> None:
    db = Mock(spec=Session)
    db.execute.return_value = gallery_rows(
        *[
            make_row(
                id=index,
                source_type="ALBUM_IMAGE",
                category="ALBUM",
                image_url=f"album_image_{index}",
                display_date=date(2026, 8, 1),
                sort_at=date(2026, 8, 1),
            )
            for index in range(1, 22)
        ]
    )

    response = request_gallery(db, "?category=ALBUM&page=1&size=10")

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["galleryItems"]] == list(range(11, 21))
    assert body["pagination"] == {"page": 1, "size": 10, "hasNext": True}


def test_gallery_sorts_album_images_by_id_ascending() -> None:
    db = Mock(spec=Session)
    db.execute.return_value = gallery_rows(
        make_row(
            id=3,
            source_type="ALBUM_IMAGE",
            category="ALBUM",
            image_url="album_image_003",
            display_date=date(2026, 9, 1),
            sort_at=date(2026, 9, 1),
        ),
        make_row(
            id=1,
            source_type="ALBUM_IMAGE",
            category="ALBUM",
            image_url="album_image_001",
            display_date=date(2026, 7, 1),
            sort_at=date(2026, 7, 1),
        ),
    )

    response = request_gallery(db, "?category=ALBUM")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["galleryItems"]] == [1, 3]


def test_gallery_rejects_size_less_than_one_with_common_400() -> None:
    db = Mock(spec=Session)

    response = request_gallery(db, "?size=0")

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.execute.assert_not_called()


def test_gallery_swagger_contract() -> None:
    operation = app.openapi()["paths"]["/api/v1/users/me/gallery"]["get"]

    assert set(operation["responses"]) == {"200"}
    assert "security" not in operation


def test_gallery_stage_ar_experience_returns_origin_stage() -> None:
    db = Mock(spec=Session)
    stage = Stage(
        id=1,
        title="SOLO",
        video_url="stage_video",
        duration_seconds=222,
    )
    session = StageSession(stage=stage)
    capture = StageCapture(
        id=701,
        stage_session=session,
        captured_position_seconds=74,
    )
    db.scalar.return_value = capture

    response = request_gallery_ar_experience(
        db,
        source_type="STAGE_CAPTURE",
        gallery_item_id=701,
    )

    assert response.status_code == 200
    assert response.json() == {
        "galleryItem": {
            "contentType": "STAGE",
            "requiredMode": "AR",
            "startPositionSeconds": 74,
            "stage": {
                "id": 1,
                "title": "SOLO",
                "videoUrl": "stage_video",
                "durationSeconds": 222,
            },
        }
    }


def test_gallery_track_ar_experience_returns_origin_track() -> None:
    db = Mock(spec=Session)
    track = Track(
        id=101,
        title="SOLO",
        audio_url="track_audio",
        duration_seconds=179,
    )
    session = TrackSession(track=track)
    capture = TrackCapture(
        id=801,
        track_session=session,
        captured_position_seconds=35,
    )
    db.scalar.return_value = capture

    response = request_gallery_ar_experience(
        db,
        source_type="TRACK_CAPTURE",
        gallery_item_id=801,
    )

    assert response.status_code == 200
    assert response.json() == {
        "galleryItem": {
            "contentType": "TRACK",
            "requiredMode": "SPECIAL",
            "startPositionSeconds": 35,
            "track": {
                "id": 101,
                "title": "SOLO",
                "audioUrl": "track_audio",
                "durationSeconds": 179,
            },
        }
    }


def test_gallery_ar_experience_rejects_unsupported_source_type() -> None:
    db = Mock(spec=Session)

    response = request_gallery_ar_experience(db, source_type="ALBUM_IMAGE")

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.scalar.assert_not_called()


def test_gallery_ar_experience_returns_404_when_capture_is_missing() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = request_gallery_ar_experience(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "GALLERY_ITEM_NOT_FOUND",
        "message": "갤러리 항목을 찾을 수 없습니다.",
    }


def test_gallery_ar_experience_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/gallery/{sourceType}/{galleryItemId}/ar-experience"
    ]["get"]

    assert set(operation["responses"]) == {"200", "400", "404"}
    assert "security" not in operation


def test_delete_gallery_stage_capture_soft_deletes_item() -> None:
    db = Mock(spec=Session)
    capture = StageCapture(id=701, deleted_at=None)
    db.scalar.return_value = capture

    response = delete_gallery_item_request(
        db,
        source_type="STAGE_CAPTURE",
        gallery_item_id=701,
    )

    assert response.status_code == 204
    assert isinstance(capture.deleted_at, datetime)
    assert capture.deleted_at.tzinfo is None
    db.commit.assert_called_once()


def test_delete_gallery_track_capture_soft_deletes_item() -> None:
    db = Mock(spec=Session)
    capture = TrackCapture(id=801, deleted_at=None)
    db.scalar.return_value = capture

    response = delete_gallery_item_request(
        db,
        source_type="TRACK_CAPTURE",
        gallery_item_id=801,
    )

    assert response.status_code == 204
    assert isinstance(capture.deleted_at, datetime)
    db.commit.assert_called_once()


def test_delete_gallery_interaction_capture_soft_deletes_item() -> None:
    db = Mock(spec=Session)
    picture = AvatarInteractionPicture(id=901, deleted_at=None)
    db.scalar.return_value = picture

    response = delete_gallery_item_request(
        db,
        source_type="INTERACTION_CAPTURE",
        gallery_item_id=901,
    )

    assert response.status_code == 204
    assert isinstance(picture.deleted_at, datetime)
    db.commit.assert_called_once()


def test_delete_gallery_item_rejects_non_capture_source_type() -> None:
    db = Mock(spec=Session)

    response = delete_gallery_item_request(db, source_type="ALBUM_IMAGE")

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.scalar.assert_not_called()


def test_delete_gallery_item_returns_404_when_item_is_missing() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = delete_gallery_item_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "GALLERY_ITEM_NOT_FOUND",
        "message": "삭제할 갤러리 항목을 찾을 수 없습니다.",
    }
    db.commit.assert_not_called()


def test_delete_gallery_item_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = StageCapture(id=701, deleted_at=None)
    db.commit.side_effect = RuntimeError("db failed")

    response = delete_gallery_item_request(db, raise_server_exceptions=False)

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_delete_gallery_item_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/gallery/{sourceType}/{galleryItemId}"
    ]["delete"]

    assert set(operation["responses"]) == {"204", "404"}
    assert "security" not in operation
