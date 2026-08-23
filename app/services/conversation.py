"""텍스트·음성 대화 목록 조회 로직."""

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import BinaryIO, NoReturn, cast

from openai import OpenAI
from openai.types.responses import (
    EasyInputMessageParam,
    ResponseInputContentParam,
    ResponseInputParam,
)
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ApiError
from app.models.avatar import AvatarInteractionPicture
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
    OwnershipStatus,
)
from app.models.stage import StageCapture
from app.models.track import TrackCapture
from app.schemas.conversation import (
    ConversationArchiveItemResponse,
    ConversationArchiveResponse,
    ConversationDetailMessageResponse,
    ConversationDetailResponse,
    ConversationDetailSessionResponse,
    ConversationLastMessageResponse,
    ConversationMessageReplyItemResponse,
    ConversationMessageReplyRequest,
    ConversationMessageReplyResponse,
    ConversationMessageSaveItemResponse,
    ConversationMessageSaveResponse,
    ConversationPaginationResponse,
    ConversationSessionCreateItemResponse,
    ConversationSessionCreateResponse,
    ConversationSessionResponse,
    ConversationSessionsResponse,
)
from app.services.blob_storage import (
    normalize_audio_content_type,
    upload_conversation_audio,
)

CONVERSATION_PAGE_SIZE = 20
KOREA_TIMEZONE = timezone(timedelta(hours=9))
JENNIE_CONVERSATION_SYSTEM_PROMPT = """
너는 아티스트 제니이고, 사용자와 1대1로 자연스럽게 대화하는 상황이다.
친근하고 짧게 한국어로 답하되, 팬과 편하게 말하는 분위기를 유지한다.
실제 사적인 일정, 확인되지 않은 사실, 민감한 개인정보는 지어내지 않는다.
사용자 입력이 빈 문자열이거나 공백/줄바꿈뿐이면 당황하지 말고 자연스럽게
"잘 못 들었어. 다시 한 번 말해줄래?" 같은 뉘앙스로 답한다.
""".strip()
CONVERSATION_TITLE_SYSTEM_PROMPT = """
너는 대화 기록을 보고 목록에 표시할 짧은 제목을 만드는 역할이다.
제목은 한국어로 20자 이내, 따옴표 없이 한 줄로만 답한다.
대화의 핵심 상황이나 주제를 자연스럽게 요약한다.
""".strip()


def get_conversation_sessions(
    *,
    db: Session,
    current_user_id: int,
    conversation_type: ConversationType,
    page: int,
    size: int,
) -> ConversationSessionsResponse:
    """마지막 메시지가 있는 대화 세션 목록을 최신순으로 반환합니다."""
    ownership = db.scalar(
        select(CubeOwnership)
        .where(
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .limit(1)
    )
    if ownership is None:
        raise ApiError(
            status_code=404,
            code="CUBE_OWNERSHIP_NOT_FOUND",
            message="큐브 소유권 정보를 찾을 수 없습니다.",
        )

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
            AvatarConversationSession.cube_ownership_id == ownership.id,
            AvatarConversationSession.conversation_type == conversation_type,
            AvatarConversationSession.deleted_at.is_(None),
        )
        .order_by(AvatarConversationMessage.sent_at.desc())
        .offset(page * size)
        .limit(size + 1)
    ).all()

    page_rows = rows[:size]
    has_next = len(rows) > size

    return ConversationSessionsResponse(
        conversation_sessions=[
            _conversation_session_response(
                session=session,
                last_message=last_message,
            )
            for session, last_message in page_rows
        ],
        pagination=ConversationPaginationResponse(
            page=page,
            size=size,
            has_next=has_next,
        ),
    )


