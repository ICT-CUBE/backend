"""마켓 도메인 API 테스트."""

from datetime import datetime
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.main import app
from app.models.blockchain import BlockchainOperation
from app.models.cube import Affinity, Cube, CubeOwnership, Level
from app.models.enums import (
    BlockchainOperationStatus,
    BlockchainOperationType,
    CubeStatus,
    LevelName,
    OwnershipStatus,
    SellListingStatus,
    TradeStatus,
)
from app.models.market import (
    DigitalCertificate,
    MarketProduct,
    SellListing,
    Trade,
)
from app.models.user import User
from app.services.blockchain.errors import BlockchainError
from tests.conftest import api_client


def read_sellable_cubes_request(db: Mock):
    with api_client(db) as client:
        return client.get("/api/v1/users/me/sellable-cubes")


def create_trade_request(
    db: Mock,
    *,
    body: dict[str, int | str] | None = None,
):
    with api_client(db) as client:
        return client.post(
            "/api/v1/users/me/trades",
            json=body
            if body is not None
            else {
                "sellListingId": 1,
                "buyerAddress": "서울특별시 강남구 테헤란로 429,1934호",
                "buyerPhoneNumber": "010-4282-4533",
                "totalPrice": 12740,
                "paidTime": "2026-08-15T21:30:00",
            },
        )


def create_sell_listing_request(
    db: Mock,
    *,
    body: dict[str, object] | None = None,
):
    with api_client(db) as client:
        return client.post(
            "/api/v1/users/me/sell-listings",
            json=(
                body
                if body is not None
                else {
                    "marketProductId": 1,
                    "productStatus": "미개봉",
                    "title": "제니 루비 큐브 판매",
                    "description": "상태 좋습니다.",
                    "price": 12500,
                }
            ),
        )


def delete_sell_listing_request(
    db: Mock,
    *,
    sell_listing_id: int = 1,
):
    with api_client(db) as client:
        return client.delete(
            f"/api/v1/users/me/sell-listings/{sell_listing_id}"
        )


def read_trade_detail_request(
    db: Mock,
    *,
    trade_id: int = 1,
):
    with api_client(db) as client:
        return client.get(f"/api/v1/users/me/trades/{trade_id}")


CERTIFICATE_VALUES = {
    "token_id": "44",
    "token_standard": "ERC-721",
    "contract_address": "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512",
    "metadata_url": "ipfs://fakecid1503b032",
    "tx_hash": "0x54aa5bda988138fb1858592ac5cd88859592fa3a",
}


def complete_trade_request(
    db: Mock,
    *,
    trade_id: int = 1,
    transfer: Mock | None = None,
    raise_server_exceptions: bool = True,
):
    """구매 확정 API를 호출합니다. NFT 이전은 기본적으로 Mock으로 대체합니다."""
    with (
        patch(
            "app.services.market.transfer_cube_nft",
            transfer or Mock(return_value=dict(CERTIFICATE_VALUES)),
        ),
        api_client(db, raise_server_exceptions=raise_server_exceptions) as client,
    ):
        return client.patch(f"/api/v1/users/me/trades/{trade_id}/complete")


def set_complete_trade_results(
    db: Mock,
    *,
    status: TradeStatus = TradeStatus.DELIVERED,
    seller_user_id: int = 2,
    serial_number: str = "NO.0044",
    cube: Cube | None = None,
):
    """거래 조회와 이전 대상 조회 결과를 순서대로 지정합니다."""
    trade, buyer = complete_trade_row(status=status)
    # 확정된·대기 중인 NFT 이전 작업이 없는 상태를 기본으로 두고 큐브를 마지막에 조회합니다.
    db.scalar.side_effect = [
        None,
        None,
        cube if cube is not None else traded_cube(status=CubeStatus.TRADE_PENDING),
    ]
    db.execute.side_effect = [
        Mock(first=Mock(return_value=(trade, buyer))),
        Mock(first=Mock(return_value=(seller_user_id, serial_number))),
    ]

    def assign_certificate_id() -> None:
        db.add.call_args.args[0].id = 1

    db.flush.side_effect = assign_certificate_id
    return trade, buyer


def active_sell_listing(*, user_id: int = 2) -> SellListing:
    return SellListing(
        id=1,
        market_product_id=3,
        user_id=user_id,
        status=SellListingStatus.ACTIVE,
        deleted_at=None,
    )


def traded_cube(*, status: CubeStatus = CubeStatus.OWNED) -> Cube:
    return Cube(id=2, status=status, deleted_at=None)


def trade_detail_row():
    trade = Trade(
        id=1,
        buyer_user_id=1,
        paid_time=datetime.fromisoformat("2026-08-05T14:30:00"),
        sent_time=datetime.fromisoformat("2026-08-05T15:09:00"),
        shipped_time=datetime.fromisoformat("2026-08-07T09:45:00"),
        delivered_time=None,
        completed_time=None,
        status=TradeStatus.SHIPPING,
    )
    sell_listing = SellListing(id=7, price=12500)
    market_product = MarketProduct(
        id=3,
        product_image_url="https://example.com/mock/market-product-001.jpg",
    )
    cube = Cube(
        id=2,
        serial_number="#012",
        product_name="RUBY CUBE",
        artist_name="JENNIE",
    )
    return trade, sell_listing, market_product, cube


def complete_trade_row(*, status: TradeStatus = TradeStatus.DELIVERED):
    trade = Trade(
        id=23,
        sell_listing_id=7,
        buyer_user_id=1,
        completed_time=None,
        status=status,
    )
    buyer = User(id=1, nickname="홍길동")
    return trade, buyer


def test_read_sellable_cubes_returns_active_unlisted_cubes() -> None:
    db = Mock(spec=Session)
    db.execute.return_value.all.return_value = [
        (
            Cube(
                id=1,
                serial_number="#012",
                product_name="RUBY CUBE",
                artist_name="JENNIE",
            ),
            MarketProduct(
                id=1,
                cube_id=1,
                product_image_url="https://example.com/cube-001.png",
            ),
        ),
        (
            Cube(
                id=3,
                serial_number="#031",
                product_name="SOLO CUBE",
                artist_name="JENNIE",
            ),
            MarketProduct(
                id=3,
                cube_id=3,
                product_image_url=None,
            ),
        ),
    ]

    response = read_sellable_cubes_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "cubes": [
            {
                "cubeId": 1,
                "marketProductId": 1,
                "serialNumber": "#012",
                "productName": "RUBY CUBE",
                "artistName": "JENNIE",
                "productImageUrl": "https://example.com/cube-001.png",
            },
            {
                "cubeId": 3,
                "marketProductId": 3,
                "serialNumber": "#031",
                "productName": "SOLO CUBE",
                "artistName": "JENNIE",
                "productImageUrl": None,
            },
        ]
    }

    query = str(db.execute.call_args.args[0])
    assert "cube_ownership.user_id" in query
    assert "cube_ownership.ownership_status" in query
    assert "cube.deleted_at IS NULL" in query
    assert "market_product.deleted_at IS NULL" in query
    assert "sell_listing.user_id" in query
    assert "sell_listing.status" in query
    assert "sell_listing.deleted_at IS NULL" in query
    assert "NOT (EXISTS" in query
    assert "ORDER BY cube.id ASC" in query
    assert "is_last_accessed" not in query


def test_read_sellable_cubes_returns_empty_list() -> None:
    db = Mock(spec=Session)
    db.execute.return_value.all.return_value = []

    response = read_sellable_cubes_request(db)

    assert response.status_code == 200
    assert response.json() == {"cubes": []}


def test_read_sellable_cubes_swagger_responses() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/sellable-cubes"
    ]["get"]

    assert set(operation["responses"]) == {"200"}
    assert operation["tags"] == ["market"]
    assert operation["security"] == [{"HTTPBearer": []}]


def test_create_sell_listing_saves_listing_from_json_body() -> None:
    db = Mock(spec=Session)
    db.scalar.side_effect = [MarketProduct(id=1, cube_id=1), None]

    def assign_sell_listing_id() -> None:
        sell_listing = db.add.call_args.args[0]
        sell_listing.id = 7

    db.flush.side_effect = assign_sell_listing_id

    response = create_sell_listing_request(db)

    assert response.status_code == 201
    assert response.json() == {"sellListingId": 7}
    sell_listing = db.add.call_args_list[0].args[0]
    assert isinstance(sell_listing, SellListing)
    assert sell_listing.market_product_id == 1
    assert sell_listing.user_id == 1
    assert sell_listing.product_status == "미개봉"
    assert sell_listing.title == "제니 루비 큐브 판매"
    assert sell_listing.description == "상태 좋습니다."
    assert sell_listing.price == 12500
    assert sell_listing.status == SellListingStatus.ACTIVE
    assert sell_listing.deleted_at is None
    assert db.add.call_count == 1
    db.flush.assert_called_once()
    db.commit.assert_called_once()

    market_product_query = str(db.scalar.call_args_list[0].args[0])
    assert "market_product.deleted_at IS NULL" in market_product_query
    assert "cube.deleted_at IS NULL" in market_product_query
    assert "cube_ownership.user_id" in market_product_query
    assert "cube_ownership.ownership_status" in market_product_query
    assert "is_last_accessed" not in market_product_query

    active_listing_query = str(db.scalar.call_args_list[1].args[0])
    assert "sell_listing.market_product_id" in active_listing_query
    assert "sell_listing.status" in active_listing_query
    assert "sell_listing.deleted_at IS NULL" in active_listing_query
    assert "sell_listing.user_id" not in active_listing_query


