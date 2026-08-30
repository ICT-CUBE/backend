"""블록체인 연동 서명·승인 JWT 테스트."""

import hashlib
import time
from contextlib import contextmanager
from unittest.mock import patch

import jwt
import pytest

from app.core.config import Settings
from app.services.blockchain import signing

HMAC_SECRET = "dGVzdC1zZWNyZXQtZm9yLWNyb3NzY2hlY2stMzJieXRlcw"
WEBHOOK_SECRET = "d2ViaG9vay1zZWNyZXQtZm9yLXRlc3QtdmFsdWUtMzJi"
APPROVAL_SECRET = "YXBwcm92YWwtc2VjcmV0LWZvci10ZXN0LXZhbHVlLTMy"
TEST_SETTINGS = Settings(
    blockchain_hmac_key_id="backend-test-v1",
    blockchain_hmac_key_secret=HMAC_SECRET,
    blockchain_webhook_hmac_key_id="outbound-test-v1",
    blockchain_webhook_hmac_key_secret=WEBHOOK_SECRET,
    blockchain_approval_jwt_secret=APPROVAL_SECRET,
    blockchain_approval_jwt_issuer="arzone-backend",
    blockchain_approval_jwt_audience="arzone-blockchain-server",
    blockchain_approval_jwt_expire_minutes=10,
)
WEBHOOK_PATH = "/api/v1/internal/blockchain/notifications"


@contextmanager
def test_settings():
    with patch(
        "app.services.blockchain.signing.get_settings",
        return_value=TEST_SETTINGS,
    ):
        yield


def webhook_headers(
    *,
    body: bytes,
    key_id: str = "outbound-test-v1",
    secret: str = WEBHOOK_SECRET,
    timestamp: str | None = None,
    nonce: str = "11111111-1111-1111-1111-111111111111",
) -> dict[str, str]:
    """블록체인 서버가 보내는 형태의 서명 헤더를 만듭니다."""
    timestamp = timestamp if timestamp is not None else str(int(time.time()))
    canonical_string = signing.build_canonical_string(
        method="POST",
        path=WEBHOOK_PATH,
        query=None,
        timestamp=timestamp,
        nonce=nonce,
        body=body,
    )
    return {
        "X-ARZONE-Key-Id": key_id,
        "X-ARZONE-Timestamp": timestamp,
        "X-ARZONE-Nonce": nonce,
        "X-ARZONE-Signature": signing._sign(
            secret=secret,
            canonical_string=canonical_string,
        ),
    }


# --- canonical string ---


def test_build_canonical_string_joins_five_lines_with_uppercase_method() -> None:
    canonical_string = signing.build_canonical_string(
        method="post",
        path="/internal/v1/wallets",
        query=None,
        timestamp="1787900000",
        nonce="a1b2",
        body=b'{"userId":"1"}',
    )

    assert canonical_string.split("\n") == [
        "POST",
        "/internal/v1/wallets",
        "1787900000",
        "a1b2",
        hashlib.sha256(b'{"userId":"1"}').hexdigest(),
    ]


def test_build_canonical_string_hashes_empty_body() -> None:
    canonical_string = signing.build_canonical_string(
        method="GET",
        path="/internal/v1/operations/abc",
        query=None,
        timestamp="1787900001",
        nonce="n-2",
        body=b"",
    )

    assert canonical_string.endswith(hashlib.sha256(b"").hexdigest())


def test_build_canonical_string_sorts_and_encodes_query() -> None:
    canonical_string = signing.build_canonical_string(
        method="GET",
        path="/internal/v1/audit/records",
        query={"b": "2", "a": ["z", "y"], "k v": "x/y"},
        timestamp="1787900002",
        nonce="n-3",
        body=b"",
    )

    assert canonical_string.split("\n")[1] == (
        "/internal/v1/audit/records?a=y&a=z&b=2&k%20v=x%2Fy"
    )