def get_conversation_archive(
    *,
    db: Session,
    current_user_id: int,
) -> ConversationArchiveResponse:
    """마지막 접근 활성 큐브에 보관된 아바타 텍스트를 최신순 반환합니다."""
    ownership = db.scalar(
        select(CubeOwnership)
        .where(
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .limit(1)
    )
    if ownership is None:
        raise ApiError(
            status_code=404,
            code="CUBE_OWNERSHIP_NOT_FOUND",
            message="큐브 소유권 정보를 찾을 수 없습니다.",
        )

    saved_messages = db.scalars(
        select(AvatarConversationMessage)
        .join(
            AvatarConversationSession,
            AvatarConversationMessage.conversation_session_id
            == AvatarConversationSession.id,
        )
        .where(
            AvatarConversationSession.cube_ownership_id == ownership.id,
            AvatarConversationSession.conversation_type == ConversationType.TEXT,
            AvatarConversationSession.deleted_at.is_(None),
            AvatarConversationMessage.sender_type
            == ConversationMessageSenderType.AVATAR,
            AvatarConversationMessage.is_text_saved.is_(True),
        )
        .order_by(
            AvatarConversationMessage.sent_at.desc(),
            AvatarConversationMessage.id.desc(),
        )
    ).all()

    return ConversationArchiveResponse(
        saved_texts=[
            ConversationArchiveItemResponse(
                id=message.id,
                conversation_session_id=message.conversation_session_id,
                content=message.content,
                sequence_number=message.sequence_number,
                sent_at=message.sent_at,
            )
            for message in saved_messages
        ]
    )


def unsave_conversation_archive_message(
    *,
    db: Session,
    current_user_id: int,
    conversation_message_id: int,
) -> None:
    """마지막 접근 활성 큐브의 보관 메시지를 보관 해제합니다."""
    conversation_message = db.scalar(
        select(AvatarConversationMessage)
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
            AvatarConversationMessage.is_text_saved.is_(True),
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .limit(1)
    )
    if conversation_message is None:
        _raise_conversation_message_not_found()

    conversation_message.is_text_saved = False
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def create_conversation_session(
    *,
    db: Session,
    current_user_id: int,
    conversation_type: ConversationType,
) -> ConversationSessionCreateResponse:
    """현재 사용자의 활성 큐브 소유권에 새 대화 세션을 생성합니다."""
    ownership = db.scalar(
        select(CubeOwnership)
        .where(
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .limit(1)
    )
    if ownership is None:
        raise ApiError(
            status_code=404,
            code="CUBE_OWNERSHIP_NOT_FOUND",
            message="큐브 소유권 정보를 찾을 수 없습니다.",
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
        conversation_session=ConversationSessionCreateItemResponse(
            id=conversation_session_id,
            conversation_type=conversation_type,
        )
    )


def delete_conversation_session(
    *,
    db: Session,
    current_user_id: int,
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
            CubeOwnership.user_id == current_user_id,
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
    current_user_id: int,
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
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            AvatarConversationSession.deleted_at.is_(None),
        )
        .limit(1)
    ).first()
    if row is None:
        _raise_conversation_message_not_found()

    conversation_message, conversation_session = cast(
        tuple[AvatarConversationMessage, AvatarConversationSession],
        row,
    )
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
        conversation_message=ConversationMessageSaveItemResponse(
            id=conversation_message.id,
            is_text_saved=conversation_message.is_text_saved,
        )
    )