def test_create_sell_listing_saves_null_when_product_status_is_omitted() -> None:
    db = Mock(spec=Session)
    db.scalar.side_effect = [MarketProduct(id=1, cube_id=1), None]

    def assign_sell_listing_id() -> None:
        sell_listing = db.add.call_args.args[0]
        sell_listing.id = 7

    db.flush.side_effect = assign_sell_listing_id
    response = create_sell_listing_request(
        db,
        body={
            "marketProductId": 1,
            "title": "제니 루비 큐브 판매",
            "description": "상태 좋습니다.",
            "price": 12500,
        },
    )

    assert response.status_code == 201
    sell_listing = db.add.call_args.args[0]
    assert sell_listing.product_status is None


def test_create_sell_listing_returns_400_when_required_json_field_is_missing() -> None:
    db = Mock(spec=Session)

    response = create_sell_listing_request(
        db,
        body={
            "marketProductId": 1,
            "description": "상태 좋습니다.",
            "price": 12500,
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.scalar.assert_not_called()


def test_create_sell_listing_returns_404_for_unavailable_market_product() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = create_sell_listing_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "MARKET_PRODUCT_NOT_FOUND",
        "message": "마켓 제품 정보를 찾을 수 없습니다.",
    }
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_sell_listing_returns_409_for_existing_active_listing() -> None:
    db = Mock(spec=Session)
    db.scalar.side_effect = [MarketProduct(id=1, cube_id=1), 8]

    response = create_sell_listing_request(db)

    assert response.status_code == 409
    assert response.json() == {
        "code": "SELL_LISTING_ALREADY_ACTIVE",
        "message": "이미 판매 중인 마켓 상품입니다.",
    }
    db.rollback.assert_called_once()
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_sell_listing_swagger_contract() -> None:
    openapi_schema = app.openapi()
    operation = openapi_schema["paths"]["/api/v1/users/me/sell-listings"]["post"]

    assert set(operation["responses"]) == {"201", "404", "409"}
    request_content = operation["requestBody"]["content"]
    assert set(request_content) == {"application/json"}
    request_schema = request_content["application/json"]["schema"]
    schema_name = request_schema["$ref"].rsplit("/", 1)[-1]
    body_schema = openapi_schema["components"]["schemas"][schema_name]
    assert set(body_schema["properties"]) == {
        "marketProductId",
        "productStatus",
        "title",
        "description",
        "price",
    }
    assert "productStatus" not in body_schema["required"]
    assert operation["tags"] == ["market"]
    assert operation["security"] == [{"HTTPBearer": []}]


def test_delete_sell_listing_soft_deletes_current_user_listing() -> None:
    db = Mock(spec=Session)
    sell_listing = active_sell_listing(user_id=1)
    db.scalar.return_value = sell_listing

    response = delete_sell_listing_request(db)

    assert response.status_code == 204
    assert response.content == b""
    assert sell_listing.status == SellListingStatus.DELETED
    assert sell_listing.deleted_at is not None
    assert sell_listing.deleted_at.tzinfo is None
    assert sell_listing.deleted_at.microsecond == 0
    db.commit.assert_called_once()

    query = str(db.scalar.call_args.args[0])
    assert "sell_listing.id" in query
    assert "sell_listing.user_id" in query
    assert "sell_listing.status !=" in query
    assert "sell_listing.deleted_at IS NULL" in query


def test_delete_sell_listing_returns_404_when_listing_is_unavailable() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = delete_sell_listing_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "SELL_LISTING_NOT_FOUND",
        "message": "판매 상품을 찾을 수 없습니다.",
    }
    db.commit.assert_not_called()


def test_delete_sell_listing_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/sell-listings/{sellListingId}"
    ]["delete"]

    assert set(operation["responses"]) == {"204", "404"}
    assert operation["tags"] == ["market"]
    assert "requestBody" not in operation
    assert operation["security"] == [{"HTTPBearer": []}]


def test_create_trade_saves_trade_and_marks_sell_listing_sold() -> None:
    db = Mock(spec=Session)
    sell_listing = active_sell_listing()
    cube = traded_cube()
    db.scalar.side_effect = [sell_listing, None, cube]

    response = create_trade_request(db)

    assert response.status_code == 204
    assert response.content == b""
    inserted = db.add.call_args.args[0]
    assert isinstance(inserted, Trade)
    assert inserted.sell_listing_id == 1
    assert inserted.buyer_user_id == 1
    assert inserted.buyer_address == "서울특별시 강남구 테헤란로 429,1934호"
    assert inserted.buyer_phone_number == "010-4282-4533"
    assert inserted.total_price == 12740
    assert inserted.paid_time == datetime.fromisoformat("2026-08-15T21:30:00")
    assert inserted.paid_time.tzinfo is None
    assert inserted.sent_time is None
    assert inserted.shipped_time is None
    assert inserted.delivered_time is None
    assert inserted.completed_time is None
    assert inserted.status == TradeStatus.PAID
    assert sell_listing.status == SellListingStatus.SOLD
    assert cube.status == CubeStatus.TRADE_PENDING
    db.commit.assert_called_once()


def test_create_trade_locks_and_marks_cube_of_the_sold_listing() -> None:
    db = Mock(spec=Session)
    cube = traded_cube()
    db.scalar.side_effect = [active_sell_listing(), None, cube]

    response = create_trade_request(db)

    assert response.status_code == 204
    assert cube.status == CubeStatus.TRADE_PENDING
    cube_query = compiled_query(db.scalar.call_args_list[2])
    assert "market_product.cube_id = cube.id" in cube_query
    assert "market_product.id = 3" in cube_query
    assert "FOR UPDATE" in cube_query


def test_create_trade_returns_404_when_cube_not_found() -> None:
    db = Mock(spec=Session)
    sell_listing = active_sell_listing()
    db.scalar.side_effect = [sell_listing, None, None]

    response = create_trade_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "SELL_LISTING_INVALID",
        "message": "판매 상품이 유효하지 않습니다.",
    }
    assert sell_listing.status == SellListingStatus.ACTIVE
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_trade_returns_404_for_missing_sell_listing() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = create_trade_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "SELL_LISTING_INVALID",
        "message": "판매 상품이 유효하지 않습니다.",
    }
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_trade_returns_404_for_inactive_sell_listing_without_existing_trade() -> None:
    db = Mock(spec=Session)
    sell_listing = active_sell_listing()
    sell_listing.status = SellListingStatus.DELETED
    db.scalar.side_effect = [sell_listing, None]

    response = create_trade_request(db)

    assert response.status_code == 404
    assert response.json()["code"] == "SELL_LISTING_INVALID"
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_trade_returns_409_when_trade_already_exists() -> None:
    db = Mock(spec=Session)
    db.scalar.side_effect = [active_sell_listing(), 10]

    response = create_trade_request(db)

    assert response.status_code == 409
    assert response.json() == {
        "code": "TRADE_ALREADY_EXISTS",
        "message": "이미 거래가 생성된 판매 상품입니다.",
    }
    db.rollback.assert_called_once()
    db.add.assert_not_called()


def test_create_trade_returns_409_for_self_trade() -> None:
    db = Mock(spec=Session)
    db.scalar.side_effect = [active_sell_listing(user_id=1), None]

    response = create_trade_request(db)

    assert response.status_code == 409
    assert response.json() == {
        "code": "SELF_TRADE_NOT_ALLOWED",
        "message": "자신이 등록한 판매 상품은 구매할 수 없습니다.",
    }
    db.rollback.assert_called_once()
    db.add.assert_not_called()


def test_create_trade_swagger_responses() -> None:
    operation = app.openapi()["paths"]["/api/v1/users/me/trades"]["post"]

    assert set(operation["responses"]) == {"204", "404", "409"}
    assert operation["security"] == [{"HTTPBearer": []}]


