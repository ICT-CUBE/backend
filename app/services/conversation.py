"""텍스트·음성 대화 목록 조회 로직."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ApiError
from app.models.conversation import (
    AvatarConversationMessage,
    AvatarConversationSession,
)
from app.models.cube import CubeOwnership
from app.models.enums import (
    AvatarConversationSessionStatus,
    ConversationMessageSenderType,
    ConversationType,
    OwnershipStatus,
)
from app.schemas.conversation import (
    ConversationDetailMessageResponse,
    ConversationDetailResponse,
    ConversationDetailSessionResponse,
    ConversationLastMessageResponse,
    ConversationMessageSaveItemResponse,
    ConversationMessageSaveResponse,
    ConversationPaginationResponse,
    ConversationSessionCreateItemResponse,
    ConversationSessionCreateResponse,
    ConversationSessionResponse,
    ConversationSessionsResponse,
)

CURRENT_USER_ID = 1
CONVERSATION_PAGE_SIZE = 20
KOREA_TIMEZONE = timezone(timedelta(hours=9))


def _kst_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=KOREA_TIMEZONE)
    return value.astimezone(KOREA_TIMEZONE)


def get_conversation_sessions(
    *,
    db: Session,
    conversation_type: ConversationType,
    page: int,
) -> ConversationSessionsResponse:
    """마지막 메시지가 있는 대화 세션 목록을 최신순으로 반환합니다."""
    last_sequence = (
        select(
            AvatarConversationMessage.conversation_session_id.label("session_id"),
            func.max(AvatarConversationMessage.sequence_number).label("sequence_number"),
        )
        .group_by(AvatarConversationMessage.conversation_session_id)
        .subquery()
    )

    rows = db.execute(
        select(AvatarConversationSession, AvatarConversationMessage)
        .join(
            CubeOwnership,
            AvatarConversationSession.cube_ownership_id == CubeOwnership.id,
        )
        .join(
            last_sequence,
            last_sequence.c.session_id == AvatarConversationSession.id,
        )
        .join(
            AvatarConversationMessage,
            (
                AvatarConversationMessage.conversation_session_id
                == AvatarConversationSession.id
            )
            & (
                AvatarConversationMessage.sequence_number
                == last_sequence.c.sequence_number
            ),
        )
        .where(
            CubeOwnership.user_id == CURRENT_USER_ID,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            AvatarConversationSession.conversation_type == conversation_type,
            AvatarConversationSession.deleted_at.is_(None),
        )
        .order_by(AvatarConversationMessage.sent_at.desc())
        .offset(page * CONVERSATION_PAGE_SIZE)
        .limit(CONVERSATION_PAGE_SIZE + 1)
    ).all()

    page_rows = rows[:CONVERSATION_PAGE_SIZE]
    has_next = len(rows) > CONVERSATION_PAGE_SIZE

    return ConversationSessionsResponse(
        conversationSessions=[
            _conversation_session_response(
                session=session,
                last_message=last_message,
            )
            for session, last_message in page_rows
        ],
        pagination=ConversationPaginationResponse(
            page=page,
            size=CONVERSATION_PAGE_SIZE,
            hasNext=has_next,
        ),
    )


def create_conversation_session(
    *,
    db: Session,
    conversation_type: ConversationType,
) -> ConversationSessionCreateResponse:
    """현재 사용자의 활성 큐브 소유권에 새 대화 세션을 생성합니다."""
    ownership = db.scalar(
        select(CubeOwnership)
        .where(
            CubeOwnership.user_id == CURRENT_USER_ID,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .limit(1)
    )

    conversation_session = AvatarConversationSession(
        cube_ownership_id=ownership.id,
        conversation_type=conversation_type,
        started_at=datetime.now(KOREA_TIMEZONE).replace(tzinfo=None),
        ended_at=None,
        audio_url=None,
        audio_duration_seconds=None,
        conversation_title=None,
        status=AvatarConversationSessionStatus.ACTIVE,
        deleted_at=None,
    )
    try:
        db.add(conversation_session)
        db.flush()
        conversation_session_id = conversation_session.id
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ConversationSessionCreateResponse(
        conversationSession=ConversationSessionCreateItemResponse(
            id=conversation_session_id,
            conversationType=conversation_type,
        )
    )


def delete_conversation_session(
    *,
    db: Session,
    conversation_session_id: int,
) -> None:
    """대화 세션을 deleted_at 저장 방식으로 소프트 딜리트합니다."""
    conversation_session = db.scalar(
        select(AvatarConversationSession)
        .join(
            CubeOwnership,
            AvatarConversationSession.cube_ownership_id == CubeOwnership.id,
        )
        .where(
            AvatarConversationSession.id == conversation_session_id,
            CubeOwnership.user_id == CURRENT_USER_ID,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            AvatarConversationSession.deleted_at.is_(None),
        )
        .limit(1)
    )
    if conversation_session is None:
        _raise_deletable_conversation_session_not_found()

    conversation_session.deleted_at = datetime.now(KOREA_TIMEZONE).replace(tzinfo=None)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def toggle_conversation_message_save(
    *,
    db: Session,
    conversation_message_id: int,
) -> ConversationMessageSaveResponse:
    """아바타 텍스트 대화 메시지의 보관 여부를 토글합니다."""
    row = db.execute(
        select(AvatarConversationMessage, AvatarConversationSession)
        .join(
            AvatarConversationSession,
            AvatarConversationMessage.conversation_session_id
            == AvatarConversationSession.id,
        )
        .join(
            CubeOwnership,
            AvatarConversationSession.cube_ownership_id == CubeOwnership.id,
        )
        .where(
            AvatarConversationMessage.id == conversation_message_id,
            CubeOwnership.user_id == CURRENT_USER_ID,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            AvatarConversationSession.deleted_at.is_(None),
        )
        .limit(1)
    ).first()
    if row is None:
        _raise_conversation_message_not_found()

    conversation_message, conversation_session = row
    if conversation_session.conversation_type == ConversationType.VOICE:
        raise ApiError(
            status_code=404,
            code="VOICE_CONVERSATION_MESSAGE_SAVE_NOT_AVAILABLE",
            message="음성 대화는 보관이 불가합니다.",
        )
    if conversation_message.sender_type == ConversationMessageSenderType.USER:
        raise ApiError(
            status_code=404,
            code="USER_CONVERSATION_MESSAGE_SAVE_NOT_AVAILABLE",
            message="사용자 대화는 보관이 불가합니다.",
        )

    conversation_message.is_text_saved = not conversation_message.is_text_saved
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ConversationMessageSaveResponse(
        conversationMessage=ConversationMessageSaveItemResponse(
            id=conversation_message.id,
            isTextSaved=conversation_message.is_text_saved,
        )
    )


def get_conversation_session_detail(
    *,
    db: Session,
    conversation_session_id: int,
) -> ConversationDetailResponse:
    """텍스트 대화 세션의 전체 메시지를 sequenceNumber 내림차순으로 반환합니다."""
    session = db.scalar(
        select(AvatarConversationSession)
        .join(
            CubeOwnership,
            AvatarConversationSession.cube_ownership_id == CubeOwnership.id,
        )
        .where(
            AvatarConversationSession.id == conversation_session_id,
            CubeOwnership.user_id == CURRENT_USER_ID,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            AvatarConversationSession.deleted_at.is_(None),
        )
        .limit(1)
    )
    if session is None:
        _raise_conversation_session_not_found()

    if session.conversation_type == ConversationType.VOICE:
        raise ApiError(
            status_code=404,
            code="VOICE_CONVERSATION_DETAIL_NOT_AVAILABLE",
            message="음성 대화는 세션 상세 조회가 불가능합니다.",
        )

    messages = db.scalars(
        select(AvatarConversationMessage)
        .where(AvatarConversationMessage.conversation_session_id == session.id)
        .order_by(AvatarConversationMessage.sequence_number.desc())
    ).all()
    if not messages:
        _raise_conversation_session_not_found()

    return ConversationDetailResponse(
        conversationSession=ConversationDetailSessionResponse(
            id=session.id,
            messages=[
                ConversationDetailMessageResponse(
                    id=message.id,
                    senderType=message.sender_type.value,
                    content=message.content,
                    sequenceNumber=message.sequence_number,
                    sentAt=_kst_datetime(message.sent_at),
                )
                for message in messages
            ],
        )
    )


def _raise_conversation_session_not_found() -> None:
    raise ApiError(
        status_code=404,
        code="CONVERSATION_SESSION_NOT_FOUND",
        message="대화 세션을 찾을 수 없습니다.",
    )


def _raise_deletable_conversation_session_not_found() -> None:
    raise ApiError(
        status_code=404,
        code="CONVERSATION_SESSION_NOT_FOUND",
        message="삭제할 대화 세션을 찾을 수 없습니다.",
    )


def _raise_conversation_message_not_found() -> None:
    raise ApiError(
        status_code=404,
        code="CONVERSATION_MESSAGE_NOT_FOUND",
        message="대화 메시지를 찾을 수 없습니다.",
    )


def _conversation_session_response(
    *,
    session: AvatarConversationSession,
    last_message: AvatarConversationMessage,
) -> ConversationSessionResponse:
    content = (
        last_message.content
        if session.conversation_type == ConversationType.TEXT
        else None
    )
    return ConversationSessionResponse(
        id=session.id,
        conversationType=session.conversation_type,
        conversationTitle=session.conversation_title,
        audioUrl=session.audio_url,
        audioDurationSeconds=session.audio_duration_seconds,
        lastMessage=ConversationLastMessageResponse(
            id=last_message.id,
            content=content,
            sentAt=_kst_datetime(last_message.sent_at),
        ),
    )