def create_conversation_report(
    *,
    db: Session,
    current_user_id: int,
    conversation_message_id: int,
    reason: ConversationReportReason,
    detail_reason: str | None,
) -> None:
    """현재 사용자의 아바타 대화 메시지에 대한 오류 신고를 저장합니다."""
    conversation_message = db.scalar(
        select(AvatarConversationMessage)
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
            AvatarConversationMessage.sender_type
            == ConversationMessageSenderType.AVATAR,
            CubeOwnership.user_id == current_user_id,
            AvatarConversationSession.deleted_at.is_(None),
        )
        .limit(1)
    )
    if conversation_message is None:
        _raise_conversation_message_not_found()

    # 같은 메시지에 여러 번 신고할 수 있으므로 기존 신고는 조회하지 않습니다.
    conversation_report = ConversationReport(
        conversation_message_id=conversation_message.id,
        reason=reason,
        detail_reason=detail_reason,
    )
    try:
        db.add(conversation_report)
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_conversation_session_detail(
    *,
    db: Session,
    current_user_id: int,
    conversation_session_id: int,
) -> ConversationDetailResponse:
    """텍스트 대화 세션의 전체 메시지를 sequenceNumber 내림차순으로 반환합니다."""
    conversation_session = db.scalar(
        select(AvatarConversationSession)
        .join(
            CubeOwnership,
            AvatarConversationSession.cube_ownership_id == CubeOwnership.id,
        )
        .where(
            AvatarConversationSession.id == conversation_session_id,
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
            AvatarConversationSession.deleted_at.is_(None),
        )
        .limit(1)
    )
    if conversation_session is None:
        _raise_conversation_session_not_found()

    if conversation_session.conversation_type == ConversationType.VOICE:
        raise ApiError(
            status_code=404,
            code="VOICE_CONVERSATION_DETAIL_NOT_AVAILABLE",
            message="음성 대화는 세션 상세 조회가 불가능합니다.",
        )

    messages = db.scalars(
        select(AvatarConversationMessage)
        .where(
            AvatarConversationMessage.conversation_session_id
            == conversation_session.id
        )
        .order_by(AvatarConversationMessage.sequence_number.desc())
    ).all()
    if not messages:
        _raise_conversation_session_not_found()

    return ConversationDetailResponse(
        conversation_session=ConversationDetailSessionResponse(
            id=conversation_session.id,
            messages=[
                ConversationDetailMessageResponse(
                    id=message.id,
                    sender_type=message.sender_type.value,
                    content=message.content,
                    sequence_number=message.sequence_number,
                    sent_at=message.sent_at,
                )
                for message in messages
            ],
        )
    )


def reply_to_conversation_message(
    *,
    db: Session,
    current_user_id: int,
    conversation_session_id: int,
    body: ConversationMessageReplyRequest,
) -> ConversationMessageReplyResponse:
    """사용자 발화를 GPT로 처리하고 USER/AVATAR 메시지를 함께 저장합니다."""
    conversation_session = db.scalar(
        select(AvatarConversationSession)
        .join(
            CubeOwnership,
            AvatarConversationSession.cube_ownership_id == CubeOwnership.id,
        )
        .where(
            AvatarConversationSession.id == conversation_session_id,
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            AvatarConversationSession.deleted_at.is_(None),
            or_(
                AvatarConversationSession.status
                == AvatarConversationSessionStatus.ACTIVE,
                and_(
                    AvatarConversationSession.conversation_type == ConversationType.TEXT,
                    AvatarConversationSession.status
                    == AvatarConversationSessionStatus.NOT_ACTIVE,
                ),
            ),
        )
        .limit(1)
    )
    if conversation_session is None:
        _raise_conversation_session_not_found()

    if conversation_session.conversation_type == ConversationType.VOICE:
        _raise_conversation_session_not_found()

    if conversation_session.status == AvatarConversationSessionStatus.NOT_ACTIVE:
        conversation_session.status = AvatarConversationSessionStatus.ACTIVE

    if _has_deleted_conversation_image_url(db=db, image_urls=body.image_urls):
        _raise_conversation_image_not_found()

    avatar_reply = generate_avatar_reply(body.content, body.image_urls)
    now = datetime.now(KOREA_TIMEZONE).replace(tzinfo=None)
    last_sequence_number = _last_conversation_sequence_number(
        db=db,
        conversation_session_id=conversation_session.id,
    )

    user_message = AvatarConversationMessage(
        conversation_session_id=conversation_session.id,
        sender_type=ConversationMessageSenderType.USER,
        content=body.content,
        sequence_number=last_sequence_number + 1,
        is_text_saved=False,
        status=ConversationMessageStatus.ALLOWED,
        violation_type=None,
        sent_at=now,
    )
    avatar_message = AvatarConversationMessage(
        conversation_session_id=conversation_session.id,
        sender_type=ConversationMessageSenderType.AVATAR,
        content=avatar_reply,
        sequence_number=last_sequence_number + 2,
        is_text_saved=False,
        status=ConversationMessageStatus.ALLOWED,
        violation_type=None,
        sent_at=now,
    )

    try:
        db.add(user_message)
        db.add(avatar_message)
        db.flush()
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ConversationMessageReplyResponse(
        user_message=_conversation_reply_message_response(
            user_message,
            image_urls=body.image_urls,
        ),
        avatar_message=_conversation_reply_message_response(avatar_message),
    )


