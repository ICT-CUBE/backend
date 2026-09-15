"""마켓 도메인 API 요청·응답 스키마."""

from datetime import date, datetime
from enum import StrEnum

from app.core.enums import SellListingStatus
from app.core.schemas import ApiSchema


class MarketProfileResponse(ApiSchema):
    profile_character_img_url: str | None
    avatar_nickname: str | None
    level: int
    level_name: str
    total_trade_count: int


class MarketProductItemResponse(ApiSchema):
    representative_cube_id: int
    market_product_id: int
    product_name: str
    artist_name: str
    product_image_url: str | None
    latest_trade_price: int | None


class MarketResponse(ApiSchema):
    profile: MarketProfileResponse
    products: list[MarketProductItemResponse]


class MarketSellListingItemResponse(ApiSchema):
    sell_listing_id: int
    product_name: str
    serial_number: str
    seller_nickname: str | None
    price: int
    like_count: int


class MarketSellListingsResponse(ApiSchema):
    sell_listings: list[MarketSellListingItemResponse]


class SellableCubeItemResponse(ApiSchema):
    cube_id: int
    market_product_id: int
    serial_number: str
    product_name: str
    artist_name: str
    product_image_url: str | None


class SellableCubesResponse(ApiSchema):
    cubes: list[SellableCubeItemResponse]


class SellListingCreateRequest(ApiSchema):
    market_product_id: int
    product_status: str | None = None
    title: str
    description: str
    price: int


class SellListingCreateResponse(ApiSchema):
    sell_listing_id: int


class SellListingDetailItemResponse(ApiSchema):
    sell_listing_id: int
    image_urls: list[str]
    seller_nickname: str | None
    seller_profile_image_url: str | None
    status: SellListingStatus
    is_mine: bool
    title: str
    description: str
    price: int
    created_at: datetime
    product_name: str
    serial_number: str


class SellListingDetailResponse(ApiSchema):
    sell_listing: SellListingDetailItemResponse


class TradeCreateRequest(ApiSchema):
    sell_listing_id: int
    buyer_address: str
    buyer_phone_number: str
    total_price: int
    paid_time: datetime


class TradeHistoryStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class TradeHistoryItemResponse(ApiSchema):
    id: int
    product_image_url: str | None
    product_name: str
    serial_number: str
    price: int
    paid_date: date
    status: TradeHistoryStatus


class TradeHistoryResponse(ApiSchema):
    trades: list[TradeHistoryItemResponse]


class TradeDetailCubeResponse(ApiSchema):
    id: int
    serial_number: str
    product_name: str
    artist_name: str


class TradeTimelineItemResponse(ApiSchema):
    status: str
    label: str
    time: datetime | None
    completed: bool


class TradeDetailItemResponse(ApiSchema):
    id: int
    paid_time: datetime | None
    price: int
    product_image_url: str | None
    cube: TradeDetailCubeResponse
    timeline: list[TradeTimelineItemResponse]


class TradeDetailResponse(ApiSchema):
    trade: TradeDetailItemResponse


class TradeCompleteCertificateResponse(ApiSchema):
    id: int
    trade_id: int
    owner_nickname: str | None
    completed_time: datetime
    network: str
    token_standard: str
    token_id: str
    contract_address: str
    tx_hash: str
    metadata_url: str


class TradeCompleteResponse(ApiSchema):
    certificate: TradeCompleteCertificateResponse
