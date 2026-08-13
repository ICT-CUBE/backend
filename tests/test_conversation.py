"""텍스트 및 음성 대화 조회 API 테스트."""

from collections.abc import Iterator
from datetime import datetime
from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models.conversation import (
    AvatarConversationMessage,
    AvatarConversationSession,
)
from app.models.cube import CubeOwnership
from app.models.enums import (
    AvatarConversationSessionStatus,
    ConversationMessageSenderType,
    ConversationMessageStatus,
    ConversationType,
)


def create_conversation_session_request(
    db: Mock,
    body: dict | None = None,
    raise_server_exceptions: bool = True,
):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            raise_server_exceptions=raise_server_exceptions,
        ) as client:
            return client.post(
                "/api/v1/users/me/conversation-sessions",
                json=body if body is not None else {"conversationType": "TEXT"},
            )
    finally:
        app.dependency_overrides.clear()


def request_conversation_session_detail(db: Mock, conversation_session_id: int = 1001):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            return client.get(
                f"/api/v1/users/me/conversation-sessions/{conversation_session_id}"
            )
    finally:
        app.dependency_overrides.clear()


def delete_conversation_session_request(
    db: Mock,
    conversation_session_id: int = 1001,
    raise_server_exceptions: bool = True,
):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            raise_server_exceptions=raise_server_exceptions,
        ) as client:
            return client.delete(
                f"/api/v1/users/me/conversation-sessions/{conversation_session_id}"
            )
    finally:
        app.dependency_overrides.clear()


def save_conversation_message_request(
    db: Mock,
    conversation_message_id: int = 5006,
    raise_server_exceptions: bool = True,
):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            raise_server_exceptions=raise_server_exceptions,
        ) as client:
            return client.patch(
                f"/api/v1/users/me/conversation-messages/{conversation_message_id}/save"
            )
    finally:
        app.dependency_overrides.clear()


def request_conversation_sessions(db: Mock, query: str = "?conversationType=TEXT"):
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            return client.get(f"/api/v1/users/me/conversation-sessions{query}")
    finally:
        app.dependency_overrides.clear()


def conversation_result(*rows: tuple[AvatarConversationSession, AvatarConversationMessage]):
    result = Mock()
    result.all.return_value = list(rows)
    return result


def first_result(row: object | None):
    result = Mock()
    result.first.return_value = row
    return result


def session(
    *,
    id: int,
    conversation_type: ConversationType,
    title: str = "오늘의 무대 이야기",
    audio_url: str | None = None,
    audio_duration_seconds: int | None = None,
) -> AvatarConversationSession:
    return AvatarConversationSession(
        id=id,
        conversation_type=conversation_type,
        conversation_title=title,
        audio_url=audio_url,
        audio_duration_seconds=audio_duration_seconds,
    )


def message(
    *,
    id: int,
    content: str = "헐! 대박인데?",
    sent_at: datetime = datetime.fromisoformat("2026-07-29T12:25:00"),
    sequence_number: int = 1,
    sender_type: ConversationMessageSenderType = ConversationMessageSenderType.USER,
    is_text_saved: bool = False,
    status: ConversationMessageStatus = ConversationMessageStatus.ALLOWED,
) -> AvatarConversationMessage:
    return AvatarConversationMessage(
        id=id,
        content=content,
        sent_at=sent_at,
        sequence_number=sequence_number,
        sender_type=sender_type,
        is_text_saved=is_text_saved,
        status=status,
    )


def test_text_conversation_sessions_return_last_message_content() -> None:
    db = Mock(spec=Session)
    db.execute.return_value = conversation_result(
        (
            session(id=1001, conversation_type=ConversationType.TEXT),
            message(id=5003),
        )
    )

    response = request_conversation_sessions(
        db,
        "?conversationType=TEXT&page=0&size=20",
    )

    assert response.status_code == 200
    assert response.json() == {
        "conversationSessions": [
            {
                "id": 1001,
                "conversationType": "TEXT",
                "conversationTitle": "오늘의 무대 이야기",
                "audioUrl": None,
                "audioDurationSeconds": None,
                "lastMessage": {
                    "id": 5003,
                    "content": "헐! 대박인데?",
                    "sentAt": "2026-07-29T12:25:00+09:00",
                },
            }
        ],
        "pagination": {"page": 0, "size": 20, "hasNext": False},
    }


