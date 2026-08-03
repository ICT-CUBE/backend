"""모든 ORM 모델을 import해 Base.metadata와 Alembic에 등록합니다."""

from app.models.album import (
    Album,
    AlbumImage,
    Stage,
    StageCapture,
    StageSession,
    Track,
    TrackCapture,
    TrackSession,
)
from app.models.conversation import (
    AvatarConversationImage,
    AvatarConversationMessage,
    AvatarConversationSession,
    AvatarInteractionPicture,
    AvatarInteractionSession,
    ConversationReport,
)
from app.models.cube import Affinity, Cube, CubeOwnership, CubeVerification
from app.models.reward import Level, Mission, MissionProgress, RewardItem, UserReward
from app.models.user import AuthSession, Notification, User, UserSetting

__all__ = [
    "Affinity",
    "Album",
    "AlbumImage",
    "AuthSession",
    "AvatarConversationImage",
    "AvatarConversationMessage",
    "AvatarConversationSession",
    "AvatarInteractionPicture",
    "AvatarInteractionSession",
    "ConversationReport",
    "Cube",
    "CubeOwnership",
    "CubeVerification",
    "Level",
    "Mission",
    "MissionProgress",
    "Notification",
    "RewardItem",
    "Stage",
    "StageCapture",
    "StageSession",
    "Track",
    "TrackCapture",
    "TrackSession",
    "User",
    "UserReward",
    "UserSetting",
]
