"""ERD에 정의된 제한 값과 SQLAlchemy Enum 타입 생성 함수."""

from enum import StrEnum

from sqlalchemy import Enum as SqlEnum


class LoginProvider(StrEnum):
    EMAIL = "EMAIL"
    GOOGLE = "GOOGLE"
    APPLE = "APPLE"


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    WITHDRAWN = "WITHDRAWN"
    SUSPENDED = "SUSPENDED"


class AuthSessionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


class CubeStatus(StrEnum):
    UNREGISTERED = "UNREGISTERED"
    OWNED = "OWNED"
    TRADE_PENDING = "TRADE_PENDING"
    DISABLED = "DISABLED"


class VerificationStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class OwnershipStatus(StrEnum):
    ACTIVE = "ACTIVE"
    TRANSFERRED = "TRANSFERRED"
    REVOKED = "REVOKED"


class LevelName(StrEnum):
    INTRO = "Intro"
    FRIEND = "Friend"
    CLOSE = "Close"
    SPECIAL = "Special"


class RewardType(StrEnum):
    AFFINITY_POINT = "AFFINITY_POINT"
    CONVERSATION_COUNT = "CONVERSATION_COUNT"
    COMMENT_TYPE = "COMMENT_TYPE"
    SPECIAL_COMMENT = "SPECIAL_COMMENT"
    AVATAR_FIRST_TALK = "AVATAR_FIRST_TALK"
    BADGE = "BADGE"


class MissionType(StrEnum):
    DAILY = "DAILY"
    EVENT = "EVENT"


class TargetAction(StrEnum):
    HOME_VIEW = "HOME_VIEW"
    CONVERSATION = "CONVERSATION"
    ALBUM_PLAY = "ALBUM_PLAY"
    OPEN_GALLERY = "OPEN_GALLERY"
    COMMUNITY_POST = "COMMUNITY_POST"
    ALBUM_CONVERSATION = "ALBUM_CONVERSATION"
    PLAY_MUSIC_VIDEO = "PLAY_MUSIC_VIDEO"


class MissionProgressStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REWARDED = "REWARDED"


class NotificationType(StrEnum):
    ALL = "ALL"
    MISSION = "MISSION"
    EVENT = "EVENT"
    MARKET = "MARKET"


class VideoType(StrEnum):
    MUSIC_VIDEO = "MUSIC_VIDEO"
    CONCERT_VIDEO = "CONCERT_VIDEO"


class PlaybackStatus(StrEnum):
    PLAYING = "PLAYING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ViewMode(StrEnum):
    NORMAL = "NORMAL"
    AR = "AR"


class PlayMode(StrEnum):
    NORMAL = "NORMAL"
    SPECIAL = "SPECIAL"


class AlbumImageType(StrEnum):
    ALBUM_IMAGE = "ALBUM_IMAGE"
    CONCERT_STILLCUT = "CONCERT_STILLCUT"
    YEZUL_FRAME = "YEZUL_FRAME"


class ConversationType(StrEnum):
    TEXT = "TEXT"
    VOICE = "VOICE"


class ConversationSessionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    NOT_ACTIVE = "NOT_ACTIVE"


class SenderType(StrEnum):
    USER = "USER"
    AVATAR = "AVATAR"


class MessageStatus(StrEnum):
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"


class ViolationType(StrEnum):
    PROFANITY = "PROFANITY"
    SEXUAL = "SEXUAL"
    THREAT = "THREAT"


class ReportReason(StrEnum):
    INCORRECT_PERSONA = "INCORRECT_PERSONA"
    HALLUCINATION = "HALLUCINATION"
    INAPPROPRIATE_EXPRESSION = "INAPPROPRIATE_EXPRESSION"
    IMPERSONATION_OR_PRIVATE = "IMPERSONATION_OR_PRIVATE"


class InteractionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


def enum_type[EnumT: StrEnum](
    enum_class: type[EnumT], *, name: str, length: int
) -> SqlEnum:
    """ERD의 VARCHAR Enum을 VARCHAR + CHECK 제약조건으로 생성합니다."""
    return SqlEnum(
        enum_class,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
        length=length,
    )