def test_read_trade_detail_returns_trade_product_and_timeline() -> None:
    db = Mock(spec=Session)
    db.execute.return_value.first.return_value = trade_detail_row()

    response = read_trade_detail_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "trade": {
            "id": 1,
            "paidTime": "2026-08-05T14:30:00",
            "price": 12500,
            "productImageUrl": "https://example.com/mock/market-product-001.jpg",
            "cube": {
                "id": 2,
                "serialNumber": "#012",
                "productName": "RUBY CUBE",
                "artistName": "JENNIE",
            },
            "timeline": [
                {
                    "status": "PAID",
                    "label": "결제 완료",
                    "time": "2026-08-05T14:30:00",
                    "completed": True,
                },
                {
                    "status": "SENT",
                    "label": "판매자 발송",
                    "time": "2026-08-05T15:09:00",
                    "completed": True,
                },
                {
                    "status": "SHIPPING",
                    "label": "배송 중",
                    "time": "2026-08-07T09:45:00",
                    "completed": True,
                },
                {
                    "status": "DELIVERED",
                    "label": "배송 완료",
                    "time": None,
                    "completed": False,
                },
                {
                    "status": "COMPLETED",
                    "label": "구매 확정",
                    "time": None,
                    "completed": False,
                },
            ],
        }
    }


def test_read_trade_detail_returns_404_for_unknown_or_other_user_trade() -> None:
    db = Mock(spec=Session)
    db.execute.return_value.first.return_value = None

    response = read_trade_detail_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "TRADE_NOT_FOUND",
        "message": "거래 정보를 찾을 수 없습니다.",
    }


def test_read_trade_detail_swagger_responses() -> None:
    operation = app.openapi()["paths"]["/api/v1/users/me/trades/{tradeId}"]["get"]

    assert set(operation["responses"]) == {"200", "404"}
    assert operation["security"] == [{"HTTPBearer": []}]


def test_complete_trade_updates_trade_and_creates_certificate(monkeypatch) -> None:
    completed_time = datetime.fromisoformat("2026-08-10T18:43:00")
    monkeypatch.setattr(
        "app.services.market._kst_now_naive",
        lambda: completed_time,
    )
    db = Mock(spec=Session)
    trade, buyer = set_complete_trade_results(db)

    response = complete_trade_request(db, trade_id=23)

    assert response.status_code == 200
    assert trade.status == TradeStatus.COMPLETED
    assert trade.completed_time == completed_time
    inserted = db.add.call_args.args[0]
    assert isinstance(inserted, DigitalCertificate)
    assert inserted.trade_id == 23
    assert inserted.network == get_settings().blockchain_network
    assert inserted.token_standard == "ERC-721"
    assert inserted.token_id == "44"
    assert inserted.contract_address == CERTIFICATE_VALUES["contract_address"]
    assert inserted.tx_hash == CERTIFICATE_VALUES["tx_hash"]
    assert inserted.metadata_url == CERTIFICATE_VALUES["metadata_url"]
    assert response.json() == {
        "certificate": {
            "id": 1,
            "tradeId": 23,
            "ownerNickname": buyer.nickname,
            "completedTime": "2026-08-10T18:43:00",
            "network": get_settings().blockchain_network,
            "tokenStandard": "ERC-721",
            "tokenId": "44",
            "contractAddress": CERTIFICATE_VALUES["contract_address"],
            "txHash": CERTIFICATE_VALUES["tx_hash"],
            "metadataUrl": CERTIFICATE_VALUES["metadata_url"],
        }
    }
    db.commit.assert_called_once()


def test_complete_trade_releases_cube_to_owned() -> None:
    db = Mock(spec=Session)
    cube = traded_cube(status=CubeStatus.TRADE_PENDING)
    set_complete_trade_results(db, cube=cube)

    response = complete_trade_request(db, trade_id=23)

    assert response.status_code == 200
    assert cube.status == CubeStatus.OWNED
    cube_query = compiled_query(db.scalar.call_args_list[2])
    assert "market_product.cube_id = cube.id" in cube_query
    assert "sell_listing.market_product_id = market_product.id" in cube_query
    assert "sell_listing.id = 7" in cube_query
    assert "FOR UPDATE" in cube_query
    db.commit.assert_called_once()


def test_complete_trade_keeps_cube_status_when_cube_is_disabled() -> None:
    db = Mock(spec=Session)
    cube = traded_cube(status=CubeStatus.DISABLED)
    set_complete_trade_results(db, cube=cube)

    response = complete_trade_request(db, trade_id=23)

    assert response.status_code == 200
    # 거래와 무관하게 비활성화된 큐브를 다시 살리지 않습니다.
    assert cube.status == CubeStatus.DISABLED
    db.commit.assert_called_once()


def test_complete_trade_requests_transfer_with_seller_and_serial_number() -> None:
    db = Mock(spec=Session)
    set_complete_trade_results(db, seller_user_id=7, serial_number="NO.0055")
    transfer = Mock(return_value=dict(CERTIFICATE_VALUES))

    response = complete_trade_request(db, trade_id=23, transfer=transfer)

    assert response.status_code == 200
    assert transfer.call_args.kwargs["trade_id"] == 23
    assert transfer.call_args.kwargs["seller_user_id"] == 7
    assert transfer.call_args.kwargs["buyer_user_id"] == 1
    assert transfer.call_args.kwargs["serial_number"] == "NO.0055"


def test_complete_trade_releases_trade_lock_before_transfer() -> None:
    db = Mock(spec=Session)
    set_complete_trade_results(db)
    order: list[str] = []
    db.rollback.side_effect = lambda: order.append("rollback")
    transfer = Mock(
        side_effect=lambda **_: order.append("transfer") or dict(CERTIFICATE_VALUES)
    )

    complete_trade_request(db, trade_id=23, transfer=transfer)

    # 수십 초 걸리는 외부 호출 전에 거래 행 잠금을 풀어야 합니다.
    assert order == ["rollback", "transfer"]


def test_complete_trade_reuses_confirmed_transfer_operation() -> None:
    db = Mock(spec=Session)
    set_complete_trade_results(db)
    db.scalar.side_effect = [
        BlockchainOperation(
            id=5,
            operation_type=BlockchainOperationType.TRANSFER,
            status=BlockchainOperationStatus.CONFIRMED,
            token_id=31,
            trade_id=23,
            idempotency_key="key-9",
            tx_hash=CERTIFICATE_VALUES["tx_hash"],
        ),
        traded_cube(status=CubeStatus.TRADE_PENDING),
    ]
    transfer = Mock()

    with patch(
        "app.services.market.certificate_values",
        return_value=dict(CERTIFICATE_VALUES),
    ) as values:
        response = complete_trade_request(db, trade_id=23, transfer=transfer)

    assert response.status_code == 200
    # 완료 알림으로 이미 확정된 거래는 다시 이전을 요청하지 않습니다.
    transfer.assert_not_called()
    values.assert_called_once_with(token_id=31, tx_hash=CERTIFICATE_VALUES["tx_hash"])


def test_complete_trade_returns_409_when_transfer_is_in_progress() -> None:
    db = Mock(spec=Session)
    set_complete_trade_results(db)
    # 확정된 작업은 없고, 아직 대기 중인 이전 작업만 있는 상태입니다.
    db.scalar.side_effect = [
        None,
        BlockchainOperation(
            id=6,
            operation_type=BlockchainOperationType.TRANSFER,
            status=BlockchainOperationStatus.REQUESTED,
            token_id=31,
            trade_id=23,
            idempotency_key="key-8",
        ),
    ]
    transfer = Mock()

    response = complete_trade_request(db, trade_id=23, transfer=transfer)

    assert response.status_code == 409
    assert response.json()["code"] == "TRADE_CONFIRMATION_TIMEOUT"
    # 같은 거래에 이전을 중복 접수하지 않습니다.
    transfer.assert_not_called()
    db.add.assert_not_called()


def test_complete_trade_queries_transfer_operation_by_status() -> None:
    db = Mock(spec=Session)
    set_complete_trade_results(db)
    db.scalar.side_effect = [None, None, traded_cube(status=CubeStatus.TRADE_PENDING)]

    complete_trade_request(db, trade_id=23)

    confirmed_query = compiled_query(db.scalar.call_args_list[0])
    requested_query = compiled_query(db.scalar.call_args_list[1])
    assert "blockchain_operation.trade_id = 23" in confirmed_query
    assert "blockchain_operation.operation_type = 'TRANSFER'" in confirmed_query
    assert "blockchain_operation.status = 'CONFIRMED'" in confirmed_query
    assert "blockchain_operation.status = 'REQUESTED'" in requested_query


def test_complete_trade_returns_409_when_transfer_is_rejected() -> None:
    db = Mock(spec=Session)
    set_complete_trade_results(db)
    transfer = Mock(
        side_effect=BlockchainError(code="TRANSFER_OWNER_MISMATCH", message="mismatch")
    )

    response = complete_trade_request(db, trade_id=23, transfer=transfer)

    assert response.status_code == 409
    assert response.json() == {
        "code": "TRADE_TRANSFER_REJECTED",
        "message": "NFT 이전 요청이 거절되었습니다.",
    }
    db.add.assert_not_called()


