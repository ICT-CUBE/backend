"""마켓 거래 생성·조회·구매 확정 로직."""

from datetime import datetime
from typing import NoReturn
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ApiError
from app.models.cube import Cube
from app.models.enums import SellListingStatus, TradeStatus
from app.models.market import DigitalCertificate, MarketProduct, SellListing, Trade
from app.models.user import User
from app.schemas.market import (
    TradeCompleteCertificateResponse,
    TradeCompleteResponse,
    TradeCreateRequest,
    TradeDetailCubeResponse,
    TradeDetailItemResponse,
    TradeDetailResponse,
    TradeTimelineItemResponse,
)

TRADE_TIMELINE_LABELS = {
    TradeStatus.PAID: "결제 완료",
    TradeStatus.SENT: "판매자 발송",
    TradeStatus.SHIPPING: "배송 중",
    TradeStatus.DELIVERED: "배송 완료",
    TradeStatus.COMPLETED: "구매 확정",
}


def create_trade(
    *,
    db: Session,
    current_user_id: int,
    body: TradeCreateRequest,
) -> None:
    """판매글을 결제 완료 상태의 거래로 전환합니다."""
    sell_listing = db.scalar(
        select(SellListing)
        .where(
            SellListing.id == body.sell_listing_id,
            SellListing.deleted_at.is_(None),
        )
        .limit(1)
        .with_for_update()
    )
    if sell_listing is None:
        _raise_sell_listing_invalid()

    existing_trade_id = db.scalar(
        select(Trade.id)
        .where(Trade.sell_listing_id == sell_listing.id)
        .limit(1)
    )
    if existing_trade_id is not None:
        db.rollback()
        raise ApiError(
            status_code=409,
            code="TRADE_ALREADY_EXISTS",
            message="이미 거래가 생성된 판매 상품입니다.",
        )

    if sell_listing.status != SellListingStatus.ACTIVE:
        _raise_sell_listing_invalid()

    if sell_listing.user_id == current_user_id:
        db.rollback()
        raise ApiError(
            status_code=409,
            code="SELF_TRADE_NOT_ALLOWED",
            message="자신이 등록한 판매 상품은 구매할 수 없습니다.",
        )

    trade = Trade(
        sell_listing_id=sell_listing.id,
        buyer_user_id=current_user_id,
        buyer_phone_number=body.buyer_phone_number,
        buyer_address=body.buyer_address,
        total_price=body.total_price,
        paid_time=body.paid_time,
        sent_time=None,
        shipped_time=None,
        delivered_time=None,
        completed_time=None,
        status=TradeStatus.PAID,
    )
    sell_listing.status = SellListingStatus.SOLD

    try:
        db.add(trade)
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_trade_detail(
    *,
    db: Session,
    current_user_id: int,
    trade_id: int,
) -> TradeDetailResponse:
    """현재 사용자가 구매자인 거래의 주문 상세 정보를 반환합니다."""
    row = db.execute(
        select(Trade, SellListing, MarketProduct, Cube)
        .join(SellListing, Trade.sell_listing_id == SellListing.id)
        .join(MarketProduct, SellListing.market_product_id == MarketProduct.id)
        .join(Cube, MarketProduct.cube_id == Cube.id)
        .where(
            Trade.id == trade_id,
            Trade.buyer_user_id == current_user_id,
        )
        .limit(1)
    ).first()
    if row is None:
        _raise_trade_not_found()

    trade, sell_listing, market_product, cube = row

    return TradeDetailResponse(
        trade=TradeDetailItemResponse(
            id=trade.id,
            paid_time=trade.paid_time,
            price=sell_listing.price,
            product_image_url=market_product.product_image_url,
            cube=TradeDetailCubeResponse(
                id=cube.id,
                serial_number=cube.serial_number,
                product_name=cube.product_name,
                artist_name=cube.artist_name,
            ),
            timeline=_trade_timeline(trade),
        )
    )