def test_build_canonical_string_keeps_path_when_query_is_empty() -> None:
    canonical_string = signing.build_canonical_string(
        method="GET",
        path="/internal/v1/nfts/26",
        query={},
        timestamp="1787900003",
        nonce="n-4",
        body=b"",
    )

    assert canonical_string.split("\n")[1] == "/internal/v1/nfts/26"


# --- 요청 서명 헤더 ---


def test_build_signature_headers_signs_canonical_string() -> None:
    body = b'{"userId":"1"}'

    with test_settings():
        headers = signing.build_signature_headers(
            method="POST",
            path="/internal/v1/wallets",
            body=body,
        )
        expected_signature = signing._sign(
            secret=HMAC_SECRET,
            canonical_string=signing.build_canonical_string(
                method="POST",
                path="/internal/v1/wallets",
                query=None,
                timestamp=headers["X-ARZONE-Timestamp"],
                nonce=headers["X-ARZONE-Nonce"],
                body=body,
            ),
        )

    assert headers["X-ARZONE-Key-Id"] == "backend-test-v1"
    assert headers["X-ARZONE-Signature"] == expected_signature
    assert int(headers["X-ARZONE-Timestamp"]) == pytest.approx(time.time(), abs=5)


def test_build_signature_headers_uses_new_nonce_every_call() -> None:
    with test_settings():
        first = signing.build_signature_headers(
            method="POST",
            path="/internal/v1/wallets",
            body=b"{}",
        )
        second = signing.build_signature_headers(
            method="POST",
            path="/internal/v1/wallets",
            body=b"{}",
        )

    assert first["X-ARZONE-Nonce"] != second["X-ARZONE-Nonce"]


# --- 승인 JWT ---


def test_issue_approval_token_contains_mint_claims() -> None:
    with test_settings():
        token = signing.issue_approval_token(
            purpose="MINT",
            token_id=26,
            claims={
                "userId": "1",
                "cubeId": "2",
                "to": "0x92E6E89aa218360852252bf7DBB64C5978395E27",
            },
        )

    payload = jwt.decode(
        token,
        signing._decode_secret(APPROVAL_SECRET),
        algorithms=["HS256"],
        issuer="arzone-backend",
        audience="arzone-blockchain-server",
    )
    assert payload["purpose"] == "MINT"
    assert payload["tokenId"] == 26
    assert payload["userId"] == "1"
    assert payload["cubeId"] == "2"
    assert payload["to"] == "0x92E6E89aa218360852252bf7DBB64C5978395E27"
    assert payload["jti"]
    assert payload["exp"] - payload["iat"] == 600


def test_issue_approval_token_contains_transfer_claims() -> None:
    with test_settings():
        token = signing.issue_approval_token(
            purpose="TRANSFER",
            token_id=26,
            claims={
                "tradeId": "3",
                "sellerUserId": "2",
                "buyerUserId": "1",
                "from": "0x1111111111111111111111111111111111111111",
                "to": "0x2222222222222222222222222222222222222222",
            },
        )

    payload = jwt.decode(
        token,
        signing._decode_secret(APPROVAL_SECRET),
        algorithms=["HS256"],
        audience="arzone-blockchain-server",
    )
    assert payload["purpose"] == "TRANSFER"
    assert payload["tradeId"] == "3"
    assert payload["from"] == "0x1111111111111111111111111111111111111111"


def test_issue_approval_token_stays_within_thirty_minutes() -> None:
    # 블록체인 서버가 maxAge 30분을 강제하므로 그보다 짧아야 합니다.
    with test_settings():
        token = signing.issue_approval_token(purpose="MINT", token_id=26, claims={})

    payload = jwt.decode(
        token,
        signing._decode_secret(APPROVAL_SECRET),
        algorithms=["HS256"],
        audience="arzone-blockchain-server",
    )
    assert payload["exp"] - payload["iat"] <= 1800