def test_complete_trade_returns_409_when_confirmation_times_out() -> None:
    db = Mock(spec=Session)
    set_complete_trade_results(db)
    transfer = Mock(
        side_effect=BlockchainError(code="CONFIRMATION_TIMEOUT", message="timeout")
    )

    response = complete_trade_request(db, trade_id=23, transfer=transfer)

    assert response.status_code == 409
    assert response.json()["code"] == "TRADE_CONFIRMATION_TIMEOUT"
    db.add.assert_not_called()


def test_complete_trade_returns_500_when_blockchain_is_unreachable() -> None:
    db = Mock(spec=Session)
    set_complete_trade_results(db)
    transfer = Mock(
        side_effect=BlockchainError(code="BLOCKCHAIN_UNREACHABLE", message="down")
    )

    response = complete_trade_request(
        db,
        trade_id=23,
        transfer=transfer,
        raise_server_exceptions=False,
    )

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "서버 내부 오류가 발생했습니다.",
    }


def test_complete_trade_returns_404_for_unknown_or_other_user_trade() -> None:
    db = Mock(spec=Session)
    db.execute.return_value.first.return_value = None

    response = complete_trade_request(db, trade_id=404)

    assert response.status_code == 404
    assert response.json() == {
        "code": "TRADE_NOT_FOUND",
        "message": "거래 정보를 찾을 수 없습니다.",
    }
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_complete_trade_returns_409_when_trade_is_not_delivered() -> None:
    db = Mock(spec=Session)
    db.execute.return_value.first.return_value = complete_trade_row(
        status=TradeStatus.COMPLETED
    )

    response = complete_trade_request(db, trade_id=23)

    assert response.status_code == 409
    assert response.json() == {
        "code": "TRADE_NOT_DELIVERED",
        "message": "배송 완료 상태인 거래만 구매 확정할 수 있습니다.",
    }
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_complete_trade_swagger_responses() -> None:
    operation = app.openapi()["paths"]["/api/v1/users/me/trades/{tradeId}/complete"][
        "patch"
    ]

    assert set(operation["responses"]) == {"200", "404", "409"}
    assert operation["security"] == [{"HTTPBearer": []}]


# --- 마켓 조회: GET /api/v1/users/me/market ---

MARKET_OWNERSHIP_NOT_FOUND_RESPONSE = {
    "code": "CUBE_OWNERSHIP_NOT_FOUND",
    "message": "큐브 소유권 정보를 찾을 수 없습니다.",
}
MARKET_AFFINITY_NOT_FOUND_RESPONSE = {
    "code": "CUBE_AFFINITY_NOT_FOUND",
    "message": "큐브 친밀도 정보를 찾을 수 없습니다.",
}


def read_market_request(db: Mock):
    with api_client(db) as client:
        return client.get("/api/v1/users/me/market")


def market_ownership(
    *,
    profile_character_img_url: str | None = "https://cdn.example.com/profile_002.png",
    avatar_nickname: str | None = "젠득이",
    with_affinity: bool = True,
) -> CubeOwnership:
    level = Level(id=3, level=3, level_name=LevelName.CLOSE, level_xp=800)
    return CubeOwnership(
        id=1,
        user_id=1,
        avatar_nickname=avatar_nickname,
        ownership_status=OwnershipStatus.ACTIVE,
        is_last_accessed=True,
        user=User(id=1, profile_character_img_url=profile_character_img_url),
        affinity=(
            Affinity(id=1, current_xp=1245, level_info=level)
            if with_affinity
            else None
        ),
    )


def market_cube(
    *,
    cube_id: int,
    product_name: str,
    artist_name: str = "Jennie",
) -> Cube:
    return Cube(
        id=cube_id,
        serial_number=f"NO.{cube_id:04d}",
        product_name=product_name,
        artist_name=artist_name,
        status=CubeStatus.OWNED,
        deleted_at=None,
    )


def market_product(
    *,
    market_product_id: int,
    cube_id: int,
    product_image_url: str | None = "https://cdn.example.com/cube.png",
) -> MarketProduct:
    return MarketProduct(
        id=market_product_id,
        cube_id=cube_id,
        product_image_url=product_image_url,
        deleted_at=None,
    )


def set_market_results(
    db: Mock,
    *,
    ownership: CubeOwnership | None,
    total_trade_count: int | None = 0,
    product_rows: list[tuple[Cube, MarketProduct]] | None = None,
    trade_rows: list[tuple[str, int]] | None = None,
) -> None:
    """서비스가 db.scalar / db.execute 를 호출하는 순서대로 결과를 지정합니다."""
    db.scalar.side_effect = [ownership, total_trade_count]
    db.execute.side_effect = [
        Mock(all=Mock(return_value=product_rows or [])),
        Mock(all=Mock(return_value=trade_rows or [])),
    ]


def test_read_market_returns_profile_and_representative_products():
    db = Mock(spec=Session)
    cube_one = market_cube(cube_id=1, product_name="JENNIE RUBY CUBE")
    cube_two = market_cube(
        cube_id=2,
        product_name="BIGBANG MADE CUBE",
        artist_name="Big Bang",
    )
    set_market_results(
        db,
        ownership=market_ownership(),
        total_trade_count=24,
        product_rows=[
            (cube_one, market_product(market_product_id=1, cube_id=1)),
            (cube_two, market_product(market_product_id=2, cube_id=2)),
        ],
        trade_rows=[("JENNIE RUBY CUBE", 12500)],
    )

    response = read_market_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "profile": {
            "profileCharacterImgUrl": "https://cdn.example.com/profile_002.png",
            "avatarNickname": "젠득이",
            "level": 3,
            "levelName": "Close",
            "totalTradeCount": 24,
        },
        "products": [
            {
                "representativeCubeId": 1,
                "marketProductId": 1,
                "productName": "JENNIE RUBY CUBE",
                "artistName": "Jennie",
                "productImageUrl": "https://cdn.example.com/cube.png",
                "latestTradePrice": 12500,
            },
            {
                "representativeCubeId": 2,
                "marketProductId": 2,
                "productName": "BIGBANG MADE CUBE",
                "artistName": "Big Bang",
                "productImageUrl": "https://cdn.example.com/cube.png",
                "latestTradePrice": None,
            },
        ],
    }
    db.commit.assert_not_called()


def test_read_market_groups_same_product_name_into_smallest_cube_id():
    db = Mock(spec=Session)
    set_market_results(
        db,
        ownership=market_ownership(),
        product_rows=[
            (
                market_cube(cube_id=3, product_name="JENNIE RUBY CUBE"),
                market_product(market_product_id=3, cube_id=3),
            ),
            (
                market_cube(cube_id=7, product_name="JENNIE RUBY CUBE"),
                market_product(market_product_id=7, cube_id=7),
            ),
        ],
    )

    response = read_market_request(db)

    assert response.status_code == 200
    products = response.json()["products"]
    assert len(products) == 1
    assert products[0]["representativeCubeId"] == 3
    assert products[0]["marketProductId"] == 3


def test_read_market_treats_different_letter_case_as_different_products():
    db = Mock(spec=Session)
    set_market_results(
        db,
        ownership=market_ownership(),
        product_rows=[
            (
                market_cube(cube_id=1, product_name="JENNIE RUBY CUBE"),
                market_product(market_product_id=1, cube_id=1),
            ),
            (
                market_cube(cube_id=2, product_name="jennie ruby cube"),
                market_product(market_product_id=2, cube_id=2),
            ),
        ],
    )

    response = read_market_request(db)

    assert response.status_code == 200
    assert [item["productName"] for item in response.json()["products"]] == [
        "JENNIE RUBY CUBE",
        "jennie ruby cube",
    ]


def test_read_market_orders_products_by_representative_cube_id():
    db = Mock(spec=Session)
    set_market_results(
        db,
        ownership=market_ownership(),
        product_rows=[
            (
                market_cube(cube_id=2, product_name="B CUBE"),
                market_product(market_product_id=2, cube_id=2),
            ),
            (
                market_cube(cube_id=5, product_name="A CUBE"),
                market_product(market_product_id=5, cube_id=5),
            ),
            (
                market_cube(cube_id=9, product_name="C CUBE"),
                market_product(market_product_id=9, cube_id=9),
            ),
        ],
    )

    response = read_market_request(db)

    assert response.status_code == 200
    assert [item["representativeCubeId"] for item in response.json()["products"]] == [
        2,
        5,
        9,
    ]