def complete_trade(
    *,
    db: Session,
    current_user_id: int,
    trade_id: int,
) -> TradeCompleteResponse:
    """배송 완료된 현재 사용자의 거래를 구매 확정 처리합니다."""
    row = db.execute(
        select(Trade, User)
        .join(User, Trade.buyer_user_id == User.id)
        .where(
            Trade.id == trade_id,
            Trade.buyer_user_id == current_user_id,
        )
        .limit(1)
        .with_for_update()
    ).first()
    if row is None:
        _raise_trade_not_found()

    trade, buyer = row
    if trade.status != TradeStatus.DELIVERED:
        raise ApiError(
            status_code=409,
            code="TRADE_NOT_DELIVERED",
            message="배송 완료 상태인 거래만 구매 확정할 수 있습니다.",
        )

    completed_time = _kst_now_naive()
    certificate = _build_example_certificate(trade_id=trade.id)
    trade.status = TradeStatus.COMPLETED
    trade.completed_time = completed_time

    try:
        db.add(certificate)
        db.flush()
        db.commit()
    except Exception:
        db.rollback()
        raise

    return TradeCompleteResponse(
        certificate=TradeCompleteCertificateResponse(
            id=certificate.id,
            trade_id=trade.id,
            owner_nickname=buyer.nickname,
            completed_time=completed_time,
            network=certificate.network,
            token_standard=certificate.token_standard,
            token_id=certificate.token_id,
            contract_address=certificate.contract_address,
            tx_hash=certificate.tx_hash,
            metadata_url=certificate.metadata_url,
        )
    )


def _raise_sell_listing_invalid() -> NoReturn:
    raise ApiError(
        status_code=404,
        code="SELL_LISTING_INVALID",
        message="판매 상품이 유효하지 않습니다.",
    )


def _raise_trade_not_found() -> NoReturn:
    raise ApiError(
        status_code=404,
        code="TRADE_NOT_FOUND",
        message="거래 정보를 찾을 수 없습니다.",
    )


def _kst_now_naive() -> datetime:
    """DB 저장 정책에 맞춰 한국시간 기준 timezone 없는 datetime을 반환합니다."""
    return datetime.now(ZoneInfo("Asia/Seoul")).replace(tzinfo=None, microsecond=0)


def _build_example_certificate(*, trade_id: int) -> DigitalCertificate:
    """블록체인 연동 전까지 DB NOT NULL 컬럼을 채우기 위한 임시 예시값을 만듭니다."""
    return DigitalCertificate(
        trade_id=trade_id,
        # 실제 블록체인 네트워크 값이 아니며, 연동 시 실제 값으로 교체해야 합니다.
        network="example_network",
        # 실제 토큰 표준 값이 아니며, 연동 시 실제 값으로 교체해야 합니다.
        token_standard="example_token_standard",
        # 실제 토큰 id가 아니며, 연동 시 실제 값으로 교체해야 합니다.
        token_id="example_token_id",
        # 실제 컨트랙트 주소가 아니며, 연동 시 실제 값으로 교체해야 합니다.
        contract_address="example_contract_address",
        # 실제 트랜잭션 해시가 아니며, 연동 시 실제 값으로 교체해야 합니다.
        tx_hash="example_tx_hash",
        # 실제 메타데이터 URL이 아니며, 연동 시 실제 값으로 교체해야 합니다.
        metadata_url="example_metadata_url",
    )


def _trade_timeline(trade: Trade) -> list[TradeTimelineItemResponse]:
    timeline_times = {
        TradeStatus.PAID: trade.paid_time,
        TradeStatus.SENT: trade.sent_time,
        TradeStatus.SHIPPING: trade.shipped_time,
        TradeStatus.DELIVERED: trade.delivered_time,
        TradeStatus.COMPLETED: trade.completed_time,
    }
    return [
        TradeTimelineItemResponse(
            status=status.value,
            label=TRADE_TIMELINE_LABELS[status],
            time=time,
            completed=time is not None,
        )
        for status, time in timeline_times.items()
    ]
