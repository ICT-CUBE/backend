"""텍스트 및 음성 대화 조회 API 테스트."""

from datetime import datetime
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session

from app.main import app
from app.models.conversation import (
    AvatarConversationMessage,
    AvatarConversationSession,
    ConversationReport,
)
from app.models.cube import CubeOwnership
from app.models.enums import (
    AvatarConversationSessionStatus,
    ConversationMessageSenderType,
    ConversationMessageStatus,
    ConversationReportReason,
    ConversationType,
)
from tests.conftest import api_client


def create_conversation_session_request(
    db: Mock,
    body: dict | None = None,
    raise_server_exceptions: bool = True,
):
    with api_client(
        db,
        raise_server_exceptions=raise_server_exceptions,
    ) as client:
        return client.post(
            "/api/v1/users/me/conversation-sessions",
            json=body if body is not None else {"conversationType": "TEXT"},
        )


def request_conversation_session_detail(db: Mock, conversation_session_id: int = 1001):
    with api_client(db) as client:
        return client.get(
            f"/api/v1/users/me/conversation-sessions/{conversation_session_id}"
        )


def delete_conversation_session_request(
    db: Mock,
    conversation_session_id: int = 1001,
    raise_server_exceptions: bool = True,
):
    with api_client(
        db,
        raise_server_exceptions=raise_server_exceptions,
    ) as client:
        return client.delete(
            f"/api/v1/users/me/conversation-sessions/{conversation_session_id}"
        )


def save_conversation_message_request(
    db: Mock,
    conversation_message_id: int = 5006,
    raise_server_exceptions: bool = True,
):
    with api_client(
        db,
        raise_server_exceptions=raise_server_exceptions,
    ) as client:
        return client.patch(
            f"/api/v1/users/me/conversation-messages/{conversation_message_id}/save"
        )


def create_conversation_report_request(
    db: Mock,
    conversation_message_id: int = 5006,
    body: dict | None = None,
    raise_server_exceptions: bool = True,
):
    with api_client(
        db,
        raise_server_exceptions=raise_server_exceptions,
    ) as client:
        return client.post(
            f"/api/v1/users/me/conversation-messages/"
            f"{conversation_message_id}/reports",
            json=(
                body
                if body is not None
                else {
                    "reason": "INCORRECT_PERSONA",
                    "detailReason": "아티스트 설정과 다른 답변입니다.",
                }
            ),
        )


def reply_conversation_message_request(
    db: Mock,
    conversation_session_id: int = 1001,
    body: dict | None = None,
    raise_server_exceptions: bool = True,
):
    with api_client(
        db,
        raise_server_exceptions=raise_server_exceptions,
    ) as client:
        return client.post(
            f"/api/v1/users/me/conversation-sessions/"
            f"{conversation_session_id}/messages",
            json=body if body is not None else {"content": "오늘 뭐 하고 있었어?"},
        )


def update_conversation_session_request(
    db: Mock,
    conversation_session_id: int = 1001,
    data: dict | None = None,
    files: dict | None = None,
    raise_server_exceptions: bool = True,
):
    with api_client(
        db,
        raise_server_exceptions=raise_server_exceptions,
    ) as client:
        return client.patch(
            f"/api/v1/users/me/conversation-sessions/{conversation_session_id}",
            data=data,
            files=files,
        )


def request_conversation_sessions(db: Mock, query: str = "?conversationType=TEXT"):
    with api_client(db) as client:
        return client.get(f"/api/v1/users/me/conversation-sessions{query}")


def request_conversation_archive(db: Mock):
    with api_client(db) as client:
        return client.get("/api/v1/users/me/conversation-archive")