def test_read_market_uses_most_recent_settled_trade_price():
    db = Mock(spec=Session)
    set_market_results(
        db,
        ownership=market_ownership(),
        product_rows=[
            (
                market_cube(cube_id=1, product_name="JENNIE RUBY CUBE"),
                market_product(market_product_id=1, cube_id=1),
            ),
        ],
        # 쿼리가 최신순으로 정렬해 주므로 같은 제품명의 첫 행이 최근 체결가입니다.
        trade_rows=[
            ("JENNIE RUBY CUBE", 12500),
            ("JENNIE RUBY CUBE", 99000),
        ],
    )

    response = read_market_request(db)

    assert response.status_code == 200
    assert response.json()["products"][0]["latestTradePrice"] == 12500


def test_read_market_returns_null_price_when_no_settled_trade():
    db = Mock(spec=Session)
    set_market_results(
        db,
        ownership=market_ownership(),
        product_rows=[
            (
                market_cube(cube_id=1, product_name="JENNIE RUBY CUBE"),
                market_product(market_product_id=1, cube_id=1),
            ),
        ],
        trade_rows=[],
    )

    response = read_market_request(db)

    assert response.status_code == 200
    assert response.json()["products"][0]["latestTradePrice"] is None


def test_read_market_returns_null_image_when_representative_product_has_none():
    db = Mock(spec=Session)
    set_market_results(
        db,
        ownership=market_ownership(),
        product_rows=[
            (
                market_cube(cube_id=1, product_name="JENNIE RUBY CUBE"),
                market_product(
                    market_product_id=1,
                    cube_id=1,
                    product_image_url=None,
                ),
            ),
        ],
    )

    response = read_market_request(db)

    assert response.status_code == 200
    assert response.json()["products"][0]["productImageUrl"] is None


def test_read_market_returns_empty_products_when_no_product_group():
    db = Mock(spec=Session)
    set_market_results(db, ownership=market_ownership(), product_rows=[])

    response = read_market_request(db)

    assert response.status_code == 200
    assert response.json()["products"] == []
    # 제품군이 없으면 시세 조회 쿼리를 실행하지 않습니다.
    assert db.execute.call_count == 1


def test_read_market_returns_null_profile_fields_when_not_set():
    db = Mock(spec=Session)
    set_market_results(
        db,
        ownership=market_ownership(
            profile_character_img_url=None,
            avatar_nickname=None,
        ),
    )

    response = read_market_request(db)

    assert response.status_code == 200
    assert response.json()["profile"]["profileCharacterImgUrl"] is None
    assert response.json()["profile"]["avatarNickname"] is None


def test_read_market_returns_zero_trade_count_when_count_is_none():
    db = Mock(spec=Session)
    set_market_results(db, ownership=market_ownership(), total_trade_count=None)

    response = read_market_request(db)

    assert response.status_code == 200
    assert response.json()["profile"]["totalTradeCount"] == 0


def test_read_market_returns_404_when_ownership_not_found():
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = read_market_request(db)

    assert response.status_code == 404
    assert response.json() == MARKET_OWNERSHIP_NOT_FOUND_RESPONSE
    db.execute.assert_not_called()


def test_read_market_returns_404_when_affinity_not_found():
    db = Mock(spec=Session)
    db.scalar.return_value = market_ownership(with_affinity=False)

    response = read_market_request(db)

    assert response.status_code == 404
    assert response.json() == MARKET_AFFINITY_NOT_FOUND_RESPONSE
    db.execute.assert_not_called()


def test_read_market_queries_only_own_active_last_accessed_ownership():
    db = Mock(spec=Session)
    set_market_results(db, ownership=market_ownership())

    read_market_request(db)

    where_clause = compiled_query(db.scalar.call_args_list[0]).split("WHERE")[1]
    assert "cube_ownership.user_id = 1" in where_clause
    assert "cube_ownership.ownership_status = 'ACTIVE'" in where_clause
    assert "cube_ownership.is_last_accessed IS true" in where_clause


def test_read_market_counts_only_completed_trades_of_buyer_or_seller():
    db = Mock(spec=Session)
    set_market_results(db, ownership=market_ownership())

    read_market_request(db)

    query = compiled_query(db.scalar.call_args_list[1])
    assert "count(trade.id)" in query
    assert "trade.status = 'COMPLETED'" in query
    assert "trade.buyer_user_id = 1 OR sell_listing.user_id = 1" in query


def test_read_market_excludes_deleted_and_disabled_cubes_from_products():
    db = Mock(spec=Session)
    set_market_results(
        db,
        ownership=market_ownership(),
        product_rows=[
            (
                market_cube(cube_id=1, product_name="JENNIE RUBY CUBE"),
                market_product(market_product_id=1, cube_id=1),
            ),
        ],
    )

    read_market_request(db)

    query = compiled_query(db.execute.call_args_list[0])
    assert "cube.deleted_at IS NULL" in query
    assert "cube.status != 'DISABLED'" in query
    assert "market_product.deleted_at IS NULL" in query
    assert "ORDER BY cube.id ASC" in query


def test_read_market_orders_trade_price_query_by_paid_time_and_trade_id():
    db = Mock(spec=Session)
    set_market_results(
        db,
        ownership=market_ownership(),
        product_rows=[
            (
                market_cube(cube_id=1, product_name="JENNIE RUBY CUBE"),
                market_product(market_product_id=1, cube_id=1),
            ),
        ],
    )

    read_market_request(db)

    query = compiled_query(db.execute.call_args_list[1])
    assert "sell_listing.price" in query
    assert (
        "trade.status IN ('PAID', 'SENT', 'SHIPPING', 'DELIVERED', 'COMPLETED')"
        in query
    )
    assert "ORDER BY trade.paid_time DESC, trade.id DESC" in query
    # 삭제된 판매글의 과거 거래도 시세 계산에 포함합니다.
    assert "sell_listing.deleted_at IS NULL" not in query


def test_read_market_swagger_contract():
    operation = app.openapi()["paths"]["/api/v1/users/me/market"]["get"]

    assert set(operation["responses"]) == {"200", "404"}
    assert operation["security"] == [{"HTTPBearer": []}]


def compiled_query(call) -> str:
    return str(call.args[0].compile(compile_kwargs={"literal_binds": True}))


# --- 마켓 세부 상품 조회: GET /users/me/market/products/{id}/sell-listings ---

MARKET_PRODUCT_NOT_FOUND_RESPONSE = {
    "code": "MARKET_PRODUCT_NOT_FOUND",
    "message": "마켓 제품 정보를 찾을 수 없습니다.",
}
INVALID_REQUEST_RESPONSE = {
    "code": "INVALID_REQUEST",
    "message": "요청값이 올바르지 않습니다.",
}


def read_market_sell_listings_request(db: Mock, *, representative_cube_id: int | str = 3):
    with api_client(db) as client:
        return client.get(
            "/api/v1/users/me/market/products/"
            f"{representative_cube_id}/sell-listings"
        )


def market_sell_listing(
    *,
    sell_listing_id: int,
    market_product_id: int,
    price: int,
    user_id: int = 3,
) -> SellListing:
    return SellListing(
        id=sell_listing_id,
        market_product_id=market_product_id,
        user_id=user_id,
        price=price,
        status=SellListingStatus.ACTIVE,
        deleted_at=None,
    )


def set_sell_listing_results(
    db: Mock,
    *,
    product_name: str | None,
    rows: list[tuple[SellListing, Cube, str | None, int]] | None = None,
) -> None:
    """서비스가 db.scalar / db.execute 를 호출하는 순서대로 결과를 지정합니다."""
    db.scalar.return_value = product_name
    db.execute.return_value.all.return_value = rows or []


def test_read_market_sell_listings_returns_listings_of_same_product_name():
    db = Mock(spec=Session)
    set_sell_listing_results(
        db,
        product_name="ROSE ROISE CUBE",
        rows=[
            (
                market_sell_listing(
                    sell_listing_id=3,
                    market_product_id=9,
                    price=42000,
                ),
                market_cube(cube_id=9, product_name="ROSE ROISE CUBE", artist_name="ROSE"),
                "로제짱",
                1,
            ),
            (
                market_sell_listing(
                    sell_listing_id=2,
                    market_product_id=3,
                    price=35000,
                ),
                market_cube(cube_id=3, product_name="ROSE ROISE CUBE", artist_name="ROSE"),
                "로제짱",
                1,
            ),
        ],
    )

    response = read_market_sell_listings_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "sellListings": [
            {
                "sellListingId": 3,
                "productName": "ROSE ROISE CUBE",
                "serialNumber": "NO.0009",
                "sellerNickname": "로제짱",
                "price": 42000,
                "likeCount": 1,
            },
            {
                "sellListingId": 2,
                "productName": "ROSE ROISE CUBE",
                "serialNumber": "NO.0003",
                "sellerNickname": "로제짱",
                "price": 35000,
                "likeCount": 1,
            },
        ]
    }
    db.commit.assert_not_called()


