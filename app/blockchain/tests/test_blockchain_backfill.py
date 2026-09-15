"""백필 Mint 처리 테스트."""

from unittest.mock import Mock, patch

from sqlalchemy.orm import Session

# 다른 도메인 모델을 문자열로 참조하는 관계를 해석하려면 모든 ORM 모델이 등록돼 있어야 합니다.
from app import models  # noqa: F401
from app.blockchain import backfill
from app.blockchain.errors import BlockchainError

WALLET_ADDRESS = "0x92E6E89aa218360852252bf7DBB64C5978395E27"
OTHER_ADDRESS = "0x1111111111111111111111111111111111111111"


def nft(*, minted: bool, owner_address: str | None = None) -> dict:
    return {
        "tokenId": 44,
        "minted": minted,
        "ownerAddress": owner_address,
        "contractAddress": "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512",
        "metadataUri": "ipfs://fakecid",
    }


def set_ownership_rows(db: Mock, rows: list[tuple[int, int, str]]) -> None:
    """(사용자 id, 큐브 id, 시리얼 번호) 목록을 조회 결과로 지정합니다."""
    db.execute.return_value.all.return_value = rows


def run_backfill(
    db: Mock,
    *,
    get_nft: Mock,
    mint: Mock | None = None,
    ensure_wallet: Mock | None = None,
) -> list[dict]:
    with (
        patch.object(
            backfill.client,
            "ensure_wallet",
            ensure_wallet or Mock(return_value=WALLET_ADDRESS),
        ),
        patch.object(backfill.client, "get_nft", get_nft),
        patch.object(backfill, "mint_cube_nft", mint or Mock()),
    ):
        return backfill.backfill_mint(db=db)


def test_backfill_mints_unminted_cube_to_current_owner() -> None:
    db = Mock(spec=Session)
    set_ownership_rows(db, [(1, 4, "NO.0044")])
    get_nft = Mock(
        side_effect=[
            nft(minted=False),
            nft(minted=True, owner_address=WALLET_ADDRESS),
        ]
    )
    mint = Mock()

    results = run_backfill(db, get_nft=get_nft, mint=mint)

    assert results[0]["status"] == backfill.MINTED
    assert results[0]["token_id"] == 44
    mint.assert_called_once_with(
        db=db,
        user_id=1,
        cube_id=4,
        serial_number="NO.0044",
    )


def test_backfill_skips_cube_already_owned_by_same_wallet() -> None:
    db = Mock(spec=Session)
    set_ownership_rows(db, [(1, 4, "NO.0044")])
    get_nft = Mock(return_value=nft(minted=True, owner_address=WALLET_ADDRESS))
    mint = Mock()

    results = run_backfill(db, get_nft=get_nft, mint=mint)

    assert results[0]["status"] == backfill.ALREADY_MINTED
    mint.assert_not_called()


def test_backfill_stops_cube_owned_by_other_wallet() -> None:
    db = Mock(spec=Session)
    set_ownership_rows(db, [(1, 4, "NO.0044")])
    get_nft = Mock(return_value=nft(minted=True, owner_address=OTHER_ADDRESS))
    mint = Mock()

    results = run_backfill(db, get_nft=get_nft, mint=mint)

    assert results[0]["status"] == backfill.OWNED_BY_OTHER
    assert results[0]["detail"] == OTHER_ADDRESS
    mint.assert_not_called()


def test_backfill_skips_unsupported_serial_number() -> None:
    db = Mock(spec=Session)
    set_ownership_rows(db, [(1, 4, "ARZ-CUBE-0002")])
    get_nft = Mock()
    mint = Mock()

    results = run_backfill(db, get_nft=get_nft, mint=mint)

    assert results[0]["status"] == backfill.SKIPPED
    assert "SERIAL_NUMBER_NOT_SUPPORTED" in results[0]["detail"]
    get_nft.assert_not_called()
    mint.assert_not_called()


def test_backfill_reports_failure_when_blockchain_call_fails() -> None:
    db = Mock(spec=Session)
    set_ownership_rows(db, [(1, 4, "NO.0044")])
    ensure_wallet = Mock(
        side_effect=BlockchainError(code="BLOCKCHAIN_UNREACHABLE", message="down")
    )

    results = run_backfill(db, get_nft=Mock(), ensure_wallet=ensure_wallet)

    assert results[0]["status"] == backfill.FAILED
    assert "BLOCKCHAIN_UNREACHABLE" in results[0]["detail"]


def test_backfill_reports_failure_when_owner_is_not_confirmed() -> None:
    db = Mock(spec=Session)
    set_ownership_rows(db, [(1, 4, "NO.0044")])
    get_nft = Mock(side_effect=[nft(minted=False), nft(minted=False)])

    results = run_backfill(db, get_nft=get_nft, mint=Mock())

    assert results[0]["status"] == backfill.FAILED


def test_backfill_processes_every_active_ownership() -> None:
    db = Mock(spec=Session)
    set_ownership_rows(db, [(1, 4, "NO.0044"), (2, 5, "NO.0055")])
    get_nft = Mock(return_value=nft(minted=True, owner_address=WALLET_ADDRESS))

    results = run_backfill(db, get_nft=get_nft)

    assert [result["cube_id"] for result in results] == [4, 5]
    assert all(result["status"] == backfill.ALREADY_MINTED for result in results)


def test_backfill_queries_only_active_ownerships() -> None:
    db = Mock(spec=Session)
    set_ownership_rows(db, [])

    run_backfill(db, get_nft=Mock())

    query = str(
        db.execute.call_args.args[0].compile(compile_kwargs={"literal_binds": True})
    )
    assert "cube_ownership.ownership_status = 'ACTIVE'" in query
    assert "cube.deleted_at IS NULL" in query
    assert "cube.status != 'DISABLED'" in query
    assert "ORDER BY cube.id ASC" in query