def test_voice_conversation_sessions_return_null_content_and_audio_fields() -> None:
    db = Mock(spec=Session)
    db.execute.return_value = conversation_result(
        (
            session(
                id=1101,
                conversation_type=ConversationType.VOICE,
                title="저녁 메뉴 추천",
                audio_url="voice_1101.m4a",
                audio_duration_seconds=264,
            ),
            message(id=5003, content="음성 대화 내용"),
        )
    )

    response = request_conversation_sessions(db, "?conversationType=VOICE")

    assert response.status_code == 200
    assert response.json()["conversationSessions"][0] == {
        "id": 1101,
        "conversationType": "VOICE",
        "conversationTitle": "저녁 메뉴 추천",
        "audioUrl": "voice_1101.m4a",
        "audioDurationSeconds": 264,
        "lastMessage": {
            "id": 5003,
            "content": None,
            "sentAt": "2026-07-29T12:25:00+09:00",
        },
    }


def test_conversation_sessions_use_fixed_size_and_has_next() -> None:
    db = Mock(spec=Session)
    db.execute.return_value = conversation_result(
        *[
            (
                session(id=index, conversation_type=ConversationType.TEXT),
                message(id=index),
            )
            for index in range(1, 22)
        ]
    )

    response = request_conversation_sessions(db)

    assert response.status_code == 200
    body = response.json()
    assert len(body["conversationSessions"]) == 20
    assert body["pagination"] == {"page": 0, "size": 20, "hasNext": True}


def test_conversation_sessions_return_empty_list() -> None:
    db = Mock(spec=Session)
    db.execute.return_value = conversation_result()

    response = request_conversation_sessions(db)

    assert response.status_code == 200
    assert response.json() == {
        "conversationSessions": [],
        "pagination": {"page": 0, "size": 20, "hasNext": False},
    }


def test_conversation_sessions_reject_invalid_query_with_common_400() -> None:
    db = Mock(spec=Session)

    response = request_conversation_sessions(db, "?conversationType=TEXT&size=10")

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.execute.assert_not_called()


def test_conversation_sessions_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/conversation-sessions"
    ]["get"]

    assert set(operation["responses"]) == {"200"}
    assert "security" not in operation


def test_create_conversation_session_adds_initial_orm_model() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = CubeOwnership(id=1)

    def set_created_id() -> None:
        db.add.call_args.args[0].id = 1001

    db.flush.side_effect = set_created_id

    response = create_conversation_session_request(db)

    assert response.status_code == 201
    assert response.json() == {
        "conversationSession": {"id": 1001, "conversationType": "TEXT"}
    }
    inserted = db.add.call_args.args[0]
    assert isinstance(inserted, AvatarConversationSession)
    assert inserted.cube_ownership_id == 1
    assert inserted.conversation_type == ConversationType.TEXT
    assert inserted.started_at.tzinfo is None
    assert inserted.ended_at is None
    assert inserted.audio_url is None
    assert inserted.audio_duration_seconds is None
    assert inserted.conversation_title is None
    assert inserted.status == AvatarConversationSessionStatus.ACTIVE
    assert inserted.deleted_at is None
    db.commit.assert_called_once()