def test_read_market_sell_listings_returns_empty_list_when_nothing_on_sale():
    db = Mock(spec=Session)
    set_sell_listing_results(db, product_name="ROSE ROISE CUBE", rows=[])

    response = read_market_sell_listings_request(db)

    assert response.status_code == 200
    assert response.json() == {"sellListings": []}


def test_read_market_sell_listings_returns_zero_like_count():
    db = Mock(spec=Session)
    set_sell_listing_results(
        db,
        product_name="ROSE ROISE CUBE",
        rows=[
            (
                market_sell_listing(sell_listing_id=2, market_product_id=3, price=35000),
                market_cube(cube_id=3, product_name="ROSE ROISE CUBE"),
                "로제짱",
                0,
            ),
        ],
    )

    response = read_market_sell_listings_request(db)

    assert response.status_code == 200
    assert response.json()["sellListings"][0]["likeCount"] == 0


def test_read_market_sell_listings_returns_null_seller_nickname():
    db = Mock(spec=Session)
    set_sell_listing_results(
        db,
        product_name="ROSE ROISE CUBE",
        rows=[
            (
                market_sell_listing(sell_listing_id=2, market_product_id=3, price=35000),
                market_cube(cube_id=3, product_name="ROSE ROISE CUBE"),
                None,
                1,
            ),
        ],
    )

    response = read_market_sell_listings_request(db)

    assert response.status_code == 200
    assert response.json()["sellListings"][0]["sellerNickname"] is None


def test_read_market_sell_listings_excludes_product_name_with_different_letter_case():
    db = Mock(spec=Session)
    set_sell_listing_results(
        db,
        product_name="ROSE ROISE CUBE",
        rows=[
            (
                market_sell_listing(sell_listing_id=3, market_product_id=9, price=42000),
                market_cube(cube_id=9, product_name="ROSE ROISE CUBE"),
                "로제짱",
                1,
            ),
            (
                market_sell_listing(sell_listing_id=2, market_product_id=3, price=35000),
                market_cube(cube_id=3, product_name="rose roise cube"),
                "로제짱",
                1,
            ),
        ],
    )

    response = read_market_sell_listings_request(db)

    assert response.status_code == 200
    assert [item["sellListingId"] for item in response.json()["sellListings"]] == [3]


def test_read_market_sell_listings_allows_minimum_representative_cube_id():
    db = Mock(spec=Session)
    set_sell_listing_results(db, product_name="JENNIE RUBY CUBE", rows=[])

    response = read_market_sell_listings_request(db, representative_cube_id=1)

    assert response.status_code == 200
    assert response.json() == {"sellListings": []}


def test_read_market_sell_listings_returns_400_when_cube_id_is_zero():
    db = Mock(spec=Session)

    response = read_market_sell_listings_request(db, representative_cube_id=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_read_market_sell_listings_returns_400_when_cube_id_is_not_a_number():
    db = Mock(spec=Session)

    response = read_market_sell_listings_request(db, representative_cube_id="abc")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_read_market_sell_listings_returns_404_when_representative_cube_not_found():
    db = Mock(spec=Session)
    set_sell_listing_results(db, product_name=None)

    response = read_market_sell_listings_request(db)

    assert response.status_code == 404
    assert response.json() == MARKET_PRODUCT_NOT_FOUND_RESPONSE
    db.execute.assert_not_called()


def test_read_market_sell_listings_requires_active_representative_cube_and_product():
    db = Mock(spec=Session)
    set_sell_listing_results(db, product_name="ROSE ROISE CUBE", rows=[])

    read_market_sell_listings_request(db)

    query = compiled_query(db.scalar.call_args)
    assert "cube.product_name" in query
    assert "cube.id = 3" in query
    assert "cube.deleted_at IS NULL" in query
    assert "cube.status != 'DISABLED'" in query
    assert "market_product.deleted_at IS NULL" in query


def test_read_market_sell_listings_returns_only_active_listings_ordered_by_id_desc():
    db = Mock(spec=Session)
    set_sell_listing_results(db, product_name="ROSE ROISE CUBE", rows=[])

    read_market_sell_listings_request(db)

    query = compiled_query(db.execute.call_args)
    assert "sell_listing.status = 'ACTIVE'" in query
    assert "sell_listing.deleted_at IS NULL" in query
    assert "cube.product_name = 'ROSE ROISE CUBE'" in query
    assert "cube.deleted_at IS NULL" in query
    assert "cube.status != 'DISABLED'" in query
    assert "ORDER BY sell_listing.id DESC" in query


def test_read_market_sell_listings_counts_only_liked_rows():
    db = Mock(spec=Session)
    set_sell_listing_results(db, product_name="ROSE ROISE CUBE", rows=[])

    read_market_sell_listings_request(db)

    query = compiled_query(db.execute.call_args)
    assert "count(selling_list_like.id)" in query
    assert "selling_list_like.is_liked IS true" in query
    assert "selling_list_like.selling_list_id = sell_listing.id" in query


def test_read_market_sell_listings_swagger_contract():
    operation = app.openapi()["paths"][
        "/api/v1/users/me/market/products/{representativeCubeId}/sell-listings"
    ]["get"]

    assert set(operation["responses"]) == {"200", "404"}
    assert operation["security"] == [{"HTTPBearer": []}]


# --- 마켓 검색 결과 조회: GET /api/v1/users/me/market/search ---


def search_market_request(db: Mock, *, keyword: str | None = "ROSE"):
    params = {} if keyword is None else {"keyword": keyword}
    with api_client(db) as client:
        return client.get("/api/v1/users/me/market/search", params=params)


def set_search_results(
    db: Mock,
    *,
    rows: list[tuple[SellListing, Cube, str | None, int]] | None = None,
) -> None:
    """서비스가 db.execute 를 호출한 결과를 지정합니다."""
    db.execute.return_value.all.return_value = rows or []


def test_search_market_returns_sell_listings_matching_keyword():
    db = Mock(spec=Session)
    set_search_results(
        db,
        rows=[
            (
                market_sell_listing(
                    sell_listing_id=3,
                    market_product_id=9,
                    price=42000,
                ),
                market_cube(
                    cube_id=99,
                    product_name="ROSE ROISE CUBE",
                    artist_name="ROSE",
                ),
                "로제짱",
                1,
            ),
            (
                market_sell_listing(
                    sell_listing_id=2,
                    market_product_id=3,
                    price=35000,
                ),
                market_cube(
                    cube_id=22,
                    product_name="ROSE ROISE CUBE",
                    artist_name="ROSE",
                ),
                "로제짱",
                1,
            ),
        ],
    )

    response = search_market_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "sellListings": [
            {
                "sellListingId": 3,
                "productName": "ROSE ROISE CUBE",
                "serialNumber": "NO.0099",
                "sellerNickname": "로제짱",
                "price": 42000,
                "likeCount": 1,
            },
            {
                "sellListingId": 2,
                "productName": "ROSE ROISE CUBE",
                "serialNumber": "NO.0022",
                "sellerNickname": "로제짱",
                "price": 35000,
                "likeCount": 1,
            },
        ]
    }
    db.commit.assert_not_called()


def test_search_market_returns_listing_matching_artist_name_only():
    db = Mock(spec=Session)
    set_search_results(
        db,
        rows=[
            (
                market_sell_listing(
                    sell_listing_id=5,
                    market_product_id=7,
                    price=30000,
                ),
                market_cube(
                    cube_id=7,
                    product_name="RUBY CUBE",
                    artist_name="JENNIE",
                ),
                "제니팬",
                0,
            ),
        ],
    )

    response = search_market_request(db, keyword="JENNIE")

    assert response.status_code == 200
    assert response.json() == {
        "sellListings": [
            {
                "sellListingId": 5,
                "productName": "RUBY CUBE",
                "serialNumber": "NO.0007",
                "sellerNickname": "제니팬",
                "price": 30000,
                "likeCount": 0,
            }
        ]
    }


def test_search_market_returns_listing_once_when_both_names_match():
    db = Mock(spec=Session)
    set_search_results(
        db,
        rows=[
            (
                market_sell_listing(
                    sell_listing_id=3,
                    market_product_id=9,
                    price=42000,
                ),
                market_cube(
                    cube_id=99,
                    product_name="ROSE ROISE CUBE",
                    artist_name="ROSE",
                ),
                "로제짱",
                1,
            ),
        ],
    )

    response = search_market_request(db)

    assert response.status_code == 200
    assert [item["sellListingId"] for item in response.json()["sellListings"]] == [3]


def test_search_market_returns_empty_list_when_no_listing_matches():
    db = Mock(spec=Session)
    set_search_results(db, rows=[])

    response = search_market_request(db, keyword="없는제품")

    assert response.status_code == 200
    assert response.json() == {"sellListings": []}