def delete_conversation_archive_message_request(
    db: Mock,
    conversation_message_id: int = 5006,
    raise_server_exceptions: bool = True,
):
    with api_client(
        db,
        raise_server_exceptions=raise_server_exceptions,
    ) as client:
        return client.delete(
            f"/api/v1/users/me/conversation-messages/"
            f"{conversation_message_id}/unsave"
        )


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
    conversation_session_id: int | None = None,
    content: str = "헐! 대박인데?",
    sent_at: datetime | None = None,
    sequence_number: int = 1,
    sender_type: ConversationMessageSenderType = ConversationMessageSenderType.USER,
    is_text_saved: bool = False,
    status: ConversationMessageStatus = ConversationMessageStatus.ALLOWED,
) -> AvatarConversationMessage:
    return AvatarConversationMessage(
        id=id,
        conversation_session_id=conversation_session_id,
        content=content,
        sent_at=sent_at or datetime.fromisoformat("2026-07-29T12:25:00"),
        sequence_number=sequence_number,
        sender_type=sender_type,
        is_text_saved=is_text_saved,
        status=status,
    )


def test_text_conversation_sessions_return_last_message_content() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = CubeOwnership(id=1)
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
                    "sentAt": "2026-07-29T12:25:00",
                },
            }
        ],
        "pagination": {"page": 0, "size": 20, "hasNext": False},
    }


def test_voice_conversation_sessions_return_null_content_and_audio_fields() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = CubeOwnership(id=1)
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
            "sentAt": "2026-07-29T12:25:00",
        },
    }


def test_conversation_sessions_use_requested_size_and_has_next() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = CubeOwnership(id=1)
    db.execute.return_value = conversation_result(
        *[
            (
                session(id=index, conversation_type=ConversationType.TEXT),
                message(id=index),
            )
            for index in range(1, 22)
        ]
    )

    response = request_conversation_sessions(db, "?conversationType=TEXT&size=10")

    assert response.status_code == 200
    body = response.json()
    assert len(body["conversationSessions"]) == 10
    assert body["pagination"] == {"page": 0, "size": 10, "hasNext": True}


def test_conversation_sessions_requested_size_changes_page_offset() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = CubeOwnership(id=1)
    db.execute.return_value = conversation_result(
        *[
            (
                session(id=index, conversation_type=ConversationType.TEXT),
                message(id=index),
            )
            for index in range(11, 22)
        ]
    )

    response = request_conversation_sessions(
        db,
        "?conversationType=TEXT&page=1&size=10",
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["conversationSessions"]] == list(range(11, 21))
    assert body["pagination"] == {"page": 1, "size": 10, "hasNext": True}


def test_conversation_sessions_return_empty_list() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = CubeOwnership(id=1)
    db.execute.return_value = conversation_result()

    response = request_conversation_sessions(db)

    assert response.status_code == 200
    assert response.json() == {
        "conversationSessions": [],
        "pagination": {"page": 0, "size": 20, "hasNext": False},
    }


def test_conversation_sessions_reject_size_less_than_one_with_common_400() -> None:
    db = Mock(spec=Session)

    response = request_conversation_sessions(db, "?conversationType=TEXT&size=0")

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

    assert set(operation["responses"]) == {"200", "404"}
    assert "security" not in operation


def test_conversation_sessions_return_404_without_last_active_ownership() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = request_conversation_sessions(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CUBE_OWNERSHIP_NOT_FOUND",
        "message": "큐브 소유권 정보를 찾을 수 없습니다.",
    }
    db.execute.assert_not_called()


def test_conversation_archive_returns_saved_avatar_texts() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = CubeOwnership(id=1)
    db.scalars.return_value.all.return_value = [
        message(
            id=5006,
            conversation_session_id=1001,
            content="오늘 하루는 어땠어?",
            sent_at=datetime.fromisoformat("2026-07-29T15:30:02"),
            sequence_number=6,
            sender_type=ConversationMessageSenderType.AVATAR,
            is_text_saved=True,
            status=ConversationMessageStatus.BLOCKED,
        ),
        message(
            id=4982,
            conversation_session_id=995,
            content="오늘 무대 정말 멋졌어!",
            sent_at=datetime.fromisoformat("2026-07-28T20:10:00"),
            sequence_number=12,
            sender_type=ConversationMessageSenderType.AVATAR,
            is_text_saved=True,
        ),
    ]
    response = request_conversation_archive(db)

    assert response.status_code == 200
    assert response.json() == {
        "savedTexts": [
            {
                "id": 5006,
                "conversationSessionId": 1001,
                "content": "오늘 하루는 어땠어?",
                "sequenceNumber": 6,
                "sentAt": "2026-07-29T15:30:02",
            },
            {
                "id": 4982,
                "conversationSessionId": 995,
                "content": "오늘 무대 정말 멋졌어!",
                "sequenceNumber": 12,
                "sentAt": "2026-07-28T20:10:00",
            },
        ]
    }