def save_conversation_session(
    *,
    db: Session,
    current_user_id: int,
    conversation_session_id: int,
    audio_file: BinaryIO | None,
    audio_content_type: str | None,
    audio_duration_seconds: int | None,
) -> None:
    """대화 세션 종료 정보를 저장하고 필요하면 제목을 생성합니다."""
    conversation_session = db.scalar(
        select(AvatarConversationSession)
        .join(
            CubeOwnership,
            AvatarConversationSession.cube_ownership_id == CubeOwnership.id,
        )
        .where(
            AvatarConversationSession.id == conversation_session_id,
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            AvatarConversationSession.deleted_at.is_(None),
        )
        .limit(1)
    )
    if conversation_session is None:
        _raise_conversation_session_not_found()

    audio_url, stored_audio_duration_seconds = _conversation_audio_values(
        conversation_session=conversation_session,
        current_user_id=current_user_id,
        audio_file=audio_file,
        audio_content_type=audio_content_type,
        audio_duration_seconds=audio_duration_seconds,
    )

    first_messages = db.scalars(
        select(AvatarConversationMessage)
        .where(
            AvatarConversationMessage.conversation_session_id
            == conversation_session.id
        )
        .order_by(AvatarConversationMessage.sequence_number.asc())
        .limit(2)
    ).all()

    if conversation_session.conversation_title is None and first_messages:
        conversation_session.conversation_title = generate_conversation_title(
            first_messages
        )

    now = datetime.now(KOREA_TIMEZONE).replace(tzinfo=None)
    conversation_session.ended_at = now
    conversation_session.status = AvatarConversationSessionStatus.NOT_ACTIVE

    conversation_session.audio_url = audio_url
    conversation_session.audio_duration_seconds = stored_audio_duration_seconds

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def generate_avatar_reply(user_content: str, image_urls: list[str] | None = None) -> str:
    """OpenAI GPT를 호출해 제니 페르소나의 응답 문장을 생성합니다."""
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    response_input = _avatar_reply_response_input(
        user_content=user_content,
        image_urls=image_urls or [],
    )
    response = client.responses.create(
        model=settings.openai_model,
        input=response_input,
    )
    return response.output_text.strip()


def _conversation_audio_values(
    *,
    conversation_session: AvatarConversationSession,
    current_user_id: int,
    audio_file: BinaryIO | None,
    audio_content_type: str | None,
    audio_duration_seconds: int | None,
) -> tuple[str | None, int | None]:
    if conversation_session.conversation_type != ConversationType.VOICE:
        return None, None

    if audio_file is None or audio_duration_seconds is None:
        _raise_invalid_request()

    normalized_content_type = normalize_audio_content_type(audio_content_type)
    if normalized_content_type is None:
        _raise_invalid_request()

    try:
        audio_url = upload_conversation_audio(
            file=audio_file,
            content_type=normalized_content_type,
            user_id=current_user_id,
            conversation_session_id=conversation_session.id,
        )
    except Exception as exc:
        raise ApiError(
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="서버 내부 오류가 발생했습니다.",
        ) from exc

    return audio_url, audio_duration_seconds


def generate_conversation_title(
    messages: Sequence[AvatarConversationMessage],
) -> str:
    """첫 대화 2개를 바탕으로 대화 제목을 생성합니다."""
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    conversation_text = "\n".join(
        f"{message.sender_type.value}: {message.content}" for message in messages
    )
    response = client.responses.create(
        model=settings.openai_model,
        input=[
            {
                "role": "system",
                "content": CONVERSATION_TITLE_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": conversation_text,
            },
        ],
    )
    return response.output_text.strip()