def test_search_market_returns_null_seller_nickname_and_zero_like_count():
    db = Mock(spec=Session)
    set_search_results(
        db,
        rows=[
            (
                market_sell_listing(
                    sell_listing_id=2,
                    market_product_id=3,
                    price=35000,
                ),
                market_cube(cube_id=3, product_name="ROSE ROISE CUBE"),
                None,
                0,
            ),
        ],
    )

    response = search_market_request(db)

    assert response.status_code == 200
    assert response.json()["sellListings"][0]["sellerNickname"] is None
    assert response.json()["sellListings"][0]["likeCount"] == 0


def test_search_market_includes_own_sell_listing():
    db = Mock(spec=Session)
    set_search_results(
        db,
        rows=[
            (
                market_sell_listing(
                    sell_listing_id=4,
                    market_product_id=9,
                    price=42000,
                    user_id=1,
                ),
                market_cube(cube_id=9, product_name="ROSE ROISE CUBE"),
                "나",
                0,
            ),
        ],
    )

    response = search_market_request(db)

    assert response.status_code == 200
    assert [item["sellListingId"] for item in response.json()["sellListings"]] == [4]
    # 현재 사용자로 결과를 거르지 않는지 확인합니다.
    assert "sell_listing.user_id = 1" not in compiled_query(db.execute.call_args)


def test_search_market_allows_single_character_keyword():
    db = Mock(spec=Session)
    set_search_results(db, rows=[])

    response = search_market_request(db, keyword="R")

    assert response.status_code == 200
    assert response.json() == {"sellListings": []}
    assert "'%R%'" in compiled_query(db.execute.call_args)


def test_search_market_returns_400_when_keyword_is_missing():
    db = Mock(spec=Session)

    response = search_market_request(db, keyword=None)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_search_market_returns_400_when_keyword_is_empty():
    db = Mock(spec=Session)

    response = search_market_request(db, keyword="")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_search_market_returns_400_when_keyword_is_only_whitespace():
    db = Mock(spec=Session)

    response = search_market_request(db, keyword="   ")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_search_market_strips_keyword_before_matching():
    db = Mock(spec=Session)
    set_search_results(db, rows=[])

    search_market_request(db, keyword="  ROSE  ")

    query = compiled_query(db.execute.call_args)
    assert "cube.product_name LIKE '%ROSE%'" in query
    assert "cube.artist_name LIKE '%ROSE%'" in query


def test_search_market_matches_product_name_or_artist_name():
    db = Mock(spec=Session)
    set_search_results(db, rows=[])

    search_market_request(db)

    query = compiled_query(db.execute.call_args)
    assert (
        "cube.product_name LIKE '%ROSE%' ESCAPE '\\' "
        "OR cube.artist_name LIKE '%ROSE%' ESCAPE '\\'" in query
    )


def test_search_market_escapes_like_wildcards_in_keyword():
    db = Mock(spec=Session)
    set_search_results(db, rows=[])

    response = search_market_request(db, keyword="50%_")

    assert response.status_code == 200
    query = compiled_query(db.execute.call_args)
    assert "cube.product_name LIKE '%50\\%\\_%' ESCAPE '\\'" in query
    assert "cube.artist_name LIKE '%50\\%\\_%' ESCAPE '\\'" in query


def test_search_market_escapes_escape_character_in_keyword():
    db = Mock(spec=Session)
    set_search_results(db, rows=[])

    response = search_market_request(db, keyword="A\\B")

    assert response.status_code == 200
    query = compiled_query(db.execute.call_args)
    assert "cube.product_name LIKE '%A\\\\B%' ESCAPE '\\'" in query
    assert "cube.artist_name LIKE '%A\\\\B%' ESCAPE '\\'" in query


def test_search_market_returns_only_active_listings_ordered_by_id_desc():
    db = Mock(spec=Session)
    set_search_results(db, rows=[])

    search_market_request(db)

    query = compiled_query(db.execute.call_args)
    assert "sell_listing.status = 'ACTIVE'" in query
    assert "sell_listing.deleted_at IS NULL" in query
    assert "cube.deleted_at IS NULL" in query
    assert "cube.status != 'DISABLED'" in query
    assert "market_product.deleted_at IS NULL" in query
    assert "ORDER BY sell_listing.id DESC" in query


def test_search_market_counts_only_liked_rows():
    db = Mock(spec=Session)
    set_search_results(db, rows=[])

    search_market_request(db)

    query = compiled_query(db.execute.call_args)
    assert "count(selling_list_like.id)" in query
    assert "selling_list_like.is_liked IS true" in query
    assert "selling_list_like.selling_list_id = sell_listing.id" in query


def test_search_market_swagger_contract():
    operation = app.openapi()["paths"]["/api/v1/users/me/market/search"]["get"]

    assert set(operation["responses"]) == {"200", "400"}
    assert operation["security"] == [{"HTTPBearer": []}]
# --- 판매글 상세 조회: GET /api/v1/users/me/sell-listings/{sellListingId} ---

SELL_LISTING_NOT_FOUND_RESPONSE = {
    "code": "SELL_LISTING_NOT_FOUND",
    "message": "판매 상품을 찾을 수 없습니다.",
}


def read_sell_listing_detail_request(db: Mock, *, sell_listing_id: int | str = 1):
    with api_client(db) as client:
        return client.get(f"/api/v1/users/me/sell-listings/{sell_listing_id}")


def sell_listing_detail_row(
    *,
    user_id: int = 2,
    status: SellListingStatus = SellListingStatus.ACTIVE,
    profile_character_img_url: str | None = "https://cdn.example.com/profile_1.png",
):
    """상세 조회가 반환하는 (판매글, 판매자, 큐브) 행을 만듭니다."""
    sell_listing = SellListing(
        id=1,
        market_product_id=3,
        user_id=user_id,
        title="제니 루비 큐브 1번 팝니다.",
        description="작년 팝업스토어에서 구매한 제니 솔로 큐브 양도합니다.",
        price=12500,
        status=status,
        created_at=datetime.fromisoformat("2026-08-28T20:30:00"),
        deleted_at=None,
    )
    seller = User(
        id=user_id,
        nickname="uddystar_142",
        profile_character_img_url=profile_character_img_url,
    )
    cube = market_cube(
        cube_id=12,
        product_name="JENNIE RUBY CUBE",
        artist_name="JENNIE",
    )
    return sell_listing, seller, cube


def set_sell_listing_detail_results(
    db: Mock,
    *,
    row: tuple[SellListing, User, Cube] | None,
    image_urls: list[str] | None = None,
) -> None:
    """서비스가 호출하는 db.execute / db.scalars 결과를 지정합니다."""
    db.execute.return_value.first.return_value = row
    db.scalars.return_value = image_urls or []


def test_read_sell_listing_detail_returns_listing_seller_and_cube():
    db = Mock(spec=Session)
    set_sell_listing_detail_results(
        db,
        row=sell_listing_detail_row(),
        image_urls=[
            "https://cdn.example.com/listing_media/1/1.jpg",
            "https://cdn.example.com/listing_media/1/2.jpg",
        ],
    )

    response = read_sell_listing_detail_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "sellListing": {
            "sellListingId": 1,
            "imageUrls": [
                "https://cdn.example.com/listing_media/1/1.jpg",
                "https://cdn.example.com/listing_media/1/2.jpg",
            ],
            "sellerNickname": "uddystar_142",
            "sellerProfileImageUrl": "https://cdn.example.com/profile_1.png",
            "status": "ACTIVE",
            "isMine": False,
            "title": "제니 루비 큐브 1번 팝니다.",
            "description": "작년 팝업스토어에서 구매한 제니 솔로 큐브 양도합니다.",
            "price": 12500,
            "createdAt": "2026-08-28T20:30:00",
            "productName": "JENNIE RUBY CUBE",
            "serialNumber": "NO.0012",
        }
    }
    db.commit.assert_not_called()


def test_read_sell_listing_detail_returns_is_mine_true_for_own_listing():
    db = Mock(spec=Session)
    set_sell_listing_detail_results(db, row=sell_listing_detail_row(user_id=1))

    response = read_sell_listing_detail_request(db)

    assert response.status_code == 200
    assert response.json()["sellListing"]["isMine"] is True


def test_read_sell_listing_detail_returns_sold_listing():
    db = Mock(spec=Session)
    set_sell_listing_detail_results(
        db,
        row=sell_listing_detail_row(status=SellListingStatus.SOLD),
    )

    response = read_sell_listing_detail_request(db)

    assert response.status_code == 200
    assert response.json()["sellListing"]["status"] == "SOLD"


def test_read_sell_listing_detail_returns_empty_image_urls():
    db = Mock(spec=Session)
    set_sell_listing_detail_results(db, row=sell_listing_detail_row(), image_urls=[])

    response = read_sell_listing_detail_request(db)

    assert response.status_code == 200
    assert response.json()["sellListing"]["imageUrls"] == []


