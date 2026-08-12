"""DB에 저장되는 고정 코드값.

DDL의 CHECK 제약 조건과 같은 값을 한곳에서 관리합니다.
"""

from enum import StrEnum


class OwnershipStatus(StrEnum):
    ACTIVE = "ACTIVE"
    TRANSFERRED = "TRANSFERRED"
    REVOKED = "REVOKED"


class LevelName(StrEnum):
    INTRO = "Intro"
    FRIEND = "Friend"
    CLOSE = "Close"
    SPECIAL = "Special"


class StageViewMode(StrEnum):
    NORMAL = "NORMAL"
    AR = "AR"


class StageSessionStatus(StrEnum):
    PLAYING = "PLAYING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TrackPlayMode(StrEnum):
    NORMAL = "NORMAL"
    SPECIAL = "SPECIAL"


class TrackSessionStatus(StrEnum):
    PLAYING = "PLAYING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AlbumImageType(StrEnum):
    ALBUM_IMAGE = "ALBUM_IMAGE"
    CONCERT_STILLCUT = "CONCERT_STILLCUT"
    YEZUL_FRAME = "YEZUL_FRAME"


class AvatarInteractionSessionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
