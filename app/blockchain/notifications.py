"""블록체인 완료 알림 처리."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.blockchain.models import BlockchainOperation
from app.blockchain.schemas import (
    BlockchainNotificationRequest,
    BlockchainNotificationResponse,
)
from app.core.enums import BlockchainOperationStatus

logger = logging.getLogger(__name__)


def record_notification(
    *,
    db: Session,
    notification: BlockchainNotificationRequest,
) -> BlockchainNotificationResponse:
    """완료 알림으로 작업을 확정 처리합니다. 중복 알림은 다시 처리하지 않습니다."""
    if _is_already_recorded(db=db, notification_id=notification.notification_id):
        return _accepted(notification=notification, duplicate=True)

    operation = db.scalar(
        select(BlockchainOperation)
        .where(BlockchainOperation.operation_id == notification.operation_id)
        .limit(1)
        .with_for_update()
    )
    if operation is None:
        # 우리가 만들지 않은 작업의 알림도 재전송을 멈추도록 수락만 합니다.
        logger.info(
            "unknown operation notification: operation_id=%s",
            notification.operation_id,
        )
        db.rollback()
        return _accepted(notification=notification, duplicate=False)

    operation.notification_id = notification.notification_id
    if operation.status != BlockchainOperationStatus.CONFIRMED:
        # 확정 대기가 시간을 넘겨 REQUESTED로 남아 있던 작업을 여기서 확정합니다.
        operation.status = BlockchainOperationStatus.CONFIRMED
        operation.tx_hash = notification.tx_hash
        operation.final_owner_address = notification.final_owner_address

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return _accepted(notification=notification, duplicate=False)


def _is_already_recorded(*, db: Session, notification_id: str) -> bool:
    recorded_id = db.scalar(
        select(BlockchainOperation.id)
        .where(BlockchainOperation.notification_id == notification_id)
        .limit(1)
    )
    return recorded_id is not None


def _accepted(
    *,
    notification: BlockchainNotificationRequest,
    duplicate: bool,
) -> BlockchainNotificationResponse:
    return BlockchainNotificationResponse(
        notification_id=notification.notification_id,
        accepted=True,
        duplicate=duplicate,
    )