def test_create_voice_conversation_session_returns_voice_type() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = CubeOwnership(id=1)
    db.flush.side_effect = lambda: setattr(db.add.call_args.args[0], "id", 1101)

    response = create_conversation_session_request(
        db,
        body={"conversationType": "VOICE"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "conversationSession": {"id": 1101, "conversationType": "VOICE"}
    }
    assert db.add.call_args.args[0].conversation_type == ConversationType.VOICE


def test_create_conversation_session_returns_400_for_invalid_body() -> None:
    db = Mock(spec=Session)

    response = create_conversation_session_request(
        db,
        body={"conversationType": "INVALID"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.scalar.assert_not_called()


def test_create_conversation_session_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = CubeOwnership(id=1)
    db.commit.side_effect = RuntimeError("db failed")

    response = create_conversation_session_request(
        db,
        raise_server_exceptions=False,
    )

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_create_conversation_session_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/conversation-sessions"
    ]["post"]

    assert set(operation["responses"]) == {"201"}
    assert "security" not in operation


def test_delete_text_conversation_session_sets_deleted_at() -> None:
    db = Mock(spec=Session)
    conversation_session = session(
        id=1001,
        conversation_type=ConversationType.TEXT,
    )
    conversation_session.deleted_at = None
    db.scalar.return_value = conversation_session

    response = delete_conversation_session_request(db)

    assert response.status_code == 204
    assert response.content == b""
    assert isinstance(conversation_session.deleted_at, datetime)
    assert conversation_session.deleted_at.tzinfo is None
    db.commit.assert_called_once()
    db.scalars.assert_not_called()


def test_delete_voice_conversation_session_succeeds() -> None:
    db = Mock(spec=Session)
    conversation_session = session(
        id=1101,
        conversation_type=ConversationType.VOICE,
    )
    conversation_session.deleted_at = None
    db.scalar.return_value = conversation_session

    response = delete_conversation_session_request(db, conversation_session_id=1101)

    assert response.status_code == 204
    assert isinstance(conversation_session.deleted_at, datetime)
    db.commit.assert_called_once()


def test_delete_empty_conversation_session_does_not_check_messages() -> None:
    db = Mock(spec=Session)
    conversation_session = session(
        id=1002,
        conversation_type=ConversationType.TEXT,
    )
    conversation_session.deleted_at = None
    db.scalar.return_value = conversation_session

    response = delete_conversation_session_request(db, conversation_session_id=1002)

    assert response.status_code == 204
    db.scalars.assert_not_called()


def test_delete_conversation_session_returns_404_for_unknown_or_already_deleted() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = delete_conversation_session_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CONVERSATION_SESSION_NOT_FOUND",
        "message": "삭제할 대화 세션을 찾을 수 없습니다.",
    }
    db.commit.assert_not_called()


def test_delete_conversation_session_rejects_invalid_path_with_common_400() -> None:
    db = Mock(spec=Session)

    response = delete_conversation_session_request(db, conversation_session_id=0)

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.scalar.assert_not_called()


def test_delete_conversation_session_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    conversation_session = session(
        id=1001,
        conversation_type=ConversationType.TEXT,
    )
    conversation_session.deleted_at = None
    db.scalar.return_value = conversation_session
    db.commit.side_effect = RuntimeError("db failed")

    response = delete_conversation_session_request(
        db,
        raise_server_exceptions=False,
    )

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_delete_conversation_session_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/conversation-sessions/{conversationSessionId}"
    ]["delete"]

    assert set(operation["responses"]) == {"204", "404"}
    assert "security" not in operation


def test_save_conversation_message_toggles_false_to_true() -> None:
    db = Mock(spec=Session)
    conversation_message = message(
        id=5006,
        sender_type=ConversationMessageSenderType.AVATAR,
        is_text_saved=False,
    )
    conversation_session = session(
        id=1001,
        conversation_type=ConversationType.TEXT,
    )
    db.execute.return_value = first_result((conversation_message, conversation_session))

    response = save_conversation_message_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "conversationMessage": {"id": 5006, "isTextSaved": True}
    }
    assert conversation_message.is_text_saved is True
    db.commit.assert_called_once()


def test_save_conversation_message_toggles_true_to_false() -> None:
    db = Mock(spec=Session)
    conversation_message = message(
        id=5006,
        sender_type=ConversationMessageSenderType.AVATAR,
        is_text_saved=True,
        status=ConversationMessageStatus.BLOCKED,
    )
    conversation_session = session(
        id=1001,
        conversation_type=ConversationType.TEXT,
    )
    db.execute.return_value = first_result((conversation_message, conversation_session))

    response = save_conversation_message_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "conversationMessage": {"id": 5006, "isTextSaved": False}
    }
    assert conversation_message.is_text_saved is False


def test_save_conversation_message_returns_404_for_unknown_or_deleted_session() -> None:
    db = Mock(spec=Session)
    db.execute.return_value = first_result(None)

    response = save_conversation_message_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CONVERSATION_MESSAGE_NOT_FOUND",
        "message": "대화 메시지를 찾을 수 없습니다.",
    }
    db.commit.assert_not_called()


def test_save_conversation_message_returns_404_for_voice_session() -> None:
    db = Mock(spec=Session)
    conversation_message = message(
        id=5006,
        sender_type=ConversationMessageSenderType.AVATAR,
    )
    conversation_session = session(
        id=1101,
        conversation_type=ConversationType.VOICE,
    )
    db.execute.return_value = first_result((conversation_message, conversation_session))

    response = save_conversation_message_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "VOICE_CONVERSATION_MESSAGE_SAVE_NOT_AVAILABLE",
        "message": "음성 대화는 보관이 불가합니다.",
    }
    assert conversation_message.is_text_saved is False
    db.commit.assert_not_called()