def _avatar_reply_response_input(
    *,
    user_content: str,
    image_urls: list[str],
) -> ResponseInputParam:
    system_message: EasyInputMessageParam = {
        "role": "system",
        "content": JENNIE_CONVERSATION_SYSTEM_PROMPT,
    }
    if not image_urls:
        user_message: EasyInputMessageParam = {
            "role": "user",
            "content": user_content,
        }
        return [system_message, user_message]

    user_content_parts: list[ResponseInputContentParam] = [
        {"type": "input_text", "text": user_content}
    ]
    user_content_parts.extend(
        {
            "type": "input_image",
            "image_url": image_url,
            "detail": "auto",
        }
        for image_url in image_urls
    )
    user_message = {
        "role": "user",
        "content": user_content_parts,
    }
    return [system_message, user_message]


def _raise_conversation_session_not_found() -> NoReturn:
    raise ApiError(
        status_code=404,
        code="CONVERSATION_SESSION_NOT_FOUND",
        message="대화 세션을 찾을 수 없습니다.",
    )


def _raise_deletable_conversation_session_not_found() -> NoReturn:
    raise ApiError(
        status_code=404,
        code="CONVERSATION_SESSION_NOT_FOUND",
        message="삭제할 대화 세션을 찾을 수 없습니다.",
    )


def _raise_conversation_message_not_found() -> NoReturn:
    raise ApiError(
        status_code=404,
        code="CONVERSATION_MESSAGE_NOT_FOUND",
        message="대화 메시지를 찾을 수 없습니다.",
    )


def _raise_conversation_image_not_found() -> NoReturn:
    raise ApiError(
        status_code=404,
        code="CONVERSATION_IMAGE_NOT_FOUND",
        message="전송할 이미지를 찾을 수 없습니다.",
    )


def _raise_invalid_request() -> NoReturn:
    raise ApiError(
        status_code=400,
        code="INVALID_REQUEST",
        message="요청값이 올바르지 않습니다.",
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
        conversation_type=session.conversation_type,
        conversation_title=session.conversation_title,
        audio_url=session.audio_url,
        audio_duration_seconds=session.audio_duration_seconds,
        last_message=ConversationLastMessageResponse(
            id=last_message.id,
            content=content,
            sent_at=last_message.sent_at,
        ),
    )


def _last_conversation_sequence_number(
    *,
    db: Session,
    conversation_session_id: int,
) -> int:
    return (
        db.scalar(
            select(func.max(AvatarConversationMessage.sequence_number)).where(
                AvatarConversationMessage.conversation_session_id
                == conversation_session_id
            )
        )
        or 0
    )


def _has_deleted_conversation_image_url(
    *,
    db: Session,
    image_urls: list[str],
) -> bool:
    if not image_urls:
        return False
    deleted_stage_capture_id = db.scalar(
        select(StageCapture.id)
        .where(
            StageCapture.stage_capture_img_url.in_(image_urls),
            StageCapture.deleted_at.is_not(None),
        )
        .limit(1)
    )
    if deleted_stage_capture_id is not None:
        return True
    deleted_track_capture_id = db.scalar(
        select(TrackCapture.id)
        .where(
            TrackCapture.track_capture_img_url.in_(image_urls),
            TrackCapture.deleted_at.is_not(None),
        )
        .limit(1)
    )
    if deleted_track_capture_id is not None:
        return True
    deleted_interaction_picture_id = db.scalar(
        select(AvatarInteractionPicture.id)
        .where(
            AvatarInteractionPicture.picture_img_url.in_(image_urls),
            AvatarInteractionPicture.deleted_at.is_not(None),
        )
        .limit(1)
    )
    return deleted_interaction_picture_id is not None


def _conversation_reply_message_response(
    message: AvatarConversationMessage,
    *,
    image_urls: list[str] | None = None,
) -> ConversationMessageReplyItemResponse:
    return ConversationMessageReplyItemResponse(
        id=message.id,
        sender_type=message.sender_type.value,
        content=message.content,
        image_urls=image_urls,
        sequence_number=message.sequence_number,
        sent_at=message.sent_at,
    )
