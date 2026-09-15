"""서비스에서 사용하는 SQLAlchemy ORM 모델.

도메인마다 흩어진 모델을 한곳에서 임포트해, 다른 도메인 모델을 문자열로 참조하는
관계도 매퍼 설정 시점에 해석될 수 있게 합니다.
"""

from app.affinity.models import Affinity, Level
from app.album.models import Album, AlbumImage, Track, TrackCapture, TrackSession
from app.avatar.models import AvatarInteractionPicture, AvatarInteractionSession
from app.blockchain.models import BlockchainOperation
from app.community.models import Comment, CommentLike, Post, PostLike, PostMedia
from app.conversation.models import (
    AvatarConversationMessage,
    AvatarConversationSession,
    ConversationReport,
)
from app.cube.models import Cube, CubeOwnership, CubeVerification
from app.market.models import (
    DigitalCertificate,
    ListingMedia,
    SellingListLike,
    SellListing,
    Trade,
)
from app.mission.models import Mission, MissionProgress, RewardItem, UserReward
from app.stage.models import Stage, StageCapture, StageSession
from app.user.models import Notification, User, UserSetting

__all__ = [
    "Affinity",
    "Album",
    "AlbumImage",
    "AvatarConversationMessage",
    "AvatarConversationSession",
    "AvatarInteractionPicture",
    "AvatarInteractionSession",
    "BlockchainOperation",
    "Comment",
    "CommentLike",
    "ConversationReport",
    "Cube",
    "CubeOwnership",
    "CubeVerification",
    "DigitalCertificate",
    "Level",
    "ListingMedia",
    "Mission",
    "MissionProgress",
    "Notification",
    "Post",
    "PostLike",
    "PostMedia",
    "RewardItem",
    "SellListing",
    "SellingListLike",
    "Stage",
    "StageCapture",
    "StageSession",
    "Track",
    "TrackCapture",
    "TrackSession",
    "Trade",
    "User",
    "UserReward",
    "UserSetting",
]
