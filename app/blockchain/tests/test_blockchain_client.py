"""블록체인 서버 클라이언트·이미지 준비 테스트."""

import base64
import json
from contextlib import ExitStack, contextmanager
from unittest.mock import Mock, patch

import httpx
import jwt
import pytest

from app.blockchain import client, images, signing
from app.blockchain.errors import BlockchainError
from app.core.config import Settings

APPROVAL_SECRET = "YXBwcm92YWwtc2VjcmV0LWZvci10ZXN0LXZhbHVlLTMy"
TEST_SETTINGS = Settings(
    blockchain_base_url="http://blockchain.test",
    blockchain_hmac_key_id="backend-test-v1",
    blockchain_hmac_key_secret="dGVzdC1zZWNyZXQtZm9yLWNyb3NzY2hlY2stMzJieXRlcw",
    blockchain_approval_jwt_secret=APPROVAL_SECRET,
    blockchain_approval_jwt_issuer="arzone-backend",
    blockchain_approval_jwt_audience="arzone-blockchain-server",
    blockchain_confirmation_timeout_seconds=10,
    blockchain_confirmation_poll_seconds=0,
)
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
WALLET_ADDRESS = "0x92E6E89aa218360852252bf7DBB64C5978395E27"


@contextmanager
def patched_settings(settings: Settings = TEST_SETTINGS):
    """설정을 임포트해 쓰는 두 모듈 모두에 테스트 설정을 주입합니다."""
    with ExitStack() as stack:
        for module in ("client", "signing"):
            stack.enter_context(
                patch(
                    f"app.blockchain.{module}.get_settings",
                    return_value=settings,
                )
            )
        yield


def send_result(payload: dict, *, status_code: int = 200):
    """`_send` 를 대체해 호출 인자를 기록하고 지정한 응답을 돌려줍니다."""
    return Mock(return_value=(status_code, payload))


def decoded_approval_token(send: Mock) -> dict:
    authorization = send.call_args.kwargs["headers"]["Authorization"]
    return jwt.decode(
        authorization.removeprefix("Bearer "),
        signing._decode_secret(APPROVAL_SECRET),
        algorithms=["HS256"],
        audience="arzone-blockchain-server",
    )


# --- 지갑 ---


def test_ensure_wallet_returns_address() -> None:
    send = send_result({"userId": "1", "address": WALLET_ADDRESS})

    with patched_settings(), patch.object(client, "_send", send):
        address = client.ensure_wallet(user_id=1)

    assert address == WALLET_ADDRESS
    assert send.call_args.kwargs["method"] == "POST"
    assert send.call_args.kwargs["url"] == (
        "http://blockchain.test/internal/v1/wallets"
    )
    assert json.loads(send.call_args.kwargs["body"]) == {"userId": "1"}


def test_request_includes_signature_headers() -> None:
    send = send_result({"address": WALLET_ADDRESS})

    with patched_settings(), patch.object(client, "_send", send):
        client.ensure_wallet(user_id=1)

    headers = send.call_args.kwargs["headers"]
    assert set(headers) >= {
        "X-ARZONE-Key-Id",
        "X-ARZONE-Timestamp",
        "X-ARZONE-Nonce",
        "X-ARZONE-Signature",
        "Content-Type",
    }
    assert headers["X-ARZONE-Key-Id"] == "backend-test-v1"
    assert "Authorization" not in headers


# --- 메타데이터 ---


def test_prepare_metadata_sends_fixed_grade_and_benefit() -> None:
    send = send_result({"tokenId": 26, "ready": True})

    with patched_settings(), patch.object(client, "_send", send):
        ready = client.prepare_metadata(
            token_id=26,
            cube_number="NO.0026",
            image_base64="aW1hZ2U=",
            image_mime_type="image/png",
        )

    assert ready is True
    assert json.loads(send.call_args.kwargs["body"]) == {
        "tokenId": 26,
        "cubeNumber": "NO.0026",
        "publicGrade": "UNSPECIFIED",
        "imageBase64": "aW1hZ2U=",
        "imageMimeType": "image/png",
        "benefitReferenceId": "NONE",
    }


