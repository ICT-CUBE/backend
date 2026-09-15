"""블록체인 완료 알림 수신 테스트."""

import json
import time
from contextlib import ExitStack, contextmanager
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session

from app.blockchain import signing
from app.blockchain.models import BlockchainOperation
from app.core.config import Settings
from app.core.enums import BlockchainOperationStatus, BlockchainOperationType
from app.core.tests.conftest import api_client
from app.main import app

WEBHOOK_SECRET = "d2ViaG9vay1zZWNyZXQtZm9yLXRlc3QtdmFsdWUtMzJi"
TEST_SETTINGS = Settings(
    blockchain_webhook_hmac_key_id="outbound-test-v1",
    blockchain_webhook_hmac_key_secret=WEBHOOK_SECRET,
)
WEBHOOK_PATH = "/api/v1/internal/blockchain/notifications"
NOTIFICATION_ID = "16e98c5d-e79d-46b5-92a5-5573d58d896e"
OPERATION_ID = "3f09aeb0-7832-46a6-8b69-d7420c52a95b"
TX_HASH = "0x54aa5bda988138fb1858592ac5cd88859592fa3ab0403a6657bddf4b3bb356e2"
OWNER_ADDRESS = "0x92E6E89aa218360852252bf7DBB64C5978395E27"
INVALID_SIGNATURE_RESPONSE = {
    "code": "INVALID_WEBHOOK_SIGNATURE",
    "message": "유효하지 않은 webhook 서명입니다.",
}
INVALID_REQUEST_RESPONSE = {
    "code": "INVALID_REQUEST",
    "message": "요청값이 올바르지 않습니다.",
}


@contextmanager
def patched_settings():
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "app.blockchain.signing.get_settings",
                return_value=TEST_SETTINGS,
            )
        )
        yield


def notification_body(**overrides) -> dict:
    body = {
        "notificationId": NOTIFICATION_ID,
        "operationId": OPERATION_ID,
        "idempotencyKey": "5be82123-7896-4b94-8759-364143586c29",
        "operationType": "MINT",
        "tokenId": 44,
        "finalStatus": "ONCHAIN_CONFIRMED",
        "finalOwnerAddress": OWNER_ADDRESS,
        "txHash": TX_HASH,
        "blockNumber": 123,
        "blockHash": "0x" + "0" * 63 + "2",
        "confirmations": 5,
        "serviceRightsState": None,
        "confirmedAt": "2026-08-29T12:00:00.000Z",
    }
    body.update(overrides)
    return body


def signed_headers(*, body: bytes, secret: str = WEBHOOK_SECRET) -> dict[str, str]:
    timestamp = str(int(time.time()))
    nonce = "22222222-2222-2222-2222-222222222222"
    canonical_string = signing.build_canonical_string(
        method="POST",
        path=WEBHOOK_PATH,
        query=None,
        timestamp=timestamp,
        nonce=nonce,
        body=body,
    )
    return {
        "X-ARZONE-Key-Id": "outbound-test-v1",
        "X-ARZONE-Timestamp": timestamp,
        "X-ARZONE-Nonce": nonce,
        "X-ARZONE-Signature": signing._sign(
            secret=secret,
            canonical_string=canonical_string,
        ),
        "Content-Type": "application/json",
    }


def notification_request(
    db: Mock,
    *,
    body: dict | None = None,
    headers: dict[str, str] | None = None,
    sign: bool = True,
):
    payload = json.dumps(body if body is not None else notification_body()).encode()
    request_headers = headers if headers is not None else {}
    if sign:
        request_headers = {**signed_headers(body=payload), **request_headers}
    with patched_settings(), api_client(db) as client:
        return client.post(WEBHOOK_PATH, content=payload, headers=request_headers)


def requested_operation(
    *,
    operation_type: BlockchainOperationType = BlockchainOperationType.MINT,
    status: BlockchainOperationStatus = BlockchainOperationStatus.REQUESTED,
) -> BlockchainOperation:
    return BlockchainOperation(
        id=1,
        operation_type=operation_type,
        status=status,
        token_id=44,
        cube_id=4,
        idempotency_key="5be82123-7896-4b94-8759-364143586c29",
        operation_id=OPERATION_ID,
    )


def set_notification_results(
    db: Mock,
    *,
    recorded_id: int | None = None,
    operation: BlockchainOperation | None = None,
) -> None:
    """중복 조회와 작업 조회 결과를 순서대로 지정합니다."""
    db.scalar.side_effect = [recorded_id, operation]


# --- 정상 ---


