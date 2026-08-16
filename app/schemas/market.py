"""마켓 도메인 API 요청·응답 스키마."""

from datetime import datetime

from pydantic import field_validator

from app.schemas.base import ApiSchema


class TradeCreateRequest(ApiSchema):
    sell_listing_id: int
    buyer_address: str
    buyer_phone_number: str
    total_price: int
    paid_time: datetime

    @field_validator("paid_time")
    @classmethod
    def validate_paid_time_is_naive(cls, value: datetime) -> datetime:
        if value.tzinfo is not None:
            raise ValueError("paid_time must be naive datetime")
        return value


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
