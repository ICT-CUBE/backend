"""블록체인 연동 도메인 API 라우터."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.concurrency import run_in_threadpool
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.blockchain.notifications import record_notification
from app.blockchain.schemas import (
    BlockchainNotificationRequest,
    BlockchainNotificationResponse,
)
from app.blockchain.signing import verify_webhook_signature
from app.core.database import get_db
from app.core.exceptions import ApiError
from app.core.schemas import ErrorResponse

router = APIRouter()

NOTIFICATION_PATH = "/notifications"


@router.post(
    NOTIFICATION_PATH,
    response_model=BlockchainNotificationResponse,
    summary="블록체인 완료 알림 수신",
    description=(
        "블록체인 서버가 온체인 확정 후 보내는 완료 알림을 받습니다. "
        "사용자 Access Token이 아니라 outbound HMAC 서명으로 검증합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "알림 본문 형식이 올바르지 않음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "INVALID_REQUEST",
                        "message": "요청값이 올바르지 않습니다.",
                    }
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "HMAC 서명이 없거나 유효하지 않음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "INVALID_WEBHOOK_SIGNATURE",
                        "message": "유효하지 않은 webhook 서명입니다.",
                    }
                }
            },
        },
    },
)
async def receive_blockchain_notification(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> BlockchainNotificationResponse:
    """POST /api/v1/internal/blockchain/notifications"""
    # 서명 대상이 전송된 raw body라 파싱 전 원본 바이트가 필요합니다.
    body = await request.body()
    if not verify_webhook_signature(
        method=request.method,
        path=request.url.path,
        headers=dict(request.headers),
        body=body,
        query=dict(request.query_params),
    ):
        raise ApiError(
            status_code=401,
            code="INVALID_WEBHOOK_SIGNATURE",
            message="유효하지 않은 webhook 서명입니다.",
        )

    notification = _parse_notification(body)
    return await run_in_threadpool(
        record_notification,
        db=db,
        notification=notification,
    )


def _parse_notification(body: bytes) -> BlockchainNotificationRequest:
    """알림 본문을 검증하고 실패하면 공통 400으로 바꿉니다."""
    try:
        return BlockchainNotificationRequest.model_validate(json.loads(body))
    except (ValidationError, ValueError) as exc:
        raise ApiError(
            status_code=400,
            code="INVALID_REQUEST",
            message="요청값이 올바르지 않습니다.",
        ) from exc
