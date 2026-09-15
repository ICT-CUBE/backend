"""블록체인 서버 요청 서명과 완료 알림 서명 검증."""

import base64
import hashlib
import hmac
import time
from collections.abc import Mapping, Sequence
from urllib.parse import quote
from uuid import uuid4

import jwt

from app.core.config import get_settings

# 블록체인 서버가 허용하는 서명 시각 오차입니다.
HMAC_TIMESTAMP_WINDOW_SECONDS = 300
KEY_ID_HEADER = "X-ARZONE-Key-Id"
TIMESTAMP_HEADER = "X-ARZONE-Timestamp"
NONCE_HEADER = "X-ARZONE-Nonce"
SIGNATURE_HEADER = "X-ARZONE-Signature"

QueryValue = str | Sequence[str]


def build_canonical_string(
    *,
    method: str,
    path: str,
    query: Mapping[str, QueryValue] | None,
    timestamp: str,
    nonce: str,
    body: bytes,
) -> str:
    """블록체인 서버와 동일한 규칙으로 서명 대상 문자열을 만듭니다."""
    return "\n".join(
        [
            method.upper(),
            _normalize_path_with_sorted_query(path, query),
            timestamp,
            nonce,
            hashlib.sha256(body).hexdigest(),
        ]
    )


def build_signature_headers(
    *,
    method: str,
    path: str,
    body: bytes,
    query: Mapping[str, QueryValue] | None = None,
) -> dict[str, str]:
    """요청에 붙일 HMAC 서명 헤더 4종을 만듭니다."""
    settings = get_settings()
    timestamp = str(int(time.time()))
    nonce = str(uuid4())
    canonical_string = build_canonical_string(
        method=method,
        path=path,
        query=query,
        timestamp=timestamp,
        nonce=nonce,
        body=body,
    )
    return {
        KEY_ID_HEADER: settings.blockchain_hmac_key_id,
        TIMESTAMP_HEADER: timestamp,
        NONCE_HEADER: nonce,
        SIGNATURE_HEADER: _sign(
            secret=settings.blockchain_hmac_key_secret,
            canonical_string=canonical_string,
        ),
    }


def issue_approval_token(
    *,
    purpose: str,
    token_id: int,
    claims: Mapping[str, object],
) -> str:
    """소유권 변경 API에 보낼 승인 JWT를 발급합니다."""
    settings = get_settings()
    issued_at = int(time.time())
    payload: dict[str, object] = {
        "jti": str(uuid4()),
        "iss": settings.blockchain_approval_jwt_issuer,
        "aud": settings.blockchain_approval_jwt_audience,
        "iat": issued_at,
        "exp": issued_at + settings.blockchain_approval_jwt_expire_minutes * 60,
        "purpose": purpose,
        "tokenId": token_id,
        **claims,
    }
    # 블록체인 서버도 base64url secret을 디코딩한 바이트로 검증합니다.
    return jwt.encode(
        payload,
        _decode_secret(settings.blockchain_approval_jwt_secret),
        algorithm="HS256",
    )


def verify_webhook_signature(
    *,
    method: str,
    path: str,
    headers: Mapping[str, str],
    body: bytes,
    query: Mapping[str, QueryValue] | None = None,
) -> bool:
    """완료 알림 요청의 HMAC 서명을 검증합니다."""
    settings = get_settings()
    lowercase_headers = {key.lower(): value for key, value in headers.items()}
    key_id = lowercase_headers.get(KEY_ID_HEADER.lower())
    timestamp = lowercase_headers.get(TIMESTAMP_HEADER.lower())
    nonce = lowercase_headers.get(NONCE_HEADER.lower())
    signature = lowercase_headers.get(SIGNATURE_HEADER.lower())
    if not (key_id and timestamp and nonce and signature):
        return False

    if key_id != settings.blockchain_webhook_hmac_key_id:
        return False

    if not _is_fresh_timestamp(timestamp):
        return False

    expected_signature = _sign(
        secret=settings.blockchain_webhook_hmac_key_secret,
        canonical_string=build_canonical_string(
            method=method,
            path=path,
            query=query,
            timestamp=timestamp,
            nonce=nonce,
            body=body,
        ),
    )
    return hmac.compare_digest(expected_signature, signature)


def _normalize_path_with_sorted_query(
    path: str,
    query: Mapping[str, QueryValue] | None,
) -> str:
    """쿼리 키와 같은 키의 값을 정렬해 경로와 합칩니다."""
    if not query:
        return path

    parameters: list[tuple[str, str]] = []
    for key in sorted(query):
        value = query[key]
        values = sorted(value) if isinstance(value, list | tuple) else [str(value)]
        parameters.extend((key, item) for item in values)
    if not parameters:
        return path

    query_string = "&".join(
        f"{quote(key, safe='')}={quote(value, safe='')}" for key, value in parameters
    )
    return f"{path}?{query_string}"


def _sign(*, secret: str, canonical_string: str) -> str:
    """base64url secret을 디코딩해 소문자 hex HMAC-SHA-256을 계산합니다."""
    return hmac.new(
        _decode_secret(secret),
        canonical_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _decode_secret(secret: str) -> bytes:
    padding = "=" * (-len(secret) % 4)
    return base64.urlsafe_b64decode(secret + padding)


def _is_fresh_timestamp(timestamp: str) -> bool:
    try:
        timestamp_seconds = int(timestamp)
    except ValueError:
        return False
    return abs(time.time() - timestamp_seconds) <= HMAC_TIMESTAMP_WINDOW_SECONDS
