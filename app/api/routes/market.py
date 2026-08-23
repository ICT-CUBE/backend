"""마켓 도메인 API 라우터."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.schemas.common import ErrorResponse
from app.schemas.market import (
    SellableCubesResponse,
    TradeCompleteResponse,
    TradeCreateRequest,
    TradeDetailResponse,
)
from app.services.market import (
    complete_trade,
    create_trade,
    get_sellable_cubes,
    get_trade_detail,
)

router = APIRouter()


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
            "description": "거래가 배송 완료 상태가 아니라 구매 확정할 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "TRADE_NOT_DELIVERED",
                        "message": "배송 완료 상태인 거래만 구매 확정할 수 있습니다.",
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
