"""홈 화면에 필요한 사용자·큐브·친밀도 조회와 알림 조회·읽음 처리 로직."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import case, select, update
from sqlalchemy.orm import Session, joinedload

from app.affinity.models import Affinity, Level
from app.core.enums import MissionTargetAction, NotificationType, OwnershipStatus
from app.core.exceptions import ApiError
from app.cube.models import CubeOwnership
from app.home.schemas import (
    HomeAffinityResponse,
    HomeCubeOwnershipResponse,
    HomeCubeResponse,
    HomeLevelResponse,
    HomeNotificationFilter,
    HomeNotificationItemResponse,
    HomeNotificationsResponse,
    HomePaginationResponse,
    HomeResponse,
    HomeUserResponse,
)
from app.mission.progress import increase_mission_progress
from app.user.models import Notification

KOREA_TIMEZONE = timezone(timedelta(hours=9))
NOTIFICATION_PAGE_SIZE = 20


def get_home(*, db: Session, current_user_id: int) -> HomeResponse:
    """현재 사용자의 홈 정보를 ORM으로 조회합니다."""
    # 홈 응답에 필요한 연관 객체를 한 번에 가져옵니다. ACTIVE 소유권이 있으면
    # 우선하고, 없으면 최근 비활성 소유권을 반환해 403과 404를 구분합니다.
    ownership = db.scalars(
        select(CubeOwnership)
        .where(CubeOwnership.user_id == current_user_id)
        .options(
            joinedload(CubeOwnership.user),
            joinedload(CubeOwnership.cube),
            joinedload(CubeOwnership.affinity).joinedload(Affinity.level_info),
        )
        .order_by(
            case(
                (CubeOwnership.ownership_status == OwnershipStatus.ACTIVE, 0),
                else_=1,
            ),
            CubeOwnership.is_last_accessed.desc(),
            CubeOwnership.acquired_at.desc(),
        )
        .limit(1)
    ).first()

    if ownership is None:
        raise ApiError(
            status_code=404,
            code="CUBE_OWNERSHIP_NOT_FOUND",
            message="큐브 소유권 정보를 찾을 수 없습니다.",
        )
    if ownership.ownership_status != OwnershipStatus.ACTIVE:
        raise ApiError(
            status_code=403,
            code="CUBE_OWNERSHIP_FORBIDDEN",
            message="해당 큐브 소유권 정보를 조회할 권한이 없습니다.",
        )

    user = ownership.user
    cube = ownership.cube
    affinity = ownership.affinity
    if affinity is None:
        raise ApiError(
            status_code=404,
            code="CUBE_AFFINITY_NOT_FOUND",
            message="큐브 친밀도 정보를 찾을 수 없습니다.",
        )
    level = affinity.level_info
    next_level_xp = db.scalar(
        select(Level.level_xp)
        .where(Level.level > level.level)
        .order_by(Level.level.asc())
        .limit(1)
    )

    response = HomeResponse(
        user=HomeUserResponse(
            id=user.id,
            profile_character_img_url=user.profile_character_img_url,
        ),
        cube_ownership=HomeCubeOwnershipResponse(
            id=ownership.id,
            avatar_nickname=ownership.avatar_nickname,
            acquired_at=ownership.acquired_at,
        ),
        cube=HomeCubeResponse(id=cube.id, artist_name=cube.artist_name),
        affinity=HomeAffinityResponse(
            id=affinity.id,
            current_xp=affinity.current_xp,
            level=HomeLevelResponse(
                id=level.id,
                level=level.level,
                level_name=level.level_name.value,
                level_xp=(
                    next_level_xp if next_level_xp is not None else level.level_xp
                ),
            ),
        ),
    )
    # 응답을 먼저 만들어 두어야 commit 후 만료된 객체를 다시 조회하지 않습니다.
    try:
        increase_mission_progress(
            db=db,
            current_user_id=current_user_id,
            target_action=MissionTargetAction.HOME_VIEW,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return response


def get_notifications(
    *,
    db: Session,
    current_user_id: int,
    notification_type: HomeNotificationFilter,
    page: int,
    size: int,
) -> HomeNotificationsResponse:
    """현재 사용자의 알림을 전송 시각 내림차순으로 한 페이지 조회합니다."""
    statement = select(Notification).where(Notification.user_id == current_user_id)
    if notification_type != HomeNotificationFilter.ALL:
        statement = statement.where(
            Notification.notification_type == NotificationType(notification_type)
        )

    # 다음 페이지 존재 여부를 판단하려고 한 건을 더 조회합니다.
    rows = db.scalars(
        statement.order_by(Notification.sent_at.desc(), Notification.id.desc())
        .offset(page * size)
        .limit(size + 1)
    ).all()

    return HomeNotificationsResponse(
        notifications=[
            HomeNotificationItemResponse(
                id=notification.id,
                notification_type=notification.notification_type,
                title=notification.title,
                content=notification.content,
                is_read=notification.is_read,
                sent_at=notification.sent_at,
            )
            for notification in rows[:size]
        ],
        pagination=HomePaginationResponse(
            page=page,
            size=size,
            has_next=len(rows) > size,
        ),
    )


def read_notification(
    *,
    db: Session,
    current_user_id: int,
    notification_id: int,
) -> None:
    """현재 사용자의 알림 한 건을 읽음 상태로 저장합니다."""
    # 같은 알림에 대한 동시 요청이 read_at을 덮어쓰지 않게 행을 잠급니다.
    notification = db.scalar(
        select(Notification)
        .where(
            Notification.id == notification_id,
            Notification.user_id == current_user_id,
        )
        .limit(1)
        .with_for_update()
    )
    if notification is None:
        raise ApiError(
            status_code=404,
            code="NOTIFICATION_NOT_FOUND",
            message="알림을 찾을 수 없습니다.",
        )
    # 이미 읽은 알림은 기존 read_at을 유지합니다.
    if notification.is_read:
        return

    notification.is_read = True
    notification.read_at = datetime.now(KOREA_TIMEZONE).replace(tzinfo=None)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def read_all_notifications(*, db: Session, current_user_id: int) -> None:
    """현재 사용자의 미읽음 알림을 한 번의 일괄 수정으로 읽음 처리합니다."""
    # 처리 대상이 모두 같은 read_at을 갖도록 시각을 한 번만 만듭니다.
    read_at = datetime.now(KOREA_TIMEZONE).replace(tzinfo=None)

    try:
        db.execute(
            update(Notification)
            .where(
                Notification.user_id == current_user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True, read_at=read_at)
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
