"""마켓 거래 생성·조회·구매 확정과 NFT 이전 연동 로직."""

from datetime import datetime, timedelta, timezone
from typing import NoReturn

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.affinity.models import Affinity
from app.blockchain.errors import BlockchainError
from app.blockchain.models import BlockchainOperation
from app.blockchain.transfer import certificate_values, transfer_cube_nft
from app.core.config import get_settings
from app.core.enums import (
    BlockchainOperationStatus,
    BlockchainOperationType,
    CubeStatus,
    OwnershipStatus,
    SellListingStatus,
    TradeStatus,
)
from app.core.exceptions import ApiError
from app.core.search import LIKE_ESCAPE_CHARACTER, like_contains_pattern
from app.cube.models import Cube, CubeOwnership
from app.market.models import (
    DigitalCertificate,
    ListingMedia,
    SellingListLike,
    SellListing,
    Trade,
)
from app.market.schemas import (
    MarketProductItemResponse,
    MarketProfileResponse,
    MarketResponse,
    MarketSellListingItemResponse,
    MarketSellListingsResponse,
    SellableCubeItemResponse,
    SellableCubesResponse,
    SellListingCreateResponse,
    SellListingDetailItemResponse,
    SellListingDetailResponse,
    TradeCompleteCertificateResponse,
    TradeCompleteResponse,
    TradeCreateRequest,
    TradeDetailCubeResponse,
    TradeDetailItemResponse,
    TradeDetailResponse,
    TradeHistoryItemResponse,
    TradeHistoryResponse,
    TradeHistoryStatus,
    TradeTimelineItemResponse,
)
from app.user.models import User

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
    cubes = list(
        db.scalars(
            select(Cube)
            .where(
                Cube.deleted_at.is_(None),
                Cube.status != CubeStatus.DISABLED,
            )
            .order_by(Cube.id.asc())
        )
    )

    # 제품명 정규화 없이 그대로 비교하며, id 오름차순이라 먼저 나온 큐브가 대표입니다.
    representatives: dict[str, Cube] = {}
    for cube in cubes:
        representatives.setdefault(cube.product_name, cube)
    if not representatives:
        return []

    price_by_product_name = _get_latest_trade_price_by_product_name(db=db)
    return [
        MarketProductItemResponse(
            representative_cube_id=cube.id,
            # API의 마켓 상품 id는 큐브 id와 같습니다.
            market_product_id=cube.id,
            product_name=cube.product_name,
            artist_name=cube.artist_name,
            product_image_url=cube.product_image_url,
            latest_trade_price=price_by_product_name.get(cube.product_name),
        )
        for cube in representatives.values()
    ]


