"""앨범 도메인 트랙 재생 세션 API 요청·응답 스키마."""

from datetime import date
from enum import StrEnum

from app.models.enums import TrackPlayMode
from app.schemas.base import ApiSchema


class AlbumTrackResponse(ApiSchema):
    id: int
    track_number: int
    title: str
    artist_name: str
    duration_seconds: int
    is_title_track: bool


class AlbumInfoResponse(ApiSchema):
    id: int
    title: str
    artist_name: str
    track_count: int
    track_total_seconds: int
    cover_image_url: str
    release_date: date
    tracks: list[AlbumTrackResponse]


class AlbumResponse(ApiSchema):
    album: AlbumInfoResponse


class AlbumTrackDetailResponse(ApiSchema):
    id: int
    audio_url: str
    duration_seconds: int
    lyrics: str


class AlbumTrackDetailGetResponse(ApiSchema):
    track: AlbumTrackDetailResponse


class TrackSessionCreateRequest(ApiSchema):
    play_mode: TrackPlayMode


class TrackSessionResponse(ApiSchema):
    id: int
    play_mode: TrackPlayMode


class TrackSessionCreateResponse(ApiSchema):
    track_session: TrackSessionResponse


class TrackSessionEndStatus(StrEnum):
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TrackSessionUpdateRequest(ApiSchema):
    # 숫자 범위는 검증하지 않고 세 필드가 전달됐는지만 확인합니다.
    status: TrackSessionEndStatus
    last_position_seconds: int
    viewed_seconds: int
