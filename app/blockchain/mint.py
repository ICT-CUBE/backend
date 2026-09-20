"""큐브 최초 인증 성공 후 NFT 발행 처리."""

import logging
import re
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.blockchain import client
from app.blockchain.errors import BlockchainError
from app.blockchain.images import prepare_product_image
from app.blockchain.models import BlockchainOperation
from app.core.enums import BlockchainOperationStatus, BlockchainOperationType
from app.cube.models import Cube

# 큐브 시리얼 번호에서 토큰 번호로 쓸 숫자 부분을 뽑아내는 형식입니다.
SERIAL_NUMBER_PATTERN = re.compile(r"^NO\.(\d+)$")
TOKEN_ID_MIN = 1
TOKEN_ID_MAX = 10000

logger = logging.getLogger(__name__)


def mint_cube_nft(
    *,
    db: Session,
    user_id: int,
    cube_id: int,
    serial_number: str,
) -> None:
    """새 큐브 소유권에 대한 NFT를 발행합니다.

    큐브 인증 자체는 이미 완료된 것으로 보기 때문에 실패를 밖으로 던지지 않고
    `blockchain_operation`에 기록만 남깁니다.
    """
    operation = BlockchainOperation(
        operation_type=BlockchainOperationType.MINT,
        status=BlockchainOperationStatus.REQUESTED,
        token_id=None,
        cube_id=cube_id,
        idempotency_key=str(uuid4()),
    )
    _save(db=db, operation=operation)

    try:
        token_id = to_token_id(serial_number)
        operation.token_id = token_id
        image_url = _get_product_image_url(db=db, cube_id=cube_id)
        image_base64, image_mime_type = prepare_product_image(image_url=image_url)
        wallet_address = client.ensure_wallet(user_id=user_id)
        _prepare_metadata(
            token_id=token_id,
            serial_number=serial_number,
            image_base64=image_base64,
            image_mime_type=image_mime_type,
        )
        operation.operation_id = client.request_mint(
            idempotency_key=operation.idempotency_key,
            user_id=user_id,
            cube_id=cube_id,
            token_id=token_id,
            to_address=wallet_address,
        )
        _save(db=db, operation=operation)

        confirmed = client.wait_for_confirmation(operation_id=operation.operation_id)
    except Exception as exc:  # noqa: BLE001 - 인증 응답을 지키기 위해 모두 기록만 합니다.
        _record_failure(db=db, operation=operation, exc=exc)
        return

    if confirmed is None:
        # 제한 시간 안에 확정되지 않으면 완료 알림이나 재조회로 처리합니다.
        logger.info(
            "mint confirmation timed out: operation_id=%s",
            operation.operation_id,
        )
        return

    _record_confirmation(
        db=db,
        operation=operation,
        confirmed=confirmed,
        expected_owner_address=wallet_address,
    )


def to_token_id(serial_number: str) -> int:
    """큐브 시리얼 번호의 숫자 부분을 토큰 번호로 변환합니다."""
    matched = SERIAL_NUMBER_PATTERN.match(serial_number.strip())
    if matched is None:
        raise BlockchainError(
            code="SERIAL_NUMBER_NOT_SUPPORTED",
            message=f"토큰 번호로 변환할 수 없는 시리얼 번호입니다: {serial_number}",
        )

    token_id = int(matched.group(1))
    if not TOKEN_ID_MIN <= token_id <= TOKEN_ID_MAX:
        raise BlockchainError(
            code="TOKEN_ID_OUT_OF_RANGE",
            message=f"토큰 번호가 허용 범위를 벗어났습니다: {token_id}",
        )
    return token_id


def _get_product_image_url(*, db: Session, cube_id: int) -> str:
    """NFT 이미지로 사용할 공식 제품 이미지 URL을 조회합니다."""
    image_url = db.scalar(
        select(Cube.product_image_url)
        .where(
            Cube.id == cube_id,
            Cube.deleted_at.is_(None),
        )
        .limit(1)
    )
    if not image_url:
        raise BlockchainError(
            code="PRODUCT_IMAGE_NOT_FOUND",
            message="NFT에 사용할 제품 이미지를 찾을 수 없습니다.",
        )
    return image_url


def _prepare_metadata(
    *,
    token_id: int,
    serial_number: str,
    image_base64: str,
    image_mime_type: str,
) -> None:
    """메타데이터를 준비하고 사용 가능 상태인지 확인합니다."""
    ready = client.prepare_metadata(
        token_id=token_id,
        cube_number=serial_number,
        image_base64=image_base64,
        image_mime_type=image_mime_type,
    )
    if ready or client.get_metadata_status(token_id=token_id):
        return

    raise BlockchainError(
        code="METADATA_NOT_READY",
        message="NFT 메타데이터가 아직 준비되지 않았습니다.",
    )


def _record_confirmation(
    *,
    db: Session,
    operation: BlockchainOperation,
    confirmed: dict,
    expected_owner_address: str,
) -> None:
    """확정된 작업의 소유자를 대조하고 결과를 기록합니다."""
    final_owner_address = confirmed.get("finalOwnerAddress")
    if final_owner_address != expected_owner_address:
        operation.status = BlockchainOperationStatus.FAILED
        operation.failure_reason = "OWNER_MISMATCH: 확정된 소유자가 예상과 다릅니다."
    else:
        operation.status = BlockchainOperationStatus.CONFIRMED
        operation.final_owner_address = final_owner_address
        operation.tx_hash = confirmed.get("currentTxHash")
    _save(db=db, operation=operation)


def _record_failure(
    *,
    db: Session,
    operation: BlockchainOperation,
    exc: Exception,
) -> None:
    """실패 사유를 기록합니다."""
    if isinstance(exc, BlockchainError):
        failure_reason = f"{exc.code}: {exc.message}"
    else:
        failure_reason = f"UNEXPECTED_ERROR: {exc}"
    logger.warning(
        "mint failed: cube_id=%s reason=%s",
        operation.cube_id,
        failure_reason,
    )
    operation.status = BlockchainOperationStatus.FAILED
    operation.failure_reason = failure_reason[:255]
    _save(db=db, operation=operation)


def _save(*, db: Session, operation: BlockchainOperation) -> None:
    """작업 기록을 저장합니다. 저장 실패는 인증 응답에 영향을 주지 않습니다."""
    try:
        db.add(operation)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("blockchain operation 기록에 실패했습니다.")