def _get_latest_trade_price_by_product_name(*, db: Session) -> dict[str, int]:
    """제품명별 가장 최근 체결 거래의 판매글 가격을 모읍니다."""
    rows = db.execute(
        select(Cube.product_name, SellListing.price)
        .select_from(Trade)
        .join(Trade.sell_listing)
        .join(SellListing.cube)
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

    rows = db.execute(
        _select_active_sell_listings().where(Cube.product_name == product_name)
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


def search_market_sell_listings(
    *,
    db: Session,
    current_user_id: int,
    keyword: str,
) -> MarketSellListingsResponse:
    """제품명 또는 아티스트명에 키워드가 포함된 큐브의 판매 중인 판매글을 조회합니다.

    판매자 본인 판매글도 제외하지 않으므로 `current_user_id`로 결과를 거르지 않습니다.
    """
    search_keyword = keyword.strip()
    if not search_keyword:
        raise ApiError(
            status_code=400,
            code="INVALID_REQUEST",
            message="요청값이 올바르지 않습니다.",
        )

    keyword_pattern = like_contains_pattern(search_keyword)
    rows = db.execute(
        _select_active_sell_listings().where(
            or_(
                Cube.product_name.like(keyword_pattern, escape=LIKE_ESCAPE_CHARACTER),
                Cube.artist_name.like(keyword_pattern, escape=LIKE_ESCAPE_CHARACTER),
            )
        )
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
        ]
    )


def _select_active_sell_listings() -> Select[tuple[SellListing, Cube, str | None, int]]:
    """판매 중인 판매글과 큐브·판매자 닉네임·좋아요 수를 함께 조회하는 select를 만듭니다."""
    like_count = (
        select(func.count(SellingListLike.id))
        .where(
            SellingListLike.selling_list_id == SellListing.id,
            SellingListLike.is_liked.is_(True),
        )
        .scalar_subquery()
    )
    return (
        select(SellListing, Cube, User.nickname, like_count)
        .join(Cube, Cube.id == SellListing.cube_id)
        .join(User, User.id == SellListing.user_id)
        .where(
            Cube.deleted_at.is_(None),
            Cube.status != CubeStatus.DISABLED,
            SellListing.status == SellListingStatus.ACTIVE,
            SellListing.deleted_at.is_(None),
        )
        .order_by(SellListing.id.desc())
    )


def get_sellable_cubes(
    *,
    db: Session,
    current_user_id: int,
) -> SellableCubesResponse:
    """현재 사용자가 새 판매글을 등록할 수 있는 활성 큐브를 반환합니다."""
    active_listing_exists = (
        select(SellListing.id)
        .where(
            SellListing.cube_id == Cube.id,
            SellListing.user_id == current_user_id,
            SellListing.status == SellListingStatus.ACTIVE,
            SellListing.deleted_at.is_(None),
        )
        .exists()
    )

    cubes = list(
        db.scalars(
            select(Cube)
            .join(CubeOwnership, CubeOwnership.cube_id == Cube.id)
            .where(
                CubeOwnership.user_id == current_user_id,
                CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
                Cube.deleted_at.is_(None),
                ~active_listing_exists,
            )
            .distinct()
            .order_by(Cube.id.asc())
        )
    )

    return SellableCubesResponse(
        cubes=[
            SellableCubeItemResponse(
                cube_id=cube.id,
                market_product_id=cube.id,
                serial_number=cube.serial_number,
                product_name=cube.product_name,
                artist_name=cube.artist_name,
                product_image_url=cube.product_image_url,
            )
            for cube in cubes
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
    """현재 사용자의 마켓 상품에 ACTIVE 판매글을 저장합니다.

    API의 마켓 상품 id는 큐브 id와 같으므로 `market_product_id`로 큐브를 조회합니다.
    """
    cube = db.scalar(
        select(Cube)
        .join(CubeOwnership, CubeOwnership.cube_id == Cube.id)
        .where(
            Cube.id == market_product_id,
            Cube.deleted_at.is_(None),
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
        )
        .limit(1)
        .with_for_update()
    )
    if cube is None:
        _raise_market_product_not_found()

    active_listing_id = db.scalar(
        select(SellListing.id)
        .where(
            SellListing.cube_id == cube.id,
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
        cube_id=cube.id,
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


def get_sell_listing_detail(
    *,
    db: Session,
    current_user_id: int,
    sell_listing_id: int,
) -> SellListingDetailResponse:
    """삭제되지 않은 판매글의 상세 정보와 등록된 이미지를 조회합니다.

    본인 판매글도 조회할 수 있으므로 `current_user_id`는 `isMine` 판단에만 씁니다.
    """
    row = db.execute(
        select(SellListing, User, Cube)
        .join(User, User.id == SellListing.user_id)
        .join(Cube, Cube.id == SellListing.cube_id)
        .where(
            SellListing.id == sell_listing_id,
            SellListing.status != SellListingStatus.DELETED,
            SellListing.deleted_at.is_(None),
        )
        .limit(1)
    ).first()
    if row is None:
        _raise_sell_listing_not_found()

    sell_listing, seller, cube = row
    image_urls = list(
        db.scalars(
            select(ListingMedia.image_url)
            .where(
                ListingMedia.sell_listing_id == sell_listing.id,
                ListingMedia.deleted_at.is_(None),
            )
            .order_by(ListingMedia.id.asc())
        )
    )

    return SellListingDetailResponse(
        sell_listing=SellListingDetailItemResponse(
            sell_listing_id=sell_listing.id,
            image_urls=image_urls,
            seller_nickname=seller.nickname,
            seller_profile_image_url=seller.profile_character_img_url,
            status=sell_listing.status,
            is_mine=sell_listing.user_id == current_user_id,
            title=sell_listing.title,
            description=sell_listing.description,
            price=sell_listing.price,
            created_at=sell_listing.created_at,
            product_name=cube.product_name,
            serial_number=cube.serial_number,
        )
    )


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

    cube = db.scalar(
        select(Cube)
        .where(Cube.id == sell_listing.cube_id)
        .limit(1)
        .with_for_update()
    )
    if cube is None:
        _raise_sell_listing_invalid()

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
    cube.status = CubeStatus.TRADE_PENDING

    try:
        db.add(trade)
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_trade_history(
    *,
    db: Session,
    current_user_id: int,
) -> TradeHistoryResponse:
    """현재 사용자가 구매자인 거래 내역을 결제 시각 내림차순으로 조회합니다."""
    rows = db.execute(
        select(Trade, SellListing.price, Cube)
        .join(
            SellListing,
            and_(
                SellListing.id == Trade.sell_listing_id,
                SellListing.deleted_at.is_(None),
            ),
        )
        .join(
            Cube,
            and_(
                Cube.id == SellListing.cube_id,
                Cube.deleted_at.is_(None),
            ),
        )
        .where(Trade.buyer_user_id == current_user_id)
        .order_by(Trade.paid_time.desc(), Trade.id.desc())
    ).all()

    return TradeHistoryResponse(
        trades=[
            TradeHistoryItemResponse(
                id=trade.id,
                product_image_url=cube.product_image_url,
                product_name=cube.product_name,
                serial_number=cube.serial_number,
                price=price,
                paid_date=trade.paid_time.date(),
                status=_trade_history_status(trade.status),
            )
            for trade, price, cube in rows
        ]
    )


def _trade_history_status(trade_status: TradeStatus) -> TradeHistoryStatus:
    """거래 상태를 거래 내역 화면에 표시할 진행 상태로 변환합니다."""
    if trade_status == TradeStatus.COMPLETED:
        return TradeHistoryStatus.COMPLETED
    return TradeHistoryStatus.IN_PROGRESS


def get_trade_detail(
    *,
    db: Session,
    current_user_id: int,
    trade_id: int,
) -> TradeDetailResponse:
    """현재 사용자가 구매자인 거래의 주문 상세 정보를 반환합니다."""
    row = db.execute(
        select(Trade, SellListing, Cube)
        .join(SellListing, Trade.sell_listing_id == SellListing.id)
        .join(Cube, SellListing.cube_id == Cube.id)
        .where(
            Trade.id == trade_id,
            Trade.buyer_user_id == current_user_id,
        )
        .limit(1)
    ).first()
    if row is None:
        _raise_trade_not_found()

    trade, sell_listing, cube = row

    return TradeDetailResponse(
        trade=TradeDetailItemResponse(
            id=trade.id,
            paid_time=trade.paid_time,
            price=sell_listing.price,
            product_image_url=cube.product_image_url,
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
        _raise_trade_not_delivered()

    transfer_target = _get_transfer_target(db=db, trade=trade)
    # NFT 이전은 수십 초가 걸릴 수 있어 거래 행 잠금을 먼저 풉니다.
    db.rollback()

    certificate_values = _transfer_traded_nft(
        db=db,
        trade_id=trade_id,
        buyer_user_id=current_user_id,
        transfer_target=transfer_target,
    )

    # 외부 호출 동안 다른 요청이 먼저 확정했을 수 있어 상태를 다시 확인합니다.
    if trade.status != TradeStatus.DELIVERED:
        _raise_trade_not_delivered()

    completed_time = _kst_now_naive()
    certificate = DigitalCertificate(
        trade_id=trade.id,
        network=get_settings().blockchain_network,
        **certificate_values,
    )
    trade.status = TradeStatus.COMPLETED
    trade.completed_time = completed_time
    _release_traded_cube(db=db, trade=trade)

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


def _get_transfer_target(*, db: Session, trade: Trade) -> tuple[int, str]:
    """거래에 연결된 판매자 id와 큐브 시리얼 번호를 조회합니다."""
    row = db.execute(
        select(SellListing.user_id, Cube.serial_number)
        .join(Cube, Cube.id == SellListing.cube_id)
        .where(SellListing.id == trade.sell_listing_id)
        .limit(1)
    ).first()
    if row is None:
        _raise_trade_not_found()
    seller_user_id, serial_number = row
    return seller_user_id, serial_number


def _release_traded_cube(*, db: Session, trade: Trade) -> None:
    """구매 확정된 거래의 큐브를 거래 대기에서 보유 상태로 되돌립니다."""
    cube = db.scalar(
        select(Cube)
        .join(SellListing, SellListing.cube_id == Cube.id)
        .where(SellListing.id == trade.sell_listing_id)
        .limit(1)
        .with_for_update()
    )
    if cube is None:
        _raise_trade_not_found()

    # 비활성화 등 거래와 무관하게 바뀐 상태는 덮어쓰지 않습니다.
    if cube.status == CubeStatus.TRADE_PENDING:
        cube.status = CubeStatus.OWNED


def _transfer_traded_nft(
    *,
    db: Session,
    trade_id: int,
    buyer_user_id: int,
    transfer_target: tuple[int, str],
) -> dict[str, str]:
    """NFT 이전을 요청하고 실패를 구매 확정 오류로 변환합니다."""
    confirmed = _get_transfer_operation(
        db=db,
        trade_id=trade_id,
        status=BlockchainOperationStatus.CONFIRMED,
    )
    if confirmed is not None:
        # 확정 대기가 시간을 넘긴 뒤 완료 알림으로 확정된 경우 다시 이전하지 않습니다.
        return certificate_values(
            token_id=confirmed.token_id,
            tx_hash=confirmed.tx_hash,
        )

    requested = _get_transfer_operation(
        db=db,
        trade_id=trade_id,
        status=BlockchainOperationStatus.REQUESTED,
    )
    if requested is not None:
        # 확정 대기 중 같은 거래가 다시 요청되면 이전을 중복 접수하지 않습니다.
        _raise_confirmation_pending()

    seller_user_id, serial_number = transfer_target
    try:
        return transfer_cube_nft(
            db=db,
            trade_id=trade_id,
            seller_user_id=seller_user_id,
            buyer_user_id=buyer_user_id,
            serial_number=serial_number,
        )
    except BlockchainError as exc:
        if exc.code == "CONFIRMATION_TIMEOUT":
            _raise_confirmation_pending(cause=exc)
        if exc.code == "BLOCKCHAIN_UNREACHABLE":
            raise ApiError(
                status_code=500,
                code="INTERNAL_SERVER_ERROR",
                message="서버 내부 오류가 발생했습니다.",
            ) from exc
        raise ApiError(
            status_code=409,
            code="TRADE_TRANSFER_REJECTED",
            message="NFT 이전 요청이 거절되었습니다.",
        ) from exc


def _get_transfer_operation(
    *,
    db: Session,
    trade_id: int,
    status: BlockchainOperationStatus,
) -> BlockchainOperation | None:
    """거래의 NFT 이전 작업을 상태별로 조회합니다."""
    return db.scalar(
        select(BlockchainOperation)
        .where(
            BlockchainOperation.trade_id == trade_id,
            BlockchainOperation.operation_type == BlockchainOperationType.TRANSFER,
            BlockchainOperation.status == status,
        )
        .limit(1)
    )


def _raise_confirmation_pending(*, cause: Exception | None = None) -> NoReturn:
    raise ApiError(
        status_code=409,
        code="TRADE_CONFIRMATION_TIMEOUT",
        message="NFT 이전이 아직 확정되지 않았습니다. 잠시 후 다시 확인해 주세요.",
    ) from cause


def _raise_trade_not_delivered() -> NoReturn:
    raise ApiError(
        status_code=409,
        code="TRADE_NOT_DELIVERED",
        message="배송 완료 상태인 거래만 구매 확정할 수 있습니다.",
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
