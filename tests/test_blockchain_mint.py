"""큐브 인증 후 NFT 발행 처리 테스트."""

from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.blockchain import BlockchainOperation
from app.models.enums import BlockchainOperationStatus, BlockchainOperationType
from app.services.blockchain import mint
from app.services.blockchain.errors import BlockchainError

IMAGE_URL = "https://cdn.example.com/cube.png"
WALLET_ADDRESS = "0x92E6E89aa218360852252bf7DBB64C5978395E27"
TX_HASH = "0xbf162a374bb6088b4da6127619436b527b7b21347700d23cdea16d5f94b9df2f"


def collect_operations(db: Mock) -> list[BlockchainOperation]:
    """db.add 로 저장한 작업 기록을 모읍니다."""
    saved: list[BlockchainOperation] = []
    db.add.side_effect = saved.append
    db.scalar.return_value = IMAGE_URL
    return saved


def mint_client(
    *,
    ready: bool = True,
    operation_id: str = "op-1",
    confirmed: dict | None = None,
) -> dict[str, Mock]:
    """블록체인 클라이언트 호출을 대체할 Mock 묶음을 만듭니다."""
    if confirmed is None:
        confirmed = {
            "status": "ONCHAIN_CONFIRMED",
            "finalOwnerAddress": WALLET_ADDRESS,
            "currentTxHash": TX_HASH,
        }
    return {
        "ensure_wallet": Mock(return_value=WALLET_ADDRESS),
        "prepare_metadata": Mock(return_value=ready),
        "get_metadata_status": Mock(return_value=ready),
        "request_mint": Mock(return_value=operation_id),
        "wait_for_confirmation": Mock(return_value=confirmed),
    }


def run_mint(
    db: Mock,
    *,
    calls: dict[str, Mock],
    serial_number: str = "NO.0044",
    cube_id: int = 4,
    user_id: int = 1,
) -> None:
    with (
        patch.object(mint.client, "ensure_wallet", calls["ensure_wallet"]),
        patch.object(mint.client, "prepare_metadata", calls["prepare_metadata"]),
        patch.object(mint.client, "get_metadata_status", calls["get_metadata_status"]),
        patch.object(mint.client, "request_mint", calls["request_mint"]),
        patch.object(
            mint.client,
            "wait_for_confirmation",
            calls["wait_for_confirmation"],
        ),
        patch.object(
            mint,
            "prepare_product_image",
            return_value=("aW1hZ2U=", "image/png"),
        ),
    ):
        mint.mint_cube_nft(
            db=db,
            user_id=user_id,
            cube_id=cube_id,
            serial_number=serial_number,
        )


# --- 토큰 번호 변환 ---


def test_to_token_id_converts_serial_number() -> None:
    assert mint.to_token_id("NO.0026") == 26
    assert mint.to_token_id("NO.0100") == 100
    assert mint.to_token_id(" NO.0001 ") == 1


def test_to_token_id_rejects_unsupported_serial_number() -> None:
    with pytest.raises(BlockchainError) as error:
        mint.to_token_id("ARZ-CUBE-0002")

    assert error.value.code == "SERIAL_NUMBER_NOT_SUPPORTED"


def test_to_token_id_rejects_out_of_range_value() -> None:
    with pytest.raises(BlockchainError) as error:
        mint.to_token_id("NO.10001")

    assert error.value.code == "TOKEN_ID_OUT_OF_RANGE"


def test_to_token_id_rejects_zero() -> None:
    with pytest.raises(BlockchainError) as error:
        mint.to_token_id("NO.0000")

    assert error.value.code == "TOKEN_ID_OUT_OF_RANGE"


# --- 정상 발행 ---


def test_mint_cube_nft_records_confirmed_operation() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    calls = mint_client()

    run_mint(db, calls=calls)

    operation = saved[0]
    assert operation.operation_type == BlockchainOperationType.MINT
    assert operation.status == BlockchainOperationStatus.CONFIRMED
    assert operation.token_id == 44
    assert operation.cube_id == 4
    assert operation.operation_id == "op-1"
    assert operation.tx_hash == TX_HASH
    assert operation.final_owner_address == WALLET_ADDRESS
    assert operation.failure_reason is None
    assert operation.idempotency_key


def test_mint_cube_nft_sends_wallet_address_and_token_id() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    calls = mint_client()

    run_mint(db, calls=calls)

    calls["ensure_wallet"].assert_called_once_with(user_id=1)
    assert calls["prepare_metadata"].call_args.kwargs["token_id"] == 44
    assert calls["prepare_metadata"].call_args.kwargs["cube_number"] == "NO.0044"
    mint_kwargs = calls["request_mint"].call_args.kwargs
    assert mint_kwargs["token_id"] == 44
    assert mint_kwargs["cube_id"] == 4
    assert mint_kwargs["user_id"] == 1
    assert mint_kwargs["to_address"] == WALLET_ADDRESS
    assert mint_kwargs["idempotency_key"] == saved[0].idempotency_key


