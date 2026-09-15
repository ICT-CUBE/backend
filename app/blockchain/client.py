"""블록체인 서버 API 호출과 확정 대기."""

import json
import time
from typing import Any

import httpx

from app.blockchain.errors import BlockchainError
from app.blockchain.signing import build_signature_headers, issue_approval_token
from app.core.config import get_settings

# 온체인 확정으로 인정하는 작업 상태입니다.
CONFIRMED_STATUSES = ("ONCHAIN_CONFIRMED", "COMPLETED")
# 더 기다려도 소용이 없는 작업 상태입니다.
FAILED_STATUSES = ("FAILED", "REVIEW_REQUIRED", "CANCELLED")
# 메타데이터의 고정 필드입니다. 블록체인 팀과 합의한 값입니다.
PUBLIC_GRADE = "UNSPECIFIED"
BENEFIT_REFERENCE_ID = "NONE"


def ensure_wallet(*, user_id: int) -> str:
    """사용자의 수탁 지갑 주소를 확보합니다. 없으면 새로 만들어 줍니다."""
    wallet = _request(
        method="POST",
        path="/internal/v1/wallets",
        body={"userId": str(user_id)},
    )
    return str(wallet["address"])


def prepare_metadata(
    *,
    token_id: int,
    cube_number: str,
    image_base64: str,
    image_mime_type: str,
) -> bool:
    """NFT 메타데이터를 준비하고 사용 가능(ready) 여부를 반환합니다."""
    metadata = _request(
        method="POST",
        path="/internal/v1/metadata",
        body={
            "tokenId": token_id,
            "cubeNumber": cube_number,
            "publicGrade": PUBLIC_GRADE,
            "imageBase64": image_base64,
            "imageMimeType": image_mime_type,
            "benefitReferenceId": BENEFIT_REFERENCE_ID,
        },
    )
    return bool(metadata["ready"])


def get_metadata_status(*, token_id: int) -> bool:
    """준비된 메타데이터의 사용 가능 여부를 다시 확인합니다."""
    metadata = _request(
        method="GET",
        path=f"/internal/v1/metadata/{token_id}",
    )
    return bool(metadata["ready"])


def request_mint(
    *,
    idempotency_key: str,
    user_id: int,
    cube_id: int,
    token_id: int,
    to_address: str,
) -> str:
    """Mint 작업을 접수하고 작업 id를 반환합니다."""
    accepted = _request(
        method="POST",
        path="/internal/v1/mints",
        body={
            "idempotencyKey": idempotency_key,
            "userId": str(user_id),
            "cubeId": str(cube_id),
            "tokenId": token_id,
        },
        approval_token=issue_approval_token(
            purpose="MINT",
            token_id=token_id,
            claims={
                "userId": str(user_id),
                "cubeId": str(cube_id),
                "to": to_address,
            },
        ),
    )
    return str(accepted["operationId"])


def request_transfer(
    *,
    idempotency_key: str,
    trade_id: int,
    seller_user_id: int,
    buyer_user_id: int,
    token_id: int,
    from_address: str,
    to_address: str,
) -> str:
    """Transfer 작업을 접수하고 작업 id를 반환합니다."""
    accepted = _request(
        method="POST",
        path="/internal/v1/transfers",
        body={
            "idempotencyKey": idempotency_key,
            "tradeId": str(trade_id),
            "sellerUserId": str(seller_user_id),
            "buyerUserId": str(buyer_user_id),
            "tokenId": token_id,
        },
        approval_token=issue_approval_token(
            purpose="TRANSFER",
            token_id=token_id,
            claims={
                "tradeId": str(trade_id),
                "sellerUserId": str(seller_user_id),
                "buyerUserId": str(buyer_user_id),
                "from": from_address,
                "to": to_address,
            },
        ),
    )
    return str(accepted["operationId"])


def get_operation(*, operation_id: str) -> dict[str, Any]:
    """작업의 현재 상태와 트랜잭션 정보를 조회합니다."""
    return _request(
        method="GET",
        path=f"/internal/v1/operations/{operation_id}",
    )


def get_nft(*, token_id: int) -> dict[str, Any]:
    """토큰의 발행 여부와 소유자·컨트랙트 주소를 조회합니다."""
    return _request(
        method="GET",
        path=f"/internal/v1/nfts/{token_id}",
    )


def wait_for_confirmation(*, operation_id: str) -> dict[str, Any] | None:
    """작업이 온체인 확정될 때까지 폴링합니다.

    확정되면 작업 정보를, 제한 시간을 넘기면 `None`을 반환합니다.
    실패로 확정된 상태는 `BlockchainError`로 알립니다.
    """
    settings = get_settings()
    deadline = time.monotonic() + settings.blockchain_confirmation_timeout_seconds
    while True:
        operation = get_operation(operation_id=operation_id)
        status = str(operation["status"])
        if status in CONFIRMED_STATUSES:
            return operation
        if status in FAILED_STATUSES:
            raise BlockchainError(
                code="OPERATION_NOT_CONFIRMED",
                message=f"블록체인 작업이 {status} 상태로 종료됐습니다.",
            )
        if time.monotonic() >= deadline:
            return None
        time.sleep(settings.blockchain_confirmation_poll_seconds)


def _request(
    *,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    approval_token: str | None = None,
) -> dict[str, Any]:
    """서명 헤더를 붙여 블록체인 서버를 호출하고 JSON 응답을 반환합니다."""
    settings = get_settings()
    # 서명 대상과 전송 본문이 같아야 하므로 직렬화한 bytes를 그대로 보냅니다.
    body_bytes = b"" if body is None else json.dumps(body).encode()
    headers = build_signature_headers(method=method, path=path, body=body_bytes)
    if body is not None:
        headers["Content-Type"] = "application/json"
    if approval_token is not None:
        headers["Authorization"] = f"Bearer {approval_token}"

    status_code, payload = _send(
        method=method,
        url=f"{settings.blockchain_base_url}{path}",
        headers=headers,
        body=body_bytes,
    )
    if status_code >= 400:
        raise BlockchainError(
            code=str(payload.get("code", "BLOCKCHAIN_REQUEST_FAILED")),
            message=str(payload.get("message", "블록체인 서버 요청에 실패했습니다.")),
            status_code=status_code,
        )
    return payload


def _send(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes,
) -> tuple[int, dict[str, Any]]:
    """실제 HTTP 요청을 보내고 (상태 코드, JSON) 을 반환합니다."""
    settings = get_settings()
    try:
        response = httpx.request(
            method,
            url,
            content=body if body else None,
            headers=headers,
            timeout=settings.blockchain_request_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise BlockchainError(
            code="BLOCKCHAIN_UNREACHABLE",
            message="블록체인 서버에 연결하지 못했습니다.",
        ) from exc

    try:
        payload = response.json()
    except ValueError:
        payload = {}
    return response.status_code, payload if isinstance(payload, dict) else {}