def test_read_sell_listing_detail_returns_null_seller_profile_image_url():
    db = Mock(spec=Session)
    set_sell_listing_detail_results(
        db,
        row=sell_listing_detail_row(profile_character_img_url=None),
    )

    response = read_sell_listing_detail_request(db)

    assert response.status_code == 200
    assert response.json()["sellListing"]["sellerProfileImageUrl"] is None


def test_read_sell_listing_detail_returns_404_when_listing_is_unavailable():
    db = Mock(spec=Session)
    set_sell_listing_detail_results(db, row=None)

    response = read_sell_listing_detail_request(db)

    assert response.status_code == 404
    assert response.json() == SELL_LISTING_NOT_FOUND_RESPONSE
    db.scalars.assert_not_called()


def test_read_sell_listing_detail_allows_minimum_sell_listing_id():
    db = Mock(spec=Session)
    set_sell_listing_detail_results(db, row=sell_listing_detail_row())

    response = read_sell_listing_detail_request(db, sell_listing_id=1)

    assert response.status_code == 200


def test_read_sell_listing_detail_returns_400_when_id_is_zero():
    db = Mock(spec=Session)

    response = read_sell_listing_detail_request(db, sell_listing_id=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_read_sell_listing_detail_returns_400_when_id_is_not_a_number():
    db = Mock(spec=Session)

    response = read_sell_listing_detail_request(db, sell_listing_id="abc")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_read_sell_listing_detail_excludes_deleted_listing():
    db = Mock(spec=Session)
    set_sell_listing_detail_results(db, row=sell_listing_detail_row())

    read_sell_listing_detail_request(db, sell_listing_id=7)

    query = compiled_query(db.execute.call_args)
    assert "sell_listing.id = 7" in query
    assert "sell_listing.status != 'DELETED'" in query
    assert "sell_listing.deleted_at IS NULL" in query
    assert '"user".id = sell_listing.user_id' in query
    assert "market_product.id = sell_listing.market_product_id" in query
    assert "cube.id = market_product.cube_id" in query


def test_read_sell_listing_detail_orders_images_by_id_asc():
    db = Mock(spec=Session)
    set_sell_listing_detail_results(db, row=sell_listing_detail_row())

    read_sell_listing_detail_request(db)

    query = compiled_query(db.scalars.call_args)
    assert "listing_media.image_url" in query
    assert "listing_media.sell_listing_id = 1" in query
    assert "listing_media.deleted_at IS NULL" in query
    assert "ORDER BY listing_media.id ASC" in query


def test_read_sell_listing_detail_swagger_contract():
    operation = app.openapi()["paths"][
        "/api/v1/users/me/sell-listings/{sellListingId}"
    ]["get"]

    assert set(operation["responses"]) == {"200", "404"}
    assert operation["security"] == [{"HTTPBearer": []}]
# --- 내 거래 내역 조회: GET /api/v1/users/me/trades ---


def read_trade_history_request(db: Mock):
    with api_client(db) as client:
        return client.get("/api/v1/users/me/trades")


def trade_history_row(
    *,
    trade_id: int = 1,
    status: TradeStatus = TradeStatus.PAID,
    paid_time: str = "2025-04-08T14:30:00",
    price: int = 35000,
    image_url: str | None = "https://cdn.example.com/cube%20card.png",
    cube_id: int = 31,
):
    """거래 내역 조회가 반환하는 (거래, 판매가, 큐브, 이미지 URL) 행을 만듭니다."""
    trade = Trade(
        id=trade_id,
        buyer_user_id=1,
        paid_time=datetime.fromisoformat(paid_time),
        status=status,
    )
    cube = market_cube(
        cube_id=cube_id,
        product_name="BIGBANG MADE CUBE",
        artist_name="Big Bang",
    )
    return trade, price, cube, image_url


def set_trade_history_results(db: Mock, *, rows: list | None = None) -> None:
    """서비스가 db.execute 로 조회한 결과를 지정합니다."""
    db.execute.return_value.all.return_value = rows or []


def test_read_trade_history_returns_buyer_trades():
    db = Mock(spec=Session)
    set_trade_history_results(
        db,
        rows=[
            trade_history_row(trade_id=2, paid_time="2025-04-09T09:00:00", price=42000),
            trade_history_row(trade_id=1),
        ],
    )

    response = read_trade_history_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "trades": [
            {
                "id": 2,
                "productImageUrl": "https://cdn.example.com/cube%20card.png",
                "productName": "BIGBANG MADE CUBE",
                "serialNumber": "NO.0031",
                "price": 42000,
                "paidDate": "2025-04-09",
                "status": "IN_PROGRESS",
            },
            {
                "id": 1,
                "productImageUrl": "https://cdn.example.com/cube%20card.png",
                "productName": "BIGBANG MADE CUBE",
                "serialNumber": "NO.0031",
                "price": 35000,
                "paidDate": "2025-04-08",
                "status": "IN_PROGRESS",
            },
        ]
    }
    db.commit.assert_not_called()


def test_read_trade_history_returns_completed_status():
    db = Mock(spec=Session)
    set_trade_history_results(
        db,
        rows=[trade_history_row(status=TradeStatus.COMPLETED)],
    )

    response = read_trade_history_request(db)

    assert response.status_code == 200
    assert response.json()["trades"][0]["status"] == "COMPLETED"


def test_read_trade_history_maps_ongoing_statuses_to_in_progress():
    db = Mock(spec=Session)
    set_trade_history_results(
        db,
        rows=[
            trade_history_row(trade_id=4, status=TradeStatus.DELIVERED),
            trade_history_row(trade_id=3, status=TradeStatus.SHIPPING),
            trade_history_row(trade_id=2, status=TradeStatus.SENT),
            trade_history_row(trade_id=1, status=TradeStatus.PAID),
        ],
    )

    response = read_trade_history_request(db)

    assert response.status_code == 200
    assert [item["status"] for item in response.json()["trades"]] == [
        "IN_PROGRESS",
        "IN_PROGRESS",
        "IN_PROGRESS",
        "IN_PROGRESS",
    ]


def test_read_trade_history_returns_null_product_image_url():
    db = Mock(spec=Session)
    set_trade_history_results(db, rows=[trade_history_row(image_url=None)])

    response = read_trade_history_request(db)

    assert response.status_code == 200
    assert response.json()["trades"][0]["productImageUrl"] is None


def test_read_trade_history_returns_date_without_time():
    db = Mock(spec=Session)
    set_trade_history_results(
        db,
        rows=[trade_history_row(paid_time="2025-04-08T23:59:59")],
    )

    response = read_trade_history_request(db)

    assert response.status_code == 200
    assert response.json()["trades"][0]["paidDate"] == "2025-04-08"


def test_read_trade_history_returns_empty_list_when_no_trade():
    db = Mock(spec=Session)
    set_trade_history_results(db, rows=[])

    response = read_trade_history_request(db)

    assert response.status_code == 200
    assert response.json() == {"trades": []}


def test_read_trade_history_queries_only_current_user_trades():
    db = Mock(spec=Session)
    set_trade_history_results(db, rows=[])

    read_trade_history_request(db)

    query = compiled_query(db.execute.call_args)
    assert "trade.buyer_user_id = 1" in query
    assert "sell_listing.user_id" not in query


def test_read_trade_history_excludes_deleted_sell_listing_and_market_product():
    db = Mock(spec=Session)
    set_trade_history_results(db, rows=[])

    read_trade_history_request(db)

    query = compiled_query(db.execute.call_args)
    assert "sell_listing.deleted_at IS NULL" in query
    assert "market_product.deleted_at IS NULL" in query
    assert "cube.id = market_product.cube_id" in query
    assert "sell_listing.price" in query


def test_read_trade_history_orders_by_paid_time_and_trade_id_desc():
    db = Mock(spec=Session)
    set_trade_history_results(db, rows=[])

    read_trade_history_request(db)

    query = compiled_query(db.execute.call_args)
    assert "ORDER BY trade.paid_time DESC, trade.id DESC" in query


def test_read_trade_history_uses_first_listing_media_image():
    db = Mock(spec=Session)
    set_trade_history_results(db, rows=[])

    read_trade_history_request(db)

    query = compiled_query(db.execute.call_args)
    assert "listing_media.image_url" in query
    assert "listing_media.sell_listing_id = sell_listing.id" in query
    assert "listing_media.deleted_at IS NULL" in query
    assert "ORDER BY listing_media.id ASC" in query
    assert "LIMIT 1" in query


def test_read_trade_history_swagger_contract():
    operation = app.openapi()["paths"]["/api/v1/users/me/trades"]["get"]

    assert set(operation["responses"]) == {"200"}
    assert operation["security"] == [{"HTTPBearer": []}]
