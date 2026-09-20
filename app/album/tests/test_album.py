"""앨범 조회 API 테스트."""

from datetime import date
from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.album.models import Album, Track
from app.core.tests.conftest import api_client
from app.main import app


def request_album(db: Mock):
    with api_client(db) as client:
        return client.get("/api/v1/album")


def request_album_track(db: Mock, track_id: int = 1):
    with api_client(db) as client:
        return client.get(f"/api/v1/tracks/{track_id}")


def ruby_album() -> Album:
    album = Album(
        id=1,
        title="Ruby",
        artist_name="Jennie",
        track_count=15,
        track_total_second=2498,
        cover_image_url=(
            "https://haniumstorage.blob.core.windows.net/hanium/"
            "album_cover_img/RUBY_cover_img.jpeg"
        ),
        release_date=date.fromisoformat("2025-03-07"),
    )
    album.tracks = [
        Track(
            id=2,
            track_number=2,
            title="like JENNIE",
            artist_name="Jennie",
            duration_seconds=124,
            is_title_track=True,
        ),
        Track(
            id=1,
            track_number=1,
            title="Intro : JANE (with FKJ)",
            artist_name="Jennie",
            duration_seconds=98,
            is_title_track=False,
        ),
    ]
    return album


def test_read_album_returns_album_and_tracks_ordered_by_track_number() -> None:
    db = Mock(spec=Session)
    db.scalar.side_effect = [12, ruby_album()]

    response = request_album(db)

    assert response.status_code == 200
    assert response.json() == {
        "album": {
            "id": 1,
            "title": "Ruby",
            "artistName": "Jennie",
            "trackCount": 15,
            "trackTotalSeconds": 2498,
            "coverImageUrl": (
                "https://haniumstorage.blob.core.windows.net/hanium/"
                "album_cover_img/RUBY_cover_img.jpeg"
            ),
            "releaseDate": "2025-03-07",
            "tracks": [
                {
                    "id": 1,
                    "trackNumber": 1,
                    "title": "Intro : JANE (with FKJ)",
                    "artistName": "Jennie",
                    "durationSeconds": 98,
                    "isTitleTrack": False,
                },
                {
                    "id": 2,
                    "trackNumber": 2,
                    "title": "like JENNIE",
                    "artistName": "Jennie",
                    "durationSeconds": 124,
                    "isTitleTrack": True,
                },
            ],
        }
    }


def test_read_album_returns_404_without_last_active_ownership() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = request_album(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CUBE_OWNERSHIP_NOT_FOUND",
        "message": "큐브 소유권 정보를 찾을 수 없습니다.",
    }
    db.scalar.assert_called_once()


def test_read_album_swagger_responses() -> None:
    operation = app.openapi()["paths"]["/api/v1/album"]["get"]

    assert set(operation["responses"]) == {"200", "404"}
    assert operation["tags"] == ["album"]
    assert operation["security"] == [{"HTTPBearer": []}]


def test_read_album_track_returns_track_playback_data() -> None:
    db = Mock(spec=Session)
    db.scalar.side_effect = [12, ruby_track()]

    response = request_album_track(db)

    assert response.status_code == 200
    assert response.json() == {
        "track": {
            "id": 1,
            "audioUrl": (
                "https://haniumstorage.blob.core.windows.net/hanium/"
                "album/album_track/song_intro.mp3"
            ),
            "durationSeconds": 98,
            "lyrics": "lyrics",
        }
    }


def test_read_album_track_returns_404_without_last_active_ownership() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = request_album_track(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CUBE_OWNERSHIP_NOT_FOUND",
        "message": "큐브 소유권 정보를 찾을 수 없습니다.",
    }
    db.scalar.assert_called_once()


def test_read_album_track_returns_404_when_track_does_not_exist() -> None:
    db = Mock(spec=Session)
    db.scalar.side_effect = [12, None]

    response = request_album_track(db, track_id=999)

    assert response.status_code == 404
    assert response.json() == {
        "code": "TRACK_NOT_FOUND",
        "message": "앨범 트랙을 찾을 수 없습니다.",
    }


def test_read_album_track_swagger_responses() -> None:
    operation = app.openapi()["paths"]["/api/v1/tracks/{trackId}"]["get"]

    assert set(operation["responses"]) == {"200", "404"}
    assert operation["tags"] == ["album"]
    assert operation["security"] == [{"HTTPBearer": []}]


def ruby_track() -> Track:
    return Track(
        id=1,
        album_id=1,
        title="Intro : JANE (with FKJ)",
        artist_name="Jennie",
        audio_url=(
            "https://haniumstorage.blob.core.windows.net/hanium/"
            "album/album_track/song_intro.mp3"
        ),
        duration_seconds=98,
        lyrics="lyrics",
        track_number=1,
        is_title_track=False,
    )