def test_conversation_archive_returns_empty_list() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = CubeOwnership(id=1)
    db.scalars.return_value.all.return_value = []

    response = request_conversation_archive(db)

    assert response.status_code == 200
    assert response.json() == {"savedTexts": []}


def test_conversation_archive_returns_404_without_last_active_ownership() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = request_conversation_archive(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CUBE_OWNERSHIP_NOT_FOUND",
        "message": "큐브 소유권 정보를 찾을 수 없습니다.",
    }
    db.scalars.assert_not_called()


def test_conversation_archive_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/conversation-archive"
    ]["get"]

    assert set(operation["responses"]) == {"200", "404"}
    assert "security" not in operation


def test_delete_conversation_archive_message_sets_is_text_saved_false() -> None:
    db = Mock(spec=Session)
    conversation_message = message(
        id=5006,
        conversation_session_id=1001,
        sender_type=ConversationMessageSenderType.AVATAR,
        is_text_saved=True,
    )
    db.scalar.return_value = conversation_message

    response = delete_conversation_archive_message_request(db)

    assert response.status_code == 204
    assert response.content == b""
    assert conversation_message.is_text_saved is False
    db.commit.assert_called_once()


def test_delete_conversation_archive_message_returns_404_when_not_saved() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = delete_conversation_archive_message_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CONVERSATION_MESSAGE_NOT_FOUND",
        "message": "대화 메시지를 찾을 수 없습니다.",
    }
    db.commit.assert_not_called()


def test_delete_conversation_archive_message_rejects_invalid_path() -> None:
    db = Mock(spec=Session)

    response = delete_conversation_archive_message_request(
        db,
        conversation_message_id=0,
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.scalar.assert_not_called()


def test_delete_conversation_archive_message_rolls_back_on_commit_failure() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = message(
        id=5006,
        conversation_session_id=1001,
        sender_type=ConversationMessageSenderType.AVATAR,
        is_text_saved=True,
    )
    db.commit.side_effect = RuntimeError("db failed")

    response = delete_conversation_archive_message_request(
        db,
        raise_server_exceptions=False,
    )

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_delete_conversation_archive_message_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/conversation-messages/{conversationMessageId}/unsave"
    ]["delete"]

    assert set(operation["responses"]) == {"204", "404"}
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


def test_create_conversation_report_saves_orm_model_and_returns_204() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = message(
        id=5006,
        sender_type=ConversationMessageSenderType.AVATAR,
    )

    response = create_conversation_report_request(db)

    assert response.status_code == 204
    assert response.content == b""
    report = db.add.call_args.args[0]
    assert isinstance(report, ConversationReport)
    assert report.conversation_message_id == 5006
    assert report.reason == ConversationReportReason.INCORRECT_PERSONA
    assert report.detail_reason == "아티스트 설정과 다른 답변입니다."
    db.commit.assert_called_once()


def test_create_conversation_report_accepts_null_and_blank_detail_reason() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = message(
        id=5006,
        sender_type=ConversationMessageSenderType.AVATAR,
    )

    null_response = create_conversation_report_request(
        db,
        body={"reason": "HALLUCINATION", "detailReason": None},
    )
    blank_response = create_conversation_report_request(
        db,
        body={"reason": "INAPPROPRIATE_EXPRESSION", "detailReason": ""},
    )

    assert null_response.status_code == 204
    assert blank_response.status_code == 204
    first_report = db.add.call_args_list[0].args[0]
    second_report = db.add.call_args_list[1].args[0]
    assert first_report.detail_reason is None
    assert second_report.detail_reason == ""


def test_create_conversation_report_allows_duplicate_reports() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = message(
        id=5006,
        sender_type=ConversationMessageSenderType.AVATAR,
    )

    first_response = create_conversation_report_request(db)
    second_response = create_conversation_report_request(db)

    assert first_response.status_code == 204
    assert second_response.status_code == 204
    assert db.add.call_count == 2
    assert db.commit.call_count == 2


