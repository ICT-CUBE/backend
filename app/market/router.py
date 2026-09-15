"""마켓 도메인 API 라우터."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.core.schemas import ErrorResponse
from app.market.schemas import (
    MarketResponse,
    MarketSellListingsResponse,
    SellableCubesResponse,
    SellListingCreateRequest,
    SellListingCreateResponse,
    SellListingDetailResponse,
    TradeCompleteResponse,
    TradeCreateRequest,
    TradeDetailResponse,
    TradeHistoryResponse,
)
from app.market.service import (
    complete_trade,
    create_sell_listing,
    create_trade,
    delete_sell_listing,
    get_market,
    get_market_product_sell_listings,
    get_sell_listing_detail,
    get_sellable_cubes,
    get_trade_detail,
    get_trade_history,
    search_market_sell_listings,
)

router = APIRouter()


@router.get(
    "/market",
    response_model=MarketResponse,
    summary="마켓 조회",
    description=(
        "현재 사용자의 마켓 프로필과 제품명별 대표 마켓 상품 목록을 "
        "최근 체결가와 함께 조회합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "큐브 소유권 또는 친밀도 정보가 없음",
            "content": {
                "application/json": {
                    "examples": {
                        "cubeOwnershipNotFound": {
                            "summary": "큐브 소유권 없음",
                            "value": {
                                "code": "CUBE_OWNERSHIP_NOT_FOUND",
                                "message": "큐브 소유권 정보를 찾을 수 없습니다.",
                            },
                        },
                        "cubeAffinityNotFound": {
                            "summary": "큐브 친밀도 정보 없음",
                            "value": {
                                "code": "CUBE_AFFINITY_NOT_FOUND",
                                "message": "큐브 친밀도 정보를 찾을 수 없습니다.",
                            },
                        },
                    }
                }
            },
        },
    },
)
def read_market(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> MarketResponse:
    """GET /api/v1/users/me/market"""
    return get_market(db=db, current_user_id=current_user_id)


@router.get(
    "/market/products/{representativeCubeId}/sell-listings",
    response_model=MarketSellListingsResponse,
    summary="마켓 세부 상품 조회",
    description=(
        "대표 큐브와 제품명이 같은 시리얼 큐브를 판매 중인 판매글 전체를 "
        "판매글 id 내림차순으로 조회합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "대표 큐브 또는 마켓 상품이 없거나 조회할 수 없는 상태",
            "content": {
                "application/json": {
                    "example": {
                        "code": "MARKET_PRODUCT_NOT_FOUND",
                        "message": "마켓 제품 정보를 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def read_market_product_sell_listings(
    representative_cube_id: Annotated[
        int,
        Path(alias="representativeCubeId", ge=1),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> MarketSellListingsResponse:
    """GET /api/v1/users/me/market/products/{representativeCubeId}/sell-listings"""
    return get_market_product_sell_listings(
        db=db,
        current_user_id=current_user_id,
        representative_cube_id=representative_cube_id,
    )


@router.get(
    "/market/search",
    response_model=MarketSellListingsResponse,
    summary="마켓 검색 결과 조회",
    description=(
        "큐브 제품명 또는 아티스트명에 키워드가 포함된 마켓 상품의 판매 중인 판매글을 "
        "판매글 id 내림차순으로 조회합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "keyword가 없거나 공백만으로 이루어짐",
            "content": {
                "application/json": {
                    "example": {
                        "code": "INVALID_REQUEST",
                        "message": "요청값이 올바르지 않습니다.",
                    }
                }
            },
        },
    },
)
def search_market(
    keyword: Annotated[str, Query(min_length=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> MarketSellListingsResponse:
    """GET /api/v1/users/me/market/search"""
    return search_market_sell_listings(
        db=db,
        current_user_id=current_user_id,
        keyword=keyword,
    )


@router.get(
    "/sellable-cubes",
    response_model=SellableCubesResponse,
    summary="판매 가능한 내 큐브 조회",
    description="현재 사용자가 새 판매글을 등록할 수 있는 활성 큐브 목록을 조회합니다.",
)
def read_sellable_cubes(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> SellableCubesResponse:
    """GET /api/v1/users/me/sellable-cubes"""
    return get_sellable_cubes(db=db, current_user_id=current_user_id)


@router.post(
    "/sell-listings",
    response_model=SellListingCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="마켓 상품 판매 등록",
    description="현재 사용자의 판매 가능한 마켓 상품에 ACTIVE 판매글을 생성합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "현재 사용자가 판매할 수 있는 마켓 상품이 아님",
            "content": {
                "application/json": {
                    "example": {
                        "code": "MARKET_PRODUCT_NOT_FOUND",
                        "message": "마켓 제품 정보를 찾을 수 없습니다.",
                    }
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "동일한 마켓 상품의 ACTIVE 판매글이 이미 존재함",
            "content": {
                "application/json": {
                    "example": {
                        "code": "SELL_LISTING_ALREADY_ACTIVE",
                        "message": "이미 판매 중인 마켓 상품입니다.",
                    }
                }
            },
        },
    },
)
def create_market_sell_listing(
    body: SellListingCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> SellListingCreateResponse:
    """POST /api/v1/users/me/sell-listings"""
    return create_sell_listing(
        db=db,
        current_user_id=current_user_id,
        market_product_id=body.market_product_id,
        product_status=body.product_status,
        title=body.title,
        description=body.description,
        price=body.price,
    )


@router.get(
    "/sell-listings/{sellListingId}",
    response_model=SellListingDetailResponse,
    summary="판매글 상세 조회",
    description=(
        "삭제되지 않은 판매글의 상세 정보와 판매자·큐브 정보, "
        "등록된 이미지 전체를 조회합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "판매글이 존재하지 않거나 삭제됨",
            "content": {
                "application/json": {
                    "example": {
                        "code": "SELL_LISTING_NOT_FOUND",
                        "message": "판매 상품을 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def read_sell_listing_detail(
    sell_listing_id: Annotated[int, Path(alias="sellListingId", ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> SellListingDetailResponse:
    """GET /api/v1/users/me/sell-listings/{sellListingId}"""
    return get_sell_listing_detail(
        db=db,
        current_user_id=current_user_id,
        sell_listing_id=sell_listing_id,
    )


@router.delete(
    "/sell-listings/{sellListingId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="마켓 상품 판매 삭제",
    description="현재 사용자가 등록한 판매글을 소프트 딜리트합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "현재 사용자의 판매글이 존재하지 않거나 이미 삭제됨",
            "content": {
                "application/json": {
                    "example": {
                        "code": "SELL_LISTING_NOT_FOUND",
                        "message": "판매 상품을 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def delete_market_sell_listing(
    sell_listing_id: Annotated[int, Path(alias="sellListingId", ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> Response:
    """DELETE /api/v1/users/me/sell-listings/{sellListingId}"""
    delete_sell_listing(
        db=db,
        current_user_id=current_user_id,
        sell_listing_id=sell_listing_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/trades",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="거래 진행 정보 생성",
    description="현재 사용자를 구매자로 하여 판매 상품의 거래 진행 정보를 생성합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "판매 상품이 존재하지 않거나 거래 생성 가능한 상태가 아님",
            "content": {
                "application/json": {
                    "example": {
                        "code": "SELL_LISTING_INVALID",
                        "message": "판매 상품이 유효하지 않습니다.",
                    }
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "이미 거래가 존재하거나 자기 판매 상품 구매 시도",
            "content": {
                "application/json": {
                    "examples": {
                        "tradeAlreadyExists": {
                            "value": {
                                "code": "TRADE_ALREADY_EXISTS",
                                "message": "이미 거래가 생성된 판매 상품입니다.",
                            }
                        },
                        "selfTradeNotAllowed": {
                            "value": {
                                "code": "SELF_TRADE_NOT_ALLOWED",
                                "message": "자신이 등록한 판매 상품은 구매할 수 없습니다.",
                            }
                        },
                    }
                }
            },
        },
    },
)
def create_trade_progress(
    body: TradeCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> Response:
    """POST /api/v1/users/me/trades"""
    create_trade(db=db, current_user_id=current_user_id, body=body)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/trades",
    response_model=TradeHistoryResponse,
    summary="내 거래 내역 조회",
    description=(
        "현재 사용자가 구매자로 참여한 거래 내역을 결제 시각 내림차순으로 조회합니다."
    ),
)
def read_trade_history(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> TradeHistoryResponse:
    """GET /api/v1/users/me/trades"""
    return get_trade_history(db=db, current_user_id=current_user_id)


@router.get(
    "/trades/{tradeId}",
    response_model=TradeDetailResponse,
    summary="주문 상세 조회",
    description="현재 사용자가 구매자인 거래의 주문 상세 정보와 진행 타임라인을 조회합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "거래가 존재하지 않거나 현재 사용자가 구매자인 거래가 아님",
            "content": {
                "application/json": {
                    "example": {
                        "code": "TRADE_NOT_FOUND",
                        "message": "거래 정보를 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def read_trade_detail(
    trade_id: Annotated[int, Path(alias="tradeId")],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> TradeDetailResponse:
    """GET /api/v1/users/me/trades/{tradeId}"""
    return get_trade_detail(
        db=db,
        current_user_id=current_user_id,
        trade_id=trade_id,
    )


@router.patch(
    "/trades/{tradeId}/complete",
    response_model=TradeCompleteResponse,
    summary="구매 확정",
    description="배송 완료된 현재 사용자의 거래를 구매 확정합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "거래가 존재하지 않거나 현재 사용자가 구매자인 거래가 아님",
            "content": {
                "application/json": {
                    "example": {
                        "code": "TRADE_NOT_FOUND",
                        "message": "거래 정보를 찾을 수 없습니다.",
                    }
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "배송 완료 상태가 아니거나 NFT 이전을 마치지 못함",
            "content": {
                "application/json": {
                    "examples": {
                        "tradeNotDelivered": {
                            "summary": "배송 완료 상태가 아님",
                            "value": {
                                "code": "TRADE_NOT_DELIVERED",
                                "message": (
                                    "배송 완료 상태인 거래만 구매 확정할 수 있습니다."
                                ),
                            },
                        },
                        "tradeTransferRejected": {
                            "summary": "NFT 이전 요청이 거절됨",
                            "value": {
                                "code": "TRADE_TRANSFER_REJECTED",
                                "message": "NFT 이전 요청이 거절되었습니다.",
                            },
                        },
                        "tradeConfirmationTimeout": {
                            "summary": "제한 시간 안에 이전이 확정되지 않음",
                            "value": {
                                "code": "TRADE_CONFIRMATION_TIMEOUT",
                                "message": (
                                    "NFT 이전이 아직 확정되지 않았습니다. "
                                    "잠시 후 다시 확인해 주세요."
                                ),
                            },
                        },
                    }
                }
            },
        },
    },
)
def complete_trade_progress(
    trade_id: Annotated[int, Path(alias="tradeId")],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> TradeCompleteResponse:
    """PATCH /api/v1/users/me/trades/{tradeId}/complete"""
    return complete_trade(
        db=db,
        current_user_id=current_user_id,
        trade_id=trade_id,
    )