def test_get_metadata_status_reads_ready_flag() -> None:
    send = send_result({"tokenId": 26, "ready": False})

    with patched_settings(), patch.object(client, "_send", send):
        assert client.get_metadata_status(token_id=26) is False

    assert send.call_args.kwargs["url"].endswith("/internal/v1/metadata/26")


# --- Mint / Transfer ---


def test_request_mint_sends_approval_token_with_mint_claims() -> None:
    send = send_result({"operationId": "op-1", "status": "REQUESTED"})

    with patched_settings(), patch.object(client, "_send", send):
        operation_id = client.request_mint(
            idempotency_key="key-1",
            user_id=1,
            cube_id=2,
            token_id=26,
            to_address=WALLET_ADDRESS,
        )

    assert operation_id == "op-1"
    assert json.loads(send.call_args.kwargs["body"]) == {
        "idempotencyKey": "key-1",
        "userId": "1",
        "cubeId": "2",
        "tokenId": 26,
    }
    payload = decoded_approval_token(send)
    assert payload["purpose"] == "MINT"
    assert payload["tokenId"] == 26
    assert payload["userId"] == "1"
    assert payload["cubeId"] == "2"
    assert payload["to"] == WALLET_ADDRESS


def test_request_transfer_sends_approval_token_with_transfer_claims() -> None:
    send = send_result({"operationId": "op-2", "status": "REQUESTED"})

    with patched_settings(), patch.object(client, "_send", send):
        operation_id = client.request_transfer(
            idempotency_key="key-2",
            trade_id=3,
            seller_user_id=2,
            buyer_user_id=1,
            token_id=26,
            from_address=WALLET_ADDRESS,
            to_address="0x1111111111111111111111111111111111111111",
        )

    assert operation_id == "op-2"
    assert json.loads(send.call_args.kwargs["body"]) == {
        "idempotencyKey": "key-2",
        "tradeId": "3",
        "sellerUserId": "2",
        "buyerUserId": "1",
        "tokenId": 26,
    }
    payload = decoded_approval_token(send)
    assert payload["purpose"] == "TRANSFER"
    assert payload["sellerUserId"] == "2"
    assert payload["buyerUserId"] == "1"
    assert payload["from"] == WALLET_ADDRESS
    assert payload["to"] == "0x1111111111111111111111111111111111111111"


# --- 조회 ---


def test_get_operation_uses_operation_path() -> None:
    send = send_result({"operationId": "op-1", "status": "PENDING"})

    with patched_settings(), patch.object(client, "_send", send):
        operation = client.get_operation(operation_id="op-1")

    assert operation["status"] == "PENDING"
    assert send.call_args.kwargs["url"].endswith("/internal/v1/operations/op-1")
    assert send.call_args.kwargs["body"] == b""


def test_get_nft_uses_token_path() -> None:
    send = send_result({"tokenId": 26, "minted": True})

    with patched_settings(), patch.object(client, "_send", send):
        nft = client.get_nft(token_id=26)

    assert nft["minted"] is True
    assert send.call_args.kwargs["url"].endswith("/internal/v1/nfts/26")


# --- 오류 처리 ---


def test_request_raises_blockchain_error_for_error_response() -> None:
    send = send_result(
        {"code": "METADATA_NOT_READY", "message": "not ready", "requestId": "r-1"},
        status_code=409,
    )

    with (
        patched_settings(),
        patch.object(client, "_send", send),
        pytest.raises(BlockchainError) as error,
    ):
        client.get_nft(token_id=26)

    assert error.value.code == "METADATA_NOT_READY"
    assert error.value.status_code == 409


def test_request_raises_blockchain_error_when_server_is_unreachable() -> None:
    with patched_settings(), patch.object(
        client.httpx,
        "request",
        side_effect=httpx.ConnectError("refused"),
    ), pytest.raises(BlockchainError) as error:
        client.get_nft(token_id=26)

    assert error.value.code == "BLOCKCHAIN_UNREACHABLE"


# --- 확정 대기 ---


def test_wait_for_confirmation_returns_confirmed_operation() -> None:
    operation = {"operationId": "op-1", "status": "ONCHAIN_CONFIRMED"}

    with patched_settings(), patch.object(
        client,
        "get_operation",
        return_value=operation,
    ):
        assert client.wait_for_confirmation(operation_id="op-1") == operation


