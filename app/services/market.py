"""마켓 거래 생성·조회·구매 확정 로직."""

from datetime import datetime, timedelta, timezone
from typing import NoReturn

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, aliased, joinedload

from app.core.exceptions import ApiError
from app.models.cube import Affinity, Cube, CubeOwnership
from app.models.enums import (
    CubeStatus,
    OwnershipStatus,
    SellListingStatus,
    TradeStatus,
)
from app.models.market import (
    DigitalCertificate,
    MarketProduct,
    SellingListLike,
    SellListing,
    Trade,
)
from app.models.user import User
from app.schemas.market import (
    MarketProductItemResponse,
    MarketProfileResponse,
    MarketResponse,
    MarketSellListingItemResponse,
    MarketSellListingsResponse,
    SellableCubeItemResponse,
    SellableCubesResponse,
    SellListingCreateResponse,
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
KOREA_TIMEZONE = timezone(timedelta(hours=9))
# 결제가 완료된 이후의 모든 거래 상태를 체결된 거래로 봅니다.
SETTLED_TRADE_STATUSES = (
    TradeStatus.PAID,
    TradeStatus.SENT,
    TradeStatus.SHIPPING,
    TradeStatus.DELIVERED,
    TradeStatus.COMPLETED,
)


def get_market(*, db: Session, current_user_id: int) -> MarketResponse:
    """현재 사용자의 마켓 홈 프로필과 제품명별 대표 상품 목록을 조회합니다."""
    cube_ownership = db.scalar(
        select(CubeOwnership)
        .where(
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .options(
            joinedload(CubeOwnership.user),
            joinedload(CubeOwnership.affinity).joinedload(Affinity.level_info),
        )
        .limit(1)
    )
    if cube_ownership is None:
        raise ApiError(
            status_code=404,
            code="CUBE_OWNERSHIP_NOT_FOUND",
            message="큐브 소유권 정보를 찾을 수 없습니다.",
        )

    affinity = cube_ownership.affinity
    if affinity is None:
        raise ApiError(
            status_code=404,
            code="CUBE_AFFINITY_NOT_FOUND",
            message="큐브 친밀도 정보를 찾을 수 없습니다.",
        )

    level = affinity.level_info
    return MarketResponse(
        profile=MarketProfileResponse(
            profile_character_img_url=cube_ownership.user.profile_character_img_url,
            avatar_nickname=cube_ownership.avatar_nickname,
            level=level.level,
            level_name=level.level_name.value,
            total_trade_count=_get_total_trade_count(
                db=db,
                current_user_id=current_user_id,
            ),
        ),
        products=_get_representative_products(db=db),
    )


def _get_total_trade_count(*, db: Session, current_user_id: int) -> int:
    """현재 사용자가 구매자 또는 판매자로 참여한 구매 확정 거래 수를 셉니다."""
    total_trade_count = db.scalar(
        select(func.count(Trade.id))
        .join(Trade.sell_listing)
        .where(
            Trade.status == TradeStatus.COMPLETED,
            or_(
                Trade.buyer_user_id == current_user_id,
                SellListing.user_id == current_user_id,
            ),
        )
    )
    return int(total_trade_count or 0)


def _get_representative_products(*, db: Session) -> list[MarketProductItemResponse]:
    """제품명이 같은 큐브를 묶고 id가 가장 작은 큐브를 대표로 반환합니다."""
    rows = db.execute(
        select(Cube, MarketProduct)
        .join(
            MarketProduct,
            and_(
                MarketProduct.cube_id == Cube.id,
                MarketProduct.deleted_at.is_(None),
            ),
        )
        .where(
            Cube.deleted_at.is_(None),
            Cube.status != CubeStatus.DISABLED,
        )
        .order_by(Cube.id.asc())
    ).all()

    # 제품명 정규화 없이 그대로 비교하며, id 오름차순이라 먼저 나온 큐브가 대표입니다.
    representatives: dict[str, tuple[Cube, MarketProduct]] = {}
    for cube, market_product in rows:
        representatives.setdefault(cube.product_name, (cube, market_product))
    if not representatives:
        return []

    price_by_product_name = _get_latest_trade_price_by_product_name(db=db)
    return [
        MarketProductItemResponse(
            representative_cube_id=cube.id,
            market_product_id=market_product.id,
            product_name=cube.product_name,
            artist_name=cube.artist_name,
            product_image_url=market_product.product_image_url,
            latest_trade_price=price_by_product_name.get(cube.product_name),
        )
        for cube, market_product in representatives.values()
    ]


def _get_latest_trade_price_by_product_name(*, db: Session) -> dict[str, int]:
    """제품명별 가장 최근 체결 거래의 판매글 가격을 모읍니다."""
    rows = db.execute(
        select(Cube.product_name, SellListing.price)
        .select_from(Trade)
        .join(Trade.sell_listing)
        .join(SellListing.market_product)
        .join(MarketProduct.cube)
        .where(Trade.status.in_(SETTLED_TRADE_STATUSES))
        .order_by(Trade.paid_time.desc(), Trade.id.desc())
    ).all()

    # 최근 순으로 정렬되어 있으므로 제품명마다 처음 만난 거래가 최근 체결 거래입니다.
    latest_price_by_product_name: dict[str, int] = {}
    for product_name, price in rows:
        latest_price_by_product_name.setdefault(product_name, price)
    return latest_price_by_product_name


def get_market_product_sell_listings(
    *,
    db: Session,
    current_user_id: int,
    representative_cube_id: int,
) -> MarketSellListingsResponse:
    """대표 큐브와 제품명이 같은 시리얼 큐브의 판매 중인 판매글을 조회합니다.

    판매자 본인 판매글도 제외하지 않으므로 `current_user_id`로 결과를 거르지 않습니다.
    """
    product_name = db.scalar(
        select(Cube.product_name)
        .join(
            MarketProduct,
            and_(
                MarketProduct.cube_id == Cube.id,
                MarketProduct.deleted_at.is_(None),
            ),
        )
        .where(
            Cube.id == representative_cube_id,
            Cube.deleted_at.is_(None),
            Cube.status != CubeStatus.DISABLED,
        )
        .limit(1)
    )
    if product_name is None:
        raise ApiError(
            status_code=404,
            code="MARKET_PRODUCT_NOT_FOUND",
            message="마켓 제품 정보를 찾을 수 없습니다.",
        )

    like_count = (
        select(func.count(SellingListLike.id))
        .where(
            SellingListLike.selling_list_id == SellListing.id,
            SellingListLike.is_liked.is_(True),
        )
        .scalar_subquery()
    )
    rows = db.execute(
        select(SellListing, Cube, User.nickname, like_count)
        .join(
            MarketProduct,
            and_(
                MarketProduct.id == SellListing.market_product_id,
                MarketProduct.deleted_at.is_(None),
            ),
        )
        .join(Cube, Cube.id == MarketProduct.cube_id)
        .join(User, User.id == SellListing.user_id)
        .where(
            Cube.product_name == product_name,
            Cube.deleted_at.is_(None),
            Cube.status != CubeStatus.DISABLED,
            SellListing.status == SellListingStatus.ACTIVE,
            SellListing.deleted_at.is_(None),
        )
        .order_by(SellListing.id.desc())
    ).all()

    return MarketSellListingsResponse(
        sell_listings=[
            MarketSellListingItemResponse(
                sell_listing_id=sell_listing.id,
                product_name=cube.product_name,
                serial_number=cube.serial_number,
                seller_nickname=seller_nickname,
                price=sell_listing.price,
                like_count=like_count_value,
            )
            for sell_listing, cube, seller_nickname, like_count_value in rows
            # DB 콜레이션이 대소문자를 구분하지 않으므로 제품명을 한 번 더 정확히 비교합니다.
            if cube.product_name == product_name
        ]
    )


def get_sellable_cubes(
    *,
    db: Session,
    current_user_id: int,
) -> SellableCubesResponse:
    """현재 사용자가 새 판매글을 등록할 수 있는 활성 큐브를 반환합니다."""
    listed_market_product = aliased(MarketProduct)
    active_listing_exists = (
        select(SellListing.id)
        .join(
            listed_market_product,
            SellListing.market_product_id == listed_market_product.id,
        )
        .where(
            listed_market_product.cube_id == Cube.id,
            SellListing.user_id == current_user_id,
            SellListing.status == SellListingStatus.ACTIVE,
            SellListing.deleted_at.is_(None),
        )
        .exists()
    )

    rows = db.execute(
        select(Cube, MarketProduct)
        .join(CubeOwnership, CubeOwnership.cube_id == Cube.id)
        .join(
            MarketProduct,
            and_(
                MarketProduct.cube_id == Cube.id,
                MarketProduct.deleted_at.is_(None),
            ),
        )
        .where(
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            Cube.deleted_at.is_(None),
            ~active_listing_exists,
        )
        .distinct()
        .order_by(Cube.id.asc())
    ).all()

    return SellableCubesResponse(
        cubes=[
            SellableCubeItemResponse(
                cube_id=cube.id,
                market_product_id=market_product.id,
                serial_number=cube.serial_number,
                product_name=cube.product_name,
                artist_name=cube.artist_name,
                product_image_url=market_product.product_image_url,
            )
            for cube, market_product in rows
        ]
    )


def create_sell_listing(
    *,
    db: Session,
    current_user_id: int,
    market_product_id: int,
    product_status: str | None,
    title: str,
    description: str,
    price: int,
) -> SellListingCreateResponse:
    """현재 사용자의 마켓 상품에 ACTIVE 판매글을 저장합니다."""
    market_product = db.scalar(
        select(MarketProduct)
        .join(Cube, MarketProduct.cube_id == Cube.id)
        .join(CubeOwnership, CubeOwnership.cube_id == Cube.id)
        .where(
            MarketProduct.id == market_product_id,
            MarketProduct.deleted_at.is_(None),
            Cube.deleted_at.is_(None),
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
        )
        .limit(1)
        .with_for_update()
    )
    if market_product is None:
        _raise_market_product_not_found()

    active_listing_id = db.scalar(
        select(SellListing.id)
        .where(
            SellListing.market_product_id == market_product.id,
            SellListing.status == SellListingStatus.ACTIVE,
            SellListing.deleted_at.is_(None),
        )
        .limit(1)
    )
    if active_listing_id is not None:
        db.rollback()
        raise ApiError(
            status_code=409,
            code="SELL_LISTING_ALREADY_ACTIVE",
            message="이미 판매 중인 마켓 상품입니다.",
        )

    sell_listing = SellListing(
        market_product_id=market_product.id,
        user_id=current_user_id,
        product_status=product_status,
        title=title,
        description=description,
        price=price,
        status=SellListingStatus.ACTIVE,
        deleted_at=None,
    )
    try:
        db.add(sell_listing)
        db.flush()
        sell_listing_id = sell_listing.id
        db.commit()
    except Exception:
        db.rollback()
        raise

    return SellListingCreateResponse(sell_listing_id=sell_listing_id)


def delete_sell_listing(
    *,
    db: Session,
    current_user_id: int,
    sell_listing_id: int,
) -> None:
    """현재 사용자가 등록한 판매글을 소프트 딜리트합니다."""
    sell_listing = db.scalar(
        select(SellListing)
        .where(
            SellListing.id == sell_listing_id,
            SellListing.user_id == current_user_id,
            SellListing.status != SellListingStatus.DELETED,
            SellListing.deleted_at.is_(None),
        )
        .limit(1)
        .with_for_update()
    )
    if sell_listing is None:
        _raise_sell_listing_not_found()

    sell_listing.status = SellListingStatus.DELETED
    sell_listing.deleted_at = _kst_now_naive()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


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


def _raise_market_product_not_found() -> NoReturn:
    raise ApiError(
        status_code=404,
        code="MARKET_PRODUCT_NOT_FOUND",
        message="마켓 제품 정보를 찾을 수 없습니다.",
    )


def _raise_sell_listing_not_found() -> NoReturn:
    raise ApiError(
        status_code=404,
        code="SELL_LISTING_NOT_FOUND",
        message="판매 상품을 찾을 수 없습니다.",
    )


def _raise_trade_not_found() -> NoReturn:
    raise ApiError(
        status_code=404,
        code="TRADE_NOT_FOUND",
        message="거래 정보를 찾을 수 없습니다.",
    )


def _kst_now_naive() -> datetime:
    """DB 저장 정책에 맞춰 한국시간 기준 timezone 없는 datetime을 반환합니다."""
    return datetime.now(KOREA_TIMEZONE).replace(tzinfo=None, microsecond=0)


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