def test_mint_cube_nft_uses_official_product_image() -> None:
    db = Mock(spec=Session)
    collect_operations(db)
    calls = mint_client()

    with (
        patch.object(
            mint,
            "prepare_product_image",
            return_value=("aW1hZ2U=", "image/png"),
        ) as prepare_image,
        patch.object(mint.client, "ensure_wallet", calls["ensure_wallet"]),
        patch.object(mint.client, "prepare_metadata", calls["prepare_metadata"]),
        patch.object(mint.client, "request_mint", calls["request_mint"]),
        patch.object(
            mint.client,
            "wait_for_confirmation",
            calls["wait_for_confirmation"],
        ),
    ):
        mint.mint_cube_nft(db=db, user_id=1, cube_id=4, serial_number="NO.0044")

    prepare_image.assert_called_once_with(image_url=IMAGE_URL)
    query = str(
        db.scalar.call_args.args[0].compile(compile_kwargs={"literal_binds": True})
    )
    assert "market_product.cube_id = 4" in query
    assert "market_product.deleted_at IS NULL" in query


def test_mint_cube_nft_checks_metadata_status_when_not_ready_yet() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    calls = mint_client(ready=False)
    calls["get_metadata_status"] = Mock(return_value=True)

    run_mint(db, calls=calls)

    calls["get_metadata_status"].assert_called_once_with(token_id=44)
    assert saved[0].status == BlockchainOperationStatus.CONFIRMED


# --- 실패·대기 ---


def test_mint_cube_nft_records_failure_for_unsupported_serial_number() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    calls = mint_client()

    run_mint(db, calls=calls, serial_number="ARZ-CUBE-0002")

    assert saved[0].status == BlockchainOperationStatus.FAILED
    assert saved[0].token_id is None
    assert "SERIAL_NUMBER_NOT_SUPPORTED" in saved[0].failure_reason
    calls["request_mint"].assert_not_called()


def test_mint_cube_nft_records_failure_when_product_image_is_missing() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    db.scalar.return_value = None
    calls = mint_client()

    run_mint(db, calls=calls)

    assert saved[0].status == BlockchainOperationStatus.FAILED
    assert "PRODUCT_IMAGE_NOT_FOUND" in saved[0].failure_reason
    calls["ensure_wallet"].assert_not_called()


def test_mint_cube_nft_records_failure_when_metadata_is_not_ready() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    calls = mint_client(ready=False)

    run_mint(db, calls=calls)

    assert saved[0].status == BlockchainOperationStatus.FAILED
    assert "METADATA_NOT_READY" in saved[0].failure_reason
    calls["request_mint"].assert_not_called()


def test_mint_cube_nft_records_failure_when_request_is_rejected() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    calls = mint_client()
    calls["request_mint"] = Mock(
        side_effect=BlockchainError(code="IDEMPOTENCY_CONFLICT", message="conflict")
    )

    run_mint(db, calls=calls)

    assert saved[0].status == BlockchainOperationStatus.FAILED
    assert "IDEMPOTENCY_CONFLICT" in saved[0].failure_reason


def test_mint_cube_nft_records_failure_for_unexpected_error() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    calls = mint_client()
    calls["ensure_wallet"] = Mock(side_effect=RuntimeError("boom"))

    run_mint(db, calls=calls)

    assert saved[0].status == BlockchainOperationStatus.FAILED
    assert "UNEXPECTED_ERROR" in saved[0].failure_reason


def test_mint_cube_nft_keeps_requested_status_after_timeout() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    calls = mint_client(confirmed=None)
    calls["wait_for_confirmation"] = Mock(return_value=None)

    run_mint(db, calls=calls)

    assert saved[0].status == BlockchainOperationStatus.REQUESTED
    assert saved[0].operation_id == "op-1"
    assert saved[0].failure_reason is None


def test_mint_cube_nft_records_failure_when_final_owner_differs() -> None:
    db = Mock(spec=Session)
    saved = collect_operations(db)
    calls = mint_client(
        confirmed={
            "status": "ONCHAIN_CONFIRMED",
            "finalOwnerAddress": "0x1111111111111111111111111111111111111111",
            "currentTxHash": TX_HASH,
        }
    )

    run_mint(db, calls=calls)

    assert saved[0].status == BlockchainOperationStatus.FAILED
    assert "OWNER_MISMATCH" in saved[0].failure_reason


def test_mint_cube_nft_never_raises_to_caller() -> None:
    db = Mock(spec=Session)
    collect_operations(db)
    db.commit.side_effect = RuntimeError("db down")
    calls = mint_client()
    calls["request_mint"] = Mock(side_effect=RuntimeError("blockchain down"))

    # 인증 API 응답을 지켜야 하므로 어떤 실패도 밖으로 나가지 않습니다.
    run_mint(db, calls=calls)

    db.rollback.assert_called()
