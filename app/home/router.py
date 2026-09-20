"""홈 도메인 API 라우터."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.core.schemas import ErrorResponse
from app.home.schemas import (
    HomeNotificationFilter,
    HomeNotificationsResponse,
    HomeResponse,
)
from app.home.service import (
    NOTIFICATION_PAGE_SIZE,
    get_home,
    get_notifications,
    read_all_notifications,
    read_notification,
)

router = APIRouter()


@router.get(
    "/home",
    response_model=HomeResponse,
    summary="홈 정보 조회",
    description="현재 사용자의 홈 화면 정보를 조회합니다.",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "소유권은 존재하지만 ACTIVE 상태가 아님",
            "content": {
                "application/json": {
                    "example": {
                        "code": "CUBE_OWNERSHIP_FORBIDDEN",
                        "message": "해당 큐브 소유권 정보를 조회할 권한이 없습니다.",
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "큐브 소유권 또는 친밀도 정보가 존재하지 않음",
            "content": {
                "application/json": {
                    "examples": {
                        "cubeOwnershipNotFound": {
                            "summary": "큐브 소유권 없음",
                            "value": {
                                "code": "CUBE_OWNERSHIP_NOT_FOUND",
                                "message": "큐브 소유권 정보를 찾을 수 없습니다.",
                            },
                        },
                        "cubeAffinityNotFound": {
                            "summary": "큐브 친밀도 없음",
                            "value": {
                                "code": "CUBE_AFFINITY_NOT_FOUND",
                                "message": "큐브 친밀도 정보를 찾을 수 없습니다.",
                            },
                        },
                    }
                }
            },
        },
    },
)
def read_home(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> HomeResponse:
    """GET /api/v1/users/me/home"""
    return get_home(db=db, current_user_id=current_user_id)


@router.get(
    "/notifications",
    response_model=HomeNotificationsResponse,
    summary="알림 목록 조회",
    description=(
        "현재 사용자의 알림을 조회 유형으로 걸러 전송 시각 내림차순으로 "
        "요청한 size 단위로 조회합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "지원하지 않는 type 또는 잘못된 page·size 값",
            "content": {
                "application/json": {
                    "example": {
                        "code": "INVALID_REQUEST",
                        "message": "요청값이 올바르지 않습니다.",
                    }
                }
            },
        },
    },
)
def read_notifications(
    notification_type: Annotated[HomeNotificationFilter, Query(alias="type")],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    page: Annotated[int, Query(ge=0)] = 0,
    size: Annotated[int, Query(ge=1)] = NOTIFICATION_PAGE_SIZE,
) -> HomeNotificationsResponse:
    """GET /api/v1/users/me/notifications"""
    return get_notifications(
        db=db,
        current_user_id=current_user_id,
        notification_type=notification_type,
        page=page,
        size=size,
    )


@router.patch(
    "/notifications/{notificationId}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="개별 알림 읽음 처리",
    description=(
        "현재 사용자의 알림 한 건을 읽음 상태로 변경합니다. "
        "이미 읽은 알림을 다시 요청해도 성공하며 기존 읽은 시각을 유지합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "알림이 없거나 현재 사용자의 알림이 아님",
            "content": {
                "application/json": {
                    "example": {
                        "code": "NOTIFICATION_NOT_FOUND",
                        "message": "알림을 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def update_notification_read(
    notification_id: Annotated[int, Path(alias="notificationId", ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> Response:
    """PATCH /api/v1/users/me/notifications/{notificationId}/read"""
    read_notification(
        db=db,
        current_user_id=current_user_id,
        notification_id=notification_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/notifications/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="전체 알림 읽음 처리",
    description=(
        "현재 사용자의 미읽음 알림을 알림 유형과 관계없이 모두 읽음 상태로 "
        "변경합니다. 미읽음 알림이 없어도 성공합니다."
    ),
)
def update_all_notifications_read(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> Response:
    """PATCH /api/v1/users/me/notifications/read-all"""
    read_all_notifications(db=db, current_user_id=current_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
