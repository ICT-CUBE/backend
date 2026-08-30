"""블록체인 연동 도메인 API 요청·응답 스키마."""

from datetime import datetime

from app.schemas.base import ApiSchema


class BlockchainNotificationRequest(ApiSchema):
    notification_id: str
    operation_id: str
    idempotency_key: str
    operation_type: str
    token_id: int
    final_status: str
    final_owner_address: str
    tx_hash: str
    block_number: int
    block_hash: str
    confirmations: int
    service_rights_state: str | None = None
    confirmed_at: datetime


class BlockchainNotificationResponse(ApiSchema):
    notification_id: str
    accepted: bool
    duplicate: bool
