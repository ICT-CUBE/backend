"""개발·데모용 백필 Mint 처리."""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cube import Cube, CubeOwnership
from app.models.enums import CubeStatus, OwnershipStatus
from app.services.blockchain import client
from app.services.blockchain.errors import BlockchainError
from app.services.blockchain.mint import mint_cube_nft, to_token_id

# 큐브 한 건을 처리한 결과입니다.
ALREADY_MINTED = "ALREADY_MINTED"
MINTED = "MINTED"
OWNED_BY_OTHER = "OWNED_BY_OTHER"
SKIPPED = "SKIPPED"
FAILED = "FAILED"

logger = logging.getLogger(__name__)


def backfill_mint(*, db: Session) -> list[dict[str, Any]]:
    """활성 큐브 소유권을 돌며 아직 발행되지 않은 NFT를 현재 소유자 앞으로 발행합니다."""
    rows = db.execute(
        select(CubeOwnership.user_id, Cube.id, Cube.serial_number)
        .join(Cube, Cube.id == CubeOwnership.cube_id)
        .where(
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            Cube.deleted_at.is_(None),
            Cube.status != CubeStatus.DISABLED,
        )
        .order_by(Cube.id.asc())
    ).all()

    return [
        _backfill_one(
            db=db,
            user_id=user_id,
            cube_id=cube_id,
            serial_number=serial_number,
        )
        for user_id, cube_id, serial_number in rows
    ]


def _backfill_one(
    *,
    db: Session,
    user_id: int,
    cube_id: int,
    serial_number: str,
) -> dict[str, Any]:
    """큐브 한 건을 멱등하게 처리합니다."""
    result: dict[str, Any] = {
        "cube_id": cube_id,
        "serial_number": serial_number,
        "user_id": user_id,
        "token_id": None,
        "status": SKIPPED,
        "detail": "",
    }
    try:
        token_id = to_token_id(serial_number)
        result["token_id"] = token_id
        wallet_address = client.ensure_wallet(user_id=user_id)
        nft = client.get_nft(token_id=token_id)
    except BlockchainError as exc:
        result["status"] = SKIPPED if exc.code.startswith("SERIAL") else FAILED
        result["detail"] = f"{exc.code}: {exc.message}"
        return result

    if nft["minted"]:
        if nft["ownerAddress"] == wallet_address:
            result["status"] = ALREADY_MINTED
            result["detail"] = wallet_address
            return result
        # 다른 지갑이 이미 보유한 토큰은 건드리지 않고 중단합니다.
        result["status"] = OWNED_BY_OTHER
        result["detail"] = str(nft["ownerAddress"])
        return result

    mint_cube_nft(
        db=db,
        user_id=user_id,
        cube_id=cube_id,
        serial_number=serial_number,
    )

    minted = client.get_nft(token_id=token_id)
    if minted["minted"] and minted["ownerAddress"] == wallet_address:
        result["status"] = MINTED
        result["detail"] = wallet_address
    else:
        result["status"] = FAILED
        result["detail"] = "발행 후에도 소유자를 확인하지 못했습니다."
    return result