def test_receive_notification_confirms_requested_operation() -> None:
    db = Mock(spec=Session)
    operation = requested_operation()
    set_notification_results(db, operation=operation)

    response = notification_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "notificationId": NOTIFICATION_ID,
        "accepted": True,
        "duplicate": False,
    }
    assert operation.status == BlockchainOperationStatus.CONFIRMED
    assert operation.notification_id == NOTIFICATION_ID
    assert operation.tx_hash == TX_HASH
    assert operation.final_owner_address == OWNER_ADDRESS
    db.commit.assert_called_once()


def test_receive_notification_returns_duplicate_for_recorded_notification() -> None:
    db = Mock(spec=Session)
    set_notification_results(db, recorded_id=1)

    response = notification_request(db)

    assert response.status_code == 200
    assert response.json()["duplicate"] is True
    db.commit.assert_not_called()


def test_receive_notification_keeps_confirmed_operation_unchanged() -> None:
    db = Mock(spec=Session)
    operation = requested_operation(status=BlockchainOperationStatus.CONFIRMED)
    operation.tx_hash = "0xalready-confirmed"
    set_notification_results(db, operation=operation)

    response = notification_request(db)

    assert response.status_code == 200
    assert response.json()["duplicate"] is False
    # 이미 확정된 작업의 결과는 덮어쓰지 않습니다.
    assert operation.tx_hash == "0xalready-confirmed"
    assert operation.notification_id == NOTIFICATION_ID


def test_receive_notification_accepts_unknown_operation() -> None:
    db = Mock(spec=Session)
    set_notification_results(db, operation=None)

    response = notification_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "notificationId": NOTIFICATION_ID,
        "accepted": True,
        "duplicate": False,
    }
    db.commit.assert_not_called()


def test_receive_notification_confirms_transfer_operation() -> None:
    db = Mock(spec=Session)
    operation = requested_operation(
        operation_type=BlockchainOperationType.TRANSFER,
    )
    set_notification_results(db, operation=operation)

    response = notification_request(
        db,
        body=notification_body(operationType="TRANSFER"),
    )

    assert response.status_code == 200
    assert operation.status == BlockchainOperationStatus.CONFIRMED


def test_receive_notification_locks_operation_row() -> None:
    db = Mock(spec=Session)
    set_notification_results(db, operation=requested_operation())

    notification_request(db)

    query = str(
        db.scalar.call_args_list[1]
        .args[0]
        .compile(compile_kwargs={"literal_binds": True})
    )
    assert f"blockchain_operation.operation_id = '{OPERATION_ID}'" in query
    assert "FOR UPDATE" in query


# --- 서명 검증 ---


def test_receive_notification_returns_401_without_signature() -> None:
    db = Mock(spec=Session)

    response = notification_request(db, sign=False)

    assert response.status_code == 401
    assert response.json() == INVALID_SIGNATURE_RESPONSE
    db.scalar.assert_not_called()


def test_receive_notification_returns_401_for_wrong_secret() -> None:
    db = Mock(spec=Session)
    payload = json.dumps(notification_body()).encode()
    headers = signed_headers(
        body=payload,
        secret="b3RoZXItc2VjcmV0LXZhbHVlLWZvci10ZXN0cw",
    )

    response = notification_request(db, headers=headers, sign=False)

    assert response.status_code == 401
    assert response.json() == INVALID_SIGNATURE_RESPONSE


def test_receive_notification_returns_401_when_body_is_modified() -> None:
    db = Mock(spec=Session)
    headers = signed_headers(body=json.dumps(notification_body()).encode())

    response = notification_request(
        db,
        body=notification_body(tokenId=99),
        headers=headers,
        sign=False,
    )

    assert response.status_code == 401
    assert response.json() == INVALID_SIGNATURE_RESPONSE


# --- 요청 검증 ---


def test_receive_notification_returns_400_when_field_is_missing() -> None:
    db = Mock(spec=Session)
    body = notification_body()
    del body["txHash"]

    response = notification_request(db, body=body)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_receive_notification_returns_400_for_broken_json() -> None:
    db = Mock(spec=Session)
    payload = b"not-json"
    headers = signed_headers(body=payload)

    with patched_settings(), api_client(db) as client:
        response = client.post(WEBHOOK_PATH, content=payload, headers=headers)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE


# --- 문서 ---


def test_receive_notification_swagger_contract() -> None:
    operation = app.openapi()["paths"][WEBHOOK_PATH]["post"]

    assert set(operation["responses"]) == {"200", "400", "401"}
    assert operation["tags"] == ["blockchain"]
    # 사용자 Access Token이 아니라 HMAC 서명으로 검증합니다.
    assert "security" not in operation
