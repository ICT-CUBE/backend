"""구매 확정 시 NFT 이전 처리 테스트."""

from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.blockchain import BlockchainOperation
from app.models.enums import BlockchainOperationStatus, BlockchainOperationType
from app.services.blockchain import transfer
from app.services.blockchain.errors import BlockchainError

SELLER_ADDRESS = "0x1111111111111111111111111111111111111111"
BUYER_ADDRESS = "0x2222222222222222222222222222222222222222"
TX_HASH = "0x54aa5bda988138fb1858592ac5cd88859592fa3ab0403a6657bddf4b3bb356e2"
CONTRACT_ADDRESS = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
METADATA_URI = "ipfs://fakecid1503b0329552d6a6229c15cd195abb442"


def collect_operations(db: Mock) -> list[BlockchainOperation]:
    saved: list[BlockchainOperation] = []
    db.add.side_effect = saved.append
    return saved


def transfer_client(
    *,
    confirmed: dict | None = None,
    operation_id: str = "op-9",
) -> dict[str, Mock]:
    if confirmed is None:
        confirmed = {
            "status": "ONCHAIN_CONFIRMED",
            "finalOwnerAddress": BUYER_ADDRESS,
            "currentTxHash": TX_HASH,
        }
    return {
        "ensure_wallet": Mock(side_effect=[SELLER_ADDRESS, BUYER_ADDRESS]),
        "request_transfer": Mock(return_value=operation_id),
        "wait_for_confirmation": Mock(return_value=confirmed),
        "get_nft": Mock(
            return_value={
                "tokenId": 44,
                "minted": True,
                "ownerAddress": BUYER_ADDRESS,
                "contractAddress": CONTRACT_ADDRESS,
                "metadataUri": METADATA_URI,
            }
        ),
    }


def run_transfer(
    db: Mock,
    *,
    calls: dict[str, Mock],
    serial_number: str = "NO.0044",
) -> dict[str, str]:
    with (
        patch.object(transfer.client, "ensure_wallet", calls["ensure_wallet"]),
        patch.object(transfer.client, "request_transfer", calls["request_transfer"]),
        patch.object(
            transfer.client,
            "wait_for_confirmation",
            calls["wait_for_confirmation"],
        ),
        patch.object(transfer.client, "get_nft", calls["get_nft"]),
    ):
        return transfer.transfer_cube_nft(
            db=db,
            trade_id=23,
            seller_user_id=2,
            buyer_user_id=1,
            serial_number=serial_number,
        )


def test_transfer_cube_nft_returns_certificate_values() -> None:
    db = Mock(spec=Session)
    collect_operations(db)
    calls = transfer_client()

    values = run_transfer(db, calls=calls)

    assert values == {
        "token_id": "44",
        "token_standard": "ERC-721",
        "contract_address": CONTRACT_ADDRESS,
        "metadata_url": METADATA_URI,
        "tx_hash": TX_HASH,
    }
    calls["get_nft"].assert_called_once_with(token_id=44)


def test_transfer_cube_nft_records_confirmed_operation() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    calls = transfer_client()

    run_transfer(db, calls=calls)

    operation = saved[0]
    assert operation.operation_type == BlockchainOperationType.TRANSFER
    assert operation.status == BlockchainOperationStatus.CONFIRMED
    assert operation.trade_id == 23
    assert operation.token_id == 44
    assert operation.cube_id is None
    assert operation.operation_id == "op-9"
    assert operation.tx_hash == TX_HASH
    assert operation.final_owner_address == BUYER_ADDRESS


def test_transfer_cube_nft_sends_seller_and_buyer_addresses() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    calls = transfer_client()

    run_transfer(db, calls=calls)

    assert calls["ensure_wallet"].call_args_list[0].kwargs == {"user_id": 2}
    assert calls["ensure_wallet"].call_args_list[1].kwargs == {"user_id": 1}
    request_kwargs = calls["request_transfer"].call_args.kwargs
    assert request_kwargs["trade_id"] == 23
    assert request_kwargs["seller_user_id"] == 2
    assert request_kwargs["buyer_user_id"] == 1
    assert request_kwargs["token_id"] == 44
    assert request_kwargs["from_address"] == SELLER_ADDRESS
    assert request_kwargs["to_address"] == BUYER_ADDRESS
    assert request_kwargs["idempotency_key"] == saved[0].idempotency_key


def test_transfer_cube_nft_raises_for_unsupported_serial_number() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    calls = transfer_client()

    with pytest.raises(BlockchainError) as error:
        run_transfer(db, calls=calls, serial_number="ARZ-CUBE-0002")

    assert error.value.code == "SERIAL_NUMBER_NOT_SUPPORTED"
    assert saved[0].status == BlockchainOperationStatus.FAILED
    calls["request_transfer"].assert_not_called()


def test_transfer_cube_nft_records_failure_when_request_is_rejected() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    calls = transfer_client()
    calls["request_transfer"] = Mock(
        side_effect=BlockchainError(
            code="TRANSFER_OWNER_MISMATCH",
            message="owner mismatch",
        )
    )

    with pytest.raises(BlockchainError) as error:
        run_transfer(db, calls=calls)

    assert error.value.code == "TRANSFER_OWNER_MISMATCH"
    assert saved[0].status == BlockchainOperationStatus.FAILED
    assert "TRANSFER_OWNER_MISMATCH" in saved[0].failure_reason


def test_transfer_cube_nft_raises_timeout_and_keeps_requested_status() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    calls = transfer_client()
    calls["wait_for_confirmation"] = Mock(return_value=None)

    with pytest.raises(BlockchainError) as error:
        run_transfer(db, calls=calls)

    assert error.value.code == "CONFIRMATION_TIMEOUT"
    # 나중에 완료 알림이나 재조회로 확정할 수 있도록 실패로 바꾸지 않습니다.
    assert saved[0].status == BlockchainOperationStatus.REQUESTED
    assert saved[0].operation_id == "op-9"


def test_transfer_cube_nft_raises_when_final_owner_is_not_buyer() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    calls = transfer_client(
        confirmed={
            "status": "ONCHAIN_CONFIRMED",
            "finalOwnerAddress": SELLER_ADDRESS,
            "currentTxHash": TX_HASH,
        }
    )

    with pytest.raises(BlockchainError) as error:
        run_transfer(db, calls=calls)

    assert error.value.code == "OWNER_MISMATCH"
    assert saved[0].status == BlockchainOperationStatus.FAILED
    calls["get_nft"].assert_not_called()
