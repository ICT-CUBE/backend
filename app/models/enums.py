"""DB에 저장되는 고정 코드값.

DDL의 CHECK 제약 조건과 같은 값을 한곳에서 관리합니다.
"""

from enum import StrEnum


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


class CubeVerificationStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class OwnershipStatus(StrEnum):
    ACTIVE = "ACTIVE"
    TRANSFERRED = "TRANSFERRED"
    REVOKED = "REVOKED"


class RewardItemType(StrEnum):
    AFFINITY_POINT = "AFFINITY_POINT"
    CONVERSATION_COUNT = "CONVERSATION_COUNT"
    COMMENT_TYPE = "COMMENT_TYPE"
    SPECIAL_COMMENT = "SPECIAL_COMMENT"
    AVATAR_FIRST_TALK = "AVATAR_FIRST_TALK"
    BADGE = "BADGE"


class LevelName(StrEnum):
    INTRO = "Intro"
    FRIEND = "Friend"
    CLOSE = "Close"
    SPECIAL = "Special"


class MissionType(StrEnum):
    DAILY = "DAILY"
    EVENT = "EVENT"


class MissionTargetAction(StrEnum):
    HOME_VIEW = "HOME_VIEW"
    CONVERSATION = "CONVERSATION"
    ALBUM_PLAY = "ALBUM_PLAY"
    OPEN_GALLERY = "OPEN_GALLERY"
    COMMUNITY_POST = "COMMUNITY_POST"
    SUMMON_AVATAR = "SUMMON_AVATAR"
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


class StageVideoType(StrEnum):
    MUSIC_VIDEO = "MUSIC_VIDEO"
    CONCERT_VIDEO = "CONCERT_VIDEO"


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


class ConversationType(StrEnum):
    TEXT = "TEXT"
    VOICE = "VOICE"


class AvatarConversationSessionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    NOT_ACTIVE = "NOT_ACTIVE"


class ConversationMessageSenderType(StrEnum):
    USER = "USER"
    AVATAR = "AVATAR"


class ConversationMessageStatus(StrEnum):
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"


class ConversationMessageViolationType(StrEnum):
    PROFANITY = "PROFANITY"
    SEXUAL = "SEXUAL"
    THREAT = "THREAT"


class ConversationReportReason(StrEnum):
    INCORRECT_PERSONA = "INCORRECT_PERSONA"
    HALLUCINATION = "HALLUCINATION"
    INAPPROPRIATE_EXPRESSION = "INAPPROPRIATE_EXPRESSION"
    IMPERSONATION_OR_PRIVATE = "IMPERSONATION_OR_PRIVATE"


class BoardType(StrEnum):
    FREE = "FREE"
    CERTIFICATION = "CERTIFICATION"


class PostStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
    REPORTED = "REPORTED"


class CommentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
    REPORTED = "REPORTED"


class SellListingStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SOLD = "SOLD"
    DELETED = "DELETED"


class TradeStatus(StrEnum):
    PAID = "PAID"
    SENT = "SENT"
    SHIPPING = "SHIPPING"
    DELIVERED = "DELIVERED"
    COMPLETED = "COMPLETED"
