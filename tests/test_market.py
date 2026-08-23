"""마켓 거래 생성 API 테스트."""

from collections.abc import Iterator
from datetime import datetime
from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models.cube import Cube
from app.models.enums import SellListingStatus, TradeStatus
from app.models.market import (
    DigitalCertificate,
    MarketProduct,
    SellListing,
    Trade,
)
from app.models.user import User


def read_sellable_cubes_request(db: Mock):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            return client.get("/api/v1/users/me/sellable-cubes")
    finally:
        app.dependency_overrides.clear()


def create_trade_request(
    db: Mock,
    *,
    body: dict[str, int | str] | None = None,
):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
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
    finally:
        app.dependency_overrides.clear()


def create_sell_listing_request(
    db: Mock,
    *,
    body: dict[str, object] | None = None,
):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
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
    finally:
        app.dependency_overrides.clear()


def delete_sell_listing_request(
    db: Mock,
    *,
    sell_listing_id: int = 1,
):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            return client.delete(
                f"/api/v1/users/me/sell-listings/{sell_listing_id}"
            )
    finally:
        app.dependency_overrides.clear()


def read_trade_detail_request(
    db: Mock,
    *,
    trade_id: int = 1,
):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            return client.get(f"/api/v1/users/me/trades/{trade_id}")
    finally:
        app.dependency_overrides.clear()


def complete_trade_request(
    db: Mock,
    *,
    trade_id: int = 1,
):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            return client.patch(f"/api/v1/users/me/trades/{trade_id}/complete")
    finally:
        app.dependency_overrides.clear()


def active_sell_listing(*, user_id: int = 2) -> SellListing:
    return SellListing(
        id=1,
        user_id=user_id,
        status=SellListingStatus.ACTIVE,
        deleted_at=None,
    )


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
    assert "security" not in operation


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
    assert "security" not in operation


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
    assert "security" not in operation


def test_create_trade_saves_trade_and_marks_sell_listing_sold() -> None:
    db = Mock(spec=Session)
    sell_listing = active_sell_listing()
    db.scalar.side_effect = [sell_listing, None]

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
    db.commit.assert_called_once()


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
    assert "security" not in operation


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
    assert "security" not in operation


def test_complete_trade_updates_trade_and_creates_certificate(monkeypatch) -> None:
    completed_time = datetime.fromisoformat("2026-08-10T18:43:00")
    monkeypatch.setattr(
        "app.services.market._kst_now_naive",
        lambda: completed_time,
    )
    db = Mock(spec=Session)
    trade, buyer = complete_trade_row()
    db.execute.return_value.first.return_value = trade, buyer

    def assign_certificate_id() -> None:
        certificate = db.add.call_args.args[0]
        certificate.id = 1

    db.flush.side_effect = assign_certificate_id

    response = complete_trade_request(db, trade_id=23)

    assert response.status_code == 200
    assert trade.status == TradeStatus.COMPLETED
    assert trade.completed_time == completed_time
    inserted = db.add.call_args.args[0]
    assert isinstance(inserted, DigitalCertificate)
    assert inserted.trade_id == 23
    assert inserted.network == "example_network"
    assert inserted.token_standard == "example_token_standard"
    assert inserted.token_id == "example_token_id"
    assert inserted.contract_address == "example_contract_address"
    assert inserted.tx_hash == "example_tx_hash"
    assert inserted.metadata_url == "example_metadata_url"
    assert response.json() == {
        "certificate": {
            "id": 1,
            "tradeId": 23,
            "ownerNickname": buyer.nickname,
            "completedTime": "2026-08-10T18:43:00",
            "network": "example_network",
            "tokenStandard": "example_token_standard",
            "tokenId": "example_token_id",
            "contractAddress": "example_contract_address",
            "txHash": "example_tx_hash",
            "metadataUrl": "example_metadata_url",
        }
    }
    db.commit.assert_called_once()


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
    assert "security" not in operation