def test_create_conversation_report_returns_404_for_unavailable_message() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = create_conversation_report_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CONVERSATION_MESSAGE_NOT_FOUND",
        "message": "대화 메시지를 찾을 수 없습니다.",
    }
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_conversation_report_rejects_detail_reason_over_200_characters() -> None:
    db = Mock(spec=Session)

    response = create_conversation_report_request(
        db,
        body={"reason": "INCORRECT_PERSONA", "detailReason": "가" * 201},
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.scalar.assert_not_called()


def test_create_conversation_report_rejects_invalid_reason() -> None:
    db = Mock(spec=Session)

    response = create_conversation_report_request(
        db,
        body={"reason": "IMPERSONATION_OR_PRIVATE", "detailReason": None},
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.scalar.assert_not_called()


def test_create_conversation_report_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = message(
        id=5006,
        sender_type=ConversationMessageSenderType.AVATAR,
    )
    db.commit.side_effect = RuntimeError("db failed")

    response = create_conversation_report_request(
        db,
        raise_server_exceptions=False,
    )

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_create_conversation_report_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/conversation-messages/{conversationMessageId}/reports"
    ]["post"]

    assert set(operation["responses"]) == {"204", "404"}
    assert operation["tags"] == ["conversation"]
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
                    "sentAt": "2026-07-29T12:25:00",
                },
                {
                    "id": 5002,
                    "senderType": "USER",
                    "content": "나 지금 카페에서 공부하고 있어.",
                    "sequenceNumber": 2,
                    "sentAt": "2026-07-29T12:23:30",
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

    statement = db.scalar.call_args.args[0]
    query = str(statement)
    assert "cube_ownership.user_id" in query
    assert "cube_ownership.ownership_status" in query
    assert "cube_ownership.is_last_accessed" in query


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


def test_reply_conversation_message_saves_user_and_avatar_messages() -> None:
    db = Mock(spec=Session)
    conversation_session = session(
        id=1001,
        conversation_type=ConversationType.TEXT,
    )
    conversation_session.cube_ownership_id = 1
    db.scalar.side_effect = [conversation_session, 12]

    def set_message_ids() -> None:
        for index, inserted in enumerate(db.add.call_args_list, start=5025):
            inserted.args[0].id = index

    db.flush.side_effect = set_message_ids

    with patch(
        "app.services.conversation.generate_avatar_reply",
        return_value="오늘 연습하고 있었어! 너는 오늘 하루 어땠어?",
    ):
        response = reply_conversation_message_request(db)

    assert response.status_code == 201
    body = response.json()
    assert body["userMessage"] == {
        "id": 5025,
        "senderType": "USER",
        "content": "오늘 뭐 하고 있었어?",
        "imageUrls": [],
        "sequenceNumber": 13,
        "sentAt": body["userMessage"]["sentAt"],
    }
    assert body["avatarMessage"] == {
        "id": 5026,
        "senderType": "AVATAR",
        "content": "오늘 연습하고 있었어! 너는 오늘 하루 어땠어?",
        "sequenceNumber": 14,
        "sentAt": body["avatarMessage"]["sentAt"],
    }

    user_message = db.add.call_args_list[0].args[0]
    avatar_message = db.add.call_args_list[1].args[0]
    assert isinstance(user_message, AvatarConversationMessage)
    assert isinstance(avatar_message, AvatarConversationMessage)
    assert user_message.conversation_session_id == 1001
    assert user_message.sender_type == ConversationMessageSenderType.USER
    assert user_message.content == "오늘 뭐 하고 있었어?"
    assert user_message.sequence_number == 13
    assert user_message.is_text_saved is False
    assert user_message.status == ConversationMessageStatus.ALLOWED
    assert user_message.violation_type is None
    assert avatar_message.sender_type == ConversationMessageSenderType.AVATAR
    assert avatar_message.sequence_number == 14
    db.commit.assert_called_once()


def test_reply_conversation_message_allows_not_active_session() -> None:
    db = Mock(spec=Session)
    conversation_session = session(
        id=1001,
        conversation_type=ConversationType.TEXT,
    )
    conversation_session.status = AvatarConversationSessionStatus.NOT_ACTIVE
    conversation_session.ended_at = datetime(2026, 7, 29, 18, 0, 0)  # noqa: DTZ001
    db.scalar.side_effect = [conversation_session, 0]
    db.flush.side_effect = lambda: [
        setattr(call.args[0], "id", index)
        for index, call in enumerate(db.add.call_args_list, start=1)
    ]

    with patch(
        "app.services.conversation.generate_avatar_reply",
        return_value="잘 못 들었어. 다시 한 번 말해줄래?",
    ) as generate_reply:
        response = reply_conversation_message_request(
            db,
            conversation_session_id=1001,
            body={"content": "다시 이어서 얘기하자"},
        )

    assert response.status_code == 201
    generate_reply.assert_called_once_with("다시 이어서 얘기하자", [])
    assert response.json()["userMessage"]["content"] == "다시 이어서 얘기하자"
    assert response.json()["avatarMessage"]["content"] == (
        "잘 못 들었어. 다시 한 번 말해줄래?"
    )
    assert conversation_session.status == AvatarConversationSessionStatus.ACTIVE
    assert conversation_session.ended_at == datetime(  # noqa: DTZ001
        2026, 7, 29, 18, 0, 0
    )


def test_reply_conversation_message_allows_active_voice_session() -> None:
    db = Mock(spec=Session)
    conversation_session = session(
        id=12,
        conversation_type=ConversationType.VOICE,
    )
    db.scalar.side_effect = [conversation_session, 0]
    db.flush.side_effect = lambda: [
        setattr(call.args[0], "id", index)
        for index, call in enumerate(db.add.call_args_list, start=1)
    ]

    with patch(
        "app.services.conversation.generate_avatar_reply",
        return_value="안녕! 오늘 기분은 어때?",
    ) as generate_reply:
        response = reply_conversation_message_request(
            db,
            conversation_session_id=12,
            body={"content": "안녕"},
        )

    assert response.status_code == 201
    generate_reply.assert_called_once_with("안녕", [])
    assert response.json()["userMessage"]["content"] == "안녕"
    assert response.json()["avatarMessage"]["content"] == (
        "안녕! 오늘 기분은 어때?"
    )
    assert all(
        call.args[0].conversation_session_id == 12
        for call in db.add.call_args_list
    )
    db.commit.assert_called_once()


def test_reply_conversation_message_returns_404_for_not_active_voice_session() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = reply_conversation_message_request(
        db,
        conversation_session_id=12,
        body={"content": "안녕"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "CONVERSATION_SESSION_NOT_FOUND",
        "message": "대화 세션을 찾을 수 없습니다.",
    }
    query = str(db.scalar.call_args.args[0])
    assert "avatar_conversation_session.conversation_type" in query
    assert "avatar_conversation_session.status" in query
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_reply_conversation_message_rejects_blank_content_with_common_400() -> None:
    db = Mock(spec=Session)

    response = reply_conversation_message_request(
        db,
        body={"content": "   \n"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.scalar.assert_not_called()


def test_reply_conversation_message_passes_image_urls_to_gpt() -> None:
    db = Mock(spec=Session)
    conversation_session = session(
        id=1001,
        conversation_type=ConversationType.TEXT,
    )
    db.scalar.side_effect = [conversation_session, None, None, None, 12]

    def set_message_ids() -> None:
        for index, inserted in enumerate(db.add.call_args_list, start=5025):
            inserted.args[0].id = index

    db.flush.side_effect = set_message_ids
    image_urls = [
        "https://haniumstorage.blob.core.windows.net/hanium/stage_capture/1/1/a.jpg",
        "https://haniumstorage.blob.core.windows.net/hanium/track_capture/1/2/b.png",
    ]

    with patch(
        "app.services.conversation.generate_avatar_reply",
        return_value="사진까지 보니까 더 생생하다!",
    ) as generate_reply:
        response = reply_conversation_message_request(
            db,
            body={"content": "이 사진들 봐줘", "imageUrls": image_urls},
        )

    assert response.status_code == 201
    generate_reply.assert_called_once_with("이 사진들 봐줘", image_urls)
    body = response.json()
    assert body["userMessage"]["imageUrls"] == image_urls
    assert "imageUrls" not in body["avatarMessage"]
    assert db.add.call_args_list[0].args[0].content == "이 사진들 봐줘"
    db.commit.assert_called_once()


def test_reply_conversation_message_rejects_more_than_five_images() -> None:
    db = Mock(spec=Session)

    response = reply_conversation_message_request(
        db,
        body={
            "content": "사진이 많아",
            "imageUrls": [f"https://example.com/{index}.jpg" for index in range(6)],
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.scalar.assert_not_called()


def test_reply_conversation_message_returns_404_for_deleted_image_url() -> None:
    db = Mock(spec=Session)
    db.scalar.side_effect = [
        session(id=1001, conversation_type=ConversationType.TEXT),
        3001,
    ]

    with patch("app.services.conversation.generate_avatar_reply") as generate_reply:
        response = reply_conversation_message_request(
            db,
            body={
                "content": "삭제된 사진이야?",
                "imageUrls": [
                    "https://haniumstorage.blob.core.windows.net/hanium/stage_capture/1/1/deleted.jpg"
                ],
            },
        )

    assert response.status_code == 404
    assert response.json() == {
        "code": "CONVERSATION_IMAGE_NOT_FOUND",
        "message": "전송할 이미지를 찾을 수 없습니다.",
    }
    generate_reply.assert_not_called()
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_reply_conversation_message_returns_404_for_unknown_or_deleted_session() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = reply_conversation_message_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CONVERSATION_SESSION_NOT_FOUND",
        "message": "대화 세션을 찾을 수 없습니다.",
    }
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_reply_conversation_message_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    db.scalar.side_effect = [
        session(id=1001, conversation_type=ConversationType.TEXT),
        0,
    ]
    db.commit.side_effect = RuntimeError("db failed")

    with patch(
        "app.services.conversation.generate_avatar_reply",
        return_value="좋아, 계속 얘기해줘!",
    ):
        response = reply_conversation_message_request(
            db,
            raise_server_exceptions=False,
        )

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_reply_conversation_message_does_not_save_when_gpt_fails() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = session(id=1001, conversation_type=ConversationType.TEXT)

    with patch(
        "app.services.conversation.generate_avatar_reply",
        side_effect=RuntimeError("openai failed"),
    ):
        response = reply_conversation_message_request(
            db,
            raise_server_exceptions=False,
        )

    assert response.status_code == 500
    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.rollback.assert_not_called()


def test_reply_conversation_message_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/conversation-sessions/{conversationSessionId}/messages"
    ]["post"]

    assert set(operation["responses"]) == {"201", "404"}
    assert "security" not in operation


def test_update_text_conversation_session_sets_title_and_ends_session() -> None:
    db = Mock(spec=Session)
    conversation_session = session(
        id=1001,
        conversation_type=ConversationType.TEXT,
        title=None,
    )
    messages = [
        message(
            id=5001,
            content="오늘 뭐 했어?",
            sequence_number=1,
            sender_type=ConversationMessageSenderType.USER,
        ),
        message(
            id=5002,
            content="연습하고 있었어!",
            sequence_number=2,
            sender_type=ConversationMessageSenderType.AVATAR,
        ),
    ]
    db.scalar.return_value = conversation_session
    db.scalars.return_value.all.return_value = messages

    with patch(
        "app.services.conversation.generate_conversation_title",
        return_value="오늘의 연습 이야기",
    ) as generate_title:
        response = update_conversation_session_request(db)

    assert response.status_code == 204
    generate_title.assert_called_once_with(messages)
    assert conversation_session.conversation_title == "오늘의 연습 이야기"
    assert isinstance(conversation_session.ended_at, datetime)
    assert conversation_session.ended_at.tzinfo is None
    assert conversation_session.status == AvatarConversationSessionStatus.NOT_ACTIVE
    assert conversation_session.audio_url is None
    assert conversation_session.audio_duration_seconds is None
    db.commit.assert_called_once()


def test_update_conversation_session_accepts_no_multipart_and_empty_messages() -> None:
    db = Mock(spec=Session)
    conversation_session = session(
        id=1001,
        conversation_type=ConversationType.TEXT,
        title=None,
    )
    db.scalar.return_value = conversation_session
    db.scalars.return_value.all.return_value = []

    with patch(
        "app.services.conversation.generate_conversation_title",
    ) as generate_title:
        response = update_conversation_session_request(db)

    assert response.status_code == 204
    generate_title.assert_not_called()
    assert conversation_session.conversation_title is None
    assert conversation_session.status == AvatarConversationSessionStatus.NOT_ACTIVE
    assert isinstance(conversation_session.ended_at, datetime)


def test_update_voice_conversation_session_uploads_audio_and_saves_url() -> None:
    db = Mock(spec=Session)
    conversation_session = session(
        id=1101,
        conversation_type=ConversationType.VOICE,
        title="기존 제목",
    )
    conversation_session.status = AvatarConversationSessionStatus.NOT_ACTIVE
    db.scalar.return_value = conversation_session
    db.scalars.return_value.all.return_value = [
        message(id=1, content="음성 대화", sequence_number=1)
    ]

    with (
        patch(
            "app.services.conversation.generate_conversation_title",
        ) as generate_title,
        patch(
            "app.services.conversation.upload_conversation_audio",
            return_value="https://storage.example.com/conversation_audio/1/1101/a.m4a",
        ) as upload_audio,
    ):
        response = update_conversation_session_request(
            db,
            conversation_session_id=1101,
            data={"audioDurationSeconds": "300"},
            files={
                "audio": (
                    "voice.m4a",
                    b"audio-bytes",
                    "audio/mp4",
                )
            },
        )

    assert response.status_code == 204
    generate_title.assert_not_called()
    upload_audio.assert_called_once()
    assert upload_audio.call_args.kwargs["content_type"] == "audio/mp4"
    assert upload_audio.call_args.kwargs["user_id"] == 1
    assert upload_audio.call_args.kwargs["conversation_session_id"] == 1101
    assert conversation_session.conversation_title == "기존 제목"
    assert conversation_session.audio_url == (
        "https://storage.example.com/conversation_audio/1/1101/a.m4a"
    )
    assert conversation_session.audio_duration_seconds == 300
    assert conversation_session.status == AvatarConversationSessionStatus.NOT_ACTIVE
    assert isinstance(conversation_session.ended_at, datetime)


def test_update_voice_conversation_session_returns_common_400_without_audio() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = session(
        id=1101,
        conversation_type=ConversationType.VOICE,
    )

    response = update_conversation_session_request(
        db,
        conversation_session_id=1101,
        files={
            "audio": (
                "voice.m4a",
                b"audio-bytes",
                "audio/mp4",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.commit.assert_not_called()


def test_update_voice_conversation_session_returns_common_400_for_invalid_audio_type() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = session(
        id=1101,
        conversation_type=ConversationType.VOICE,
    )

    response = update_conversation_session_request(
        db,
        conversation_session_id=1101,
        data={"audioDurationSeconds": "300"},
        files={
            "audio": (
                "voice.txt",
                b"not-audio",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }
    db.commit.assert_not_called()


def test_update_conversation_session_returns_404_for_unknown_or_deleted_session() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = update_conversation_session_request(db)

    assert response.status_code == 404
    assert response.json() == {
        "code": "CONVERSATION_SESSION_NOT_FOUND",
        "message": "대화 세션을 찾을 수 없습니다.",
    }
    db.commit.assert_not_called()


def test_update_conversation_session_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = session(
        id=1001,
        conversation_type=ConversationType.TEXT,
        title="기존 제목",
    )
    db.scalars.return_value.all.return_value = []
    db.commit.side_effect = RuntimeError("db failed")

    response = update_conversation_session_request(db, raise_server_exceptions=False)

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_update_conversation_session_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/users/me/conversation-sessions/{conversationSessionId}"
    ]["patch"]

    assert set(operation["responses"]) == {"204", "404"}
    assert "security" not in operation