def test_issue_approval_token_uses_new_jti_every_call() -> None:
    with test_settings():
        first = signing.issue_approval_token(purpose="MINT", token_id=26, claims={})
        second = signing.issue_approval_token(purpose="MINT", token_id=26, claims={})

    options = {"verify_aud": False}

    def jti(token: str) -> str:
        payload = jwt.decode(
            token,
            signing._decode_secret(APPROVAL_SECRET),
            algorithms=["HS256"],
            options=options,
        )
        return payload["jti"]

    assert jti(first) != jti(second)


# --- webhook 서명 검증 ---


def test_verify_webhook_signature_accepts_valid_signature() -> None:
    body = b'{"notificationId":"abc"}'

    with test_settings():
        assert signing.verify_webhook_signature(
            method="POST",
            path=WEBHOOK_PATH,
            headers=webhook_headers(body=body),
            body=body,
        )


def test_verify_webhook_signature_accepts_lowercase_header_names() -> None:
    body = b'{"notificationId":"abc"}'
    headers = {key.lower(): value for key, value in webhook_headers(body=body).items()}

    with test_settings():
        assert signing.verify_webhook_signature(
            method="POST",
            path=WEBHOOK_PATH,
            headers=headers,
            body=body,
        )


def test_verify_webhook_signature_rejects_modified_body() -> None:
    headers = webhook_headers(body=b'{"notificationId":"abc"}')

    with test_settings():
        assert not signing.verify_webhook_signature(
            method="POST",
            path=WEBHOOK_PATH,
            headers=headers,
            body=b'{"notificationId":"tampered"}',
        )


def test_verify_webhook_signature_rejects_other_secret() -> None:
    body = b"{}"
    headers = webhook_headers(body=body, secret=HMAC_SECRET)

    with test_settings():
        assert not signing.verify_webhook_signature(
            method="POST",
            path=WEBHOOK_PATH,
            headers=headers,
            body=body,
        )


def test_verify_webhook_signature_rejects_unknown_key_id() -> None:
    body = b"{}"
    headers = webhook_headers(body=body, key_id="unknown-key")

    with test_settings():
        assert not signing.verify_webhook_signature(
            method="POST",
            path=WEBHOOK_PATH,
            headers=headers,
            body=body,
        )


def test_verify_webhook_signature_rejects_expired_timestamp() -> None:
    body = b"{}"
    old_timestamp = str(int(time.time()) - signing.HMAC_TIMESTAMP_WINDOW_SECONDS - 1)
    headers = webhook_headers(body=body, timestamp=old_timestamp)

    with test_settings():
        assert not signing.verify_webhook_signature(
            method="POST",
            path=WEBHOOK_PATH,
            headers=headers,
            body=body,
        )


def test_verify_webhook_signature_accepts_timestamp_inside_window() -> None:
    body = b"{}"
    recent_timestamp = str(int(time.time()) - signing.HMAC_TIMESTAMP_WINDOW_SECONDS + 5)
    headers = webhook_headers(body=body, timestamp=recent_timestamp)

    with test_settings():
        assert signing.verify_webhook_signature(
            method="POST",
            path=WEBHOOK_PATH,
            headers=headers,
            body=body,
        )


def test_verify_webhook_signature_rejects_non_numeric_timestamp() -> None:
    body = b"{}"
    headers = webhook_headers(body=body)
    headers["X-ARZONE-Timestamp"] = "not-a-number"

    with test_settings():
        assert not signing.verify_webhook_signature(
            method="POST",
            path=WEBHOOK_PATH,
            headers=headers,
            body=body,
        )


def test_verify_webhook_signature_rejects_missing_headers() -> None:
    body = b"{}"
    headers = webhook_headers(body=body)
    del headers["X-ARZONE-Signature"]

    with test_settings():
        assert not signing.verify_webhook_signature(
            method="POST",
            path=WEBHOOK_PATH,
            headers=headers,
            body=body,
        )


def test_verify_webhook_signature_rejects_different_path() -> None:
    body = b"{}"
    headers = webhook_headers(body=body)

    with test_settings():
        assert not signing.verify_webhook_signature(
            method="POST",
            path="/api/v1/internal/blockchain/other",
            headers=headers,
            body=body,
        )
