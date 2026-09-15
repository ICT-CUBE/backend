"""구매 확정 시 NFT 이전 처리."""

import logging
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.blockchain import client
from app.blockchain.errors import BlockchainError
from app.blockchain.mint import to_token_id
from app.blockchain.models import BlockchainOperation
from app.core.enums import BlockchainOperationStatus, BlockchainOperationType

TOKEN_STANDARD = "ERC-721"

logger = logging.getLogger(__name__)


def transfer_cube_nft(
    *,
    db: Session,
    trade_id: int,
    seller_user_id: int,
    buyer_user_id: int,
    serial_number: str,
) -> dict[str, str]:
    """NFT를 구매자에게 이전하고 디지털 인증서에 넣을 값을 반환합니다.

    Mint와 달리 실패를 호출자에게 알립니다. 구매 확정 API가 오류로 응답해야 하기 때문입니다.
    """
    operation = BlockchainOperation(
        operation_type=BlockchainOperationType.TRANSFER,
        status=BlockchainOperationStatus.REQUESTED,
        token_id=None,
        trade_id=trade_id,
        idempotency_key=str(uuid4()),
    )
    _save(db=db, operation=operation)

    try:
        token_id = to_token_id(serial_number)
        operation.token_id = token_id
        seller_address = client.ensure_wallet(user_id=seller_user_id)
        buyer_address = client.ensure_wallet(user_id=buyer_user_id)
        operation.operation_id = client.request_transfer(
            idempotency_key=operation.idempotency_key,
            trade_id=trade_id,
            seller_user_id=seller_user_id,
            buyer_user_id=buyer_user_id,
            token_id=token_id,
            from_address=seller_address,
            to_address=buyer_address,
        )
        _save(db=db, operation=operation)

        confirmed = client.wait_for_confirmation(operation_id=operation.operation_id)
    except BlockchainError as exc:
        _record_failure(
            db=db,
            operation=operation,
            failure_reason=f"{exc.code}: {exc.message}",
        )
        raise

    if confirmed is None:
        # 작업 기록은 REQUESTED로 남겨 완료 알림이나 재조회로 확정할 수 있게 합니다.
        raise BlockchainError(
            code="CONFIRMATION_TIMEOUT",
            message="제한 시간 안에 NFT 이전이 확정되지 않았습니다.",
        )

    final_owner_address = confirmed.get("finalOwnerAddress")
    if final_owner_address != buyer_address:
        _record_failure(
            db=db,
            operation=operation,
            failure_reason="OWNER_MISMATCH: 확정된 소유자가 구매자와 다릅니다.",
        )
        raise BlockchainError(
            code="OWNER_MISMATCH",
            message="확정된 NFT 소유자가 구매자와 다릅니다.",
        )

    operation.status = BlockchainOperationStatus.CONFIRMED
    operation.final_owner_address = final_owner_address
    operation.tx_hash = confirmed.get("currentTxHash")
    _save(db=db, operation=operation)

    return certificate_values(token_id=token_id, tx_hash=operation.tx_hash)


def certificate_values(*, token_id: int, tx_hash: str | None) -> dict[str, str]:
    """확정된 토큰 정보를 디지털 인증서 컬럼 값으로 만듭니다."""
    nft: dict[str, Any] = client.get_nft(token_id=token_id)
    return {
        "token_id": str(token_id),
        "token_standard": TOKEN_STANDARD,
        "contract_address": str(nft["contractAddress"]),
        "metadata_url": str(nft["metadataUri"]),
        "tx_hash": str(tx_hash or ""),
    }


def _record_failure(
    *,
    db: Session,
    operation: BlockchainOperation,
    failure_reason: str,
) -> None:
    """실패 사유를 기록합니다."""
    logger.warning(
        "transfer failed: trade_id=%s reason=%s",
        operation.trade_id,
        failure_reason,
    )
    operation.status = BlockchainOperationStatus.FAILED
    operation.failure_reason = failure_reason[:255]
    _save(db=db, operation=operation)


def _save(*, db: Session, operation: BlockchainOperation) -> None:
    """작업 기록을 저장합니다."""
    try:
        db.add(operation)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("blockchain operation 기록에 실패했습니다.")