def test_wait_for_confirmation_polls_until_confirmed() -> None:
    responses = [
        {"status": "REQUESTED"},
        {"status": "PENDING"},
        {"status": "COMPLETED"},
    ]

    with patched_settings(), patch.object(
        client,
        "get_operation",
        side_effect=responses,
    ) as get_operation:
        operation = client.wait_for_confirmation(operation_id="op-1")

    assert operation["status"] == "COMPLETED"
    assert get_operation.call_count == 3


def test_wait_for_confirmation_raises_for_failed_status() -> None:
    with patched_settings(), patch.object(
        client,
        "get_operation",
        return_value={"status": "FAILED"},
    ), pytest.raises(BlockchainError) as error:
        client.wait_for_confirmation(operation_id="op-1")

    assert error.value.code == "OPERATION_NOT_CONFIRMED"


def test_wait_for_confirmation_raises_for_review_required_status() -> None:
    with patched_settings(), patch.object(
        client,
        "get_operation",
        return_value={"status": "REVIEW_REQUIRED"},
    ), pytest.raises(BlockchainError):
        client.wait_for_confirmation(operation_id="op-1")


def test_wait_for_confirmation_returns_none_after_timeout() -> None:
    timeout_settings = TEST_SETTINGS.model_copy(
        update={"blockchain_confirmation_timeout_seconds": 0}
    )

    with patched_settings(timeout_settings), patch.object(
        client,
        "get_operation",
        return_value={"status": "PENDING"},
    ) as get_operation:
        assert client.wait_for_confirmation(operation_id="op-1") is None

    assert get_operation.call_count == 1


# --- 제품 이미지 ---


def test_prepare_product_image_returns_base64_and_mime_type() -> None:
    with patch.object(
        images.httpx,
        "get",
        return_value=Mock(content=PNG_BYTES, raise_for_status=Mock()),
    ):
        image_base64, mime_type = images.prepare_product_image(
            image_url="https://cdn.example.com/cube.png"
        )

    assert base64.b64decode(image_base64) == PNG_BYTES
    assert mime_type == "image/png"


def test_prepare_product_image_detects_jpeg_webp_gif() -> None:
    samples = {
        b"\xff\xd8\xff" + b"\x00" * 16: "image/jpeg",
        b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 8: "image/webp",
        b"GIF89a" + b"\x00" * 16: "image/gif",
    }

    for content, expected_mime_type in samples.items():
        with patch.object(
            images.httpx,
            "get",
            return_value=Mock(content=content, raise_for_status=Mock()),
        ):
            _, mime_type = images.prepare_product_image(
                image_url="https://cdn.example.com/cube"
            )
        assert mime_type == expected_mime_type


def test_prepare_product_image_rejects_oversized_image() -> None:
    oversized = b"\x89PNG\r\n\x1a\n" + b"\x00" * images.IMAGE_MAX_BYTES

    with patch.object(
        images.httpx,
        "get",
        return_value=Mock(content=oversized, raise_for_status=Mock()),
    ), pytest.raises(BlockchainError) as error:
        images.prepare_product_image(image_url="https://cdn.example.com/cube.png")

    assert error.value.code == "IMAGE_TOO_LARGE"


def test_prepare_product_image_rejects_unsupported_format() -> None:
    with patch.object(
        images.httpx,
        "get",
        return_value=Mock(content=b"%PDF-1.7", raise_for_status=Mock()),
    ), pytest.raises(BlockchainError) as error:
        images.prepare_product_image(image_url="https://cdn.example.com/cube.pdf")

    assert error.value.code == "IMAGE_TYPE_NOT_SUPPORTED"


def test_prepare_product_image_reports_download_failure() -> None:
    with patch.object(
        images.httpx,
        "get",
        side_effect=httpx.ConnectError("refused"),
    ), pytest.raises(BlockchainError) as error:
        images.prepare_product_image(image_url="https://cdn.example.com/cube.png")

    assert error.value.code == "IMAGE_DOWNLOAD_FAILED"