def test_save_conversation_message_returns_404_for_user_message() -> None:
    db = Mock(spec=Session)
    conversation_message = message(
        id=5006,
        sender_type=ConversationMessageSenderType.USER,
    )
    conversation_session = session(
        id=1001,
        conversation_type=ConversationType.TEXT,
    )
    db.execute.return_value = first_result((conversation_message, conversation_session))

    response = save_conversation_message_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "USER_CONVERSATION_MESSAGE_SAVE_NOT_AVAILABLE",
        "message": "사용자 대화는 보관이 불가합니다.",
    }
    assert conversation_message.is_text_saved is False
    db.commit.assert_not_called()


def test_save_conversation_message_rejects_invalid_path_with_common_400() -> None:
    db = Mock(spec=Session)

    response = save_conversation_message_request(db, conversation_message_id=0)

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.execute.assert_not_called()


def test_save_conversation_message_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    conversation_message = message(
        id=5006,
        sender_type=ConversationMessageSenderType.AVATAR,
    )
    conversation_session = session(
        id=1001,
        conversation_type=ConversationType.TEXT,
    )
    db.execute.return_value = first_result((conversation_message, conversation_session))
    db.commit.side_effect = RuntimeError("db failed")

    response = save_conversation_message_request(
        db,
        raise_server_exceptions=False,
    )

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_save_conversation_message_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/conversation-messages/{conversationMessageId}/save"
    ]["patch"]

    assert set(operation["responses"]) == {"200", "404"}
    assert "security" not in operation


def test_conversation_session_detail_returns_messages_descending() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = session(
        id=1001,
        conversation_type=ConversationType.TEXT,
    )
    db.scalars.return_value.all.return_value = [
        message(
            id=5003,
            content="헐!! 대박인데?",
            sequence_number=3,
            sender_type=ConversationMessageSenderType.AVATAR,
            sent_at=datetime.fromisoformat("2026-07-29T12:25:00"),
        ),
        message(
            id=5002,
            content="나 지금 카페에서 공부하고 있어.",
            sequence_number=2,
            sender_type=ConversationMessageSenderType.USER,
            sent_at=datetime.fromisoformat("2026-07-29T12:23:30"),
        ),
    ]

    response = request_conversation_session_detail(db)

    assert response.status_code == 200
    assert response.json() == {
        "conversationSession": {
            "id": 1001,
            "messages": [
                {
                    "id": 5003,
                    "senderType": "AVATAR",
                    "content": "헐!! 대박인데?",
                    "sequenceNumber": 3,
                    "sentAt": "2026-07-29T12:25:00+09:00",
                },
                {
                    "id": 5002,
                    "senderType": "USER",
                    "content": "나 지금 카페에서 공부하고 있어.",
                    "sequenceNumber": 2,
                    "sentAt": "2026-07-29T12:23:30+09:00",
                },
            ],
        }
    }


def test_conversation_session_detail_returns_404_for_unknown_session() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = request_conversation_session_detail(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CONVERSATION_SESSION_NOT_FOUND",
        "message": "대화 세션을 찾을 수 없습니다.",
    }
    db.scalars.assert_not_called()


def test_conversation_session_detail_returns_404_for_voice_session() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = session(
        id=1101,
        conversation_type=ConversationType.VOICE,
    )

    response = request_conversation_session_detail(db, conversation_session_id=1101)

    assert response.status_code == 404
    assert response.json() == {
        "code": "VOICE_CONVERSATION_DETAIL_NOT_AVAILABLE",
        "message": "음성 대화는 세션 상세 조회가 불가능합니다.",
    }
    db.scalars.assert_not_called()


def test_conversation_session_detail_returns_404_when_message_is_empty() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = session(
        id=1001,
        conversation_type=ConversationType.TEXT,
    )
    db.scalars.return_value.all.return_value = []

    response = request_conversation_session_detail(db)

    assert response.status_code == 404
    assert response.json()["code"] == "CONVERSATION_SESSION_NOT_FOUND"


def test_conversation_session_detail_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/conversation-sessions/{conversationSessionId}"
    ]["get"]

    assert set(operation["responses"]) == {"200", "404"}
    assert "security" not in operation
