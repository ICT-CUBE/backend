"""대화 도메인 API 라우터."""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Path,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.models.enums import ConversationType
from app.schemas.common import ErrorResponse
from app.schemas.conversation import (
    ConversationArchiveResponse,
    ConversationDetailResponse,
    ConversationMessageReplyRequest,
    ConversationMessageReplyResponse,
    ConversationMessageSaveResponse,
    ConversationReportCreateRequest,
    ConversationSessionCreateRequest,
    ConversationSessionCreateResponse,
    ConversationSessionsResponse,
)
from app.services.conversation import (
    CONVERSATION_PAGE_SIZE,
    create_conversation_report,
    create_conversation_session,
    delete_conversation_session,
    get_conversation_archive,
    get_conversation_session_detail,
    get_conversation_sessions,
    reply_to_conversation_message,
    save_conversation_session,
    toggle_conversation_message_save,
    unsave_conversation_archive_message,
)

router = APIRouter()


@router.get(
    "/conversation-sessions",
    response_model=ConversationSessionsResponse,
    summary="텍스트 및 음성 대화 조회",
    description=(
        "현재 사용자의 마지막 접근 활성 큐브 소유권에 속한 텍스트 또는 "
        "음성 대화 세션을 요청한 size 단위로 마지막 메시지 최신순 조회합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "마지막 접근 ACTIVE 큐브 소유권이 존재하지 않음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "CUBE_OWNERSHIP_NOT_FOUND",
                        "message": "큐브 소유권 정보를 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def read_conversation_sessions(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    conversation_type: Annotated[
        ConversationType,
        Query(alias="conversationType"),
    ],
    page: Annotated[int, Query(ge=0)] = 0,
    size: Annotated[int, Query(ge=1)] = CONVERSATION_PAGE_SIZE,
) -> ConversationSessionsResponse:
    """GET /api/v1/users/me/conversation-sessions"""
    return get_conversation_sessions(
        db=db,
        current_user_id=current_user_id,
        conversation_type=conversation_type,
        page=page,
        size=size,
    )


@router.get(
    "/conversation-archive",
    response_model=ConversationArchiveResponse,
    summary="대화 보관함 조회",
    description=(
        "현재 사용자의 마지막 접근 활성 큐브 소유권에 속한 보관된 "
        "아바타 텍스트 대화 메시지를 최신순으로 조회합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "마지막 접근 ACTIVE 큐브 소유권이 존재하지 않음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "CUBE_OWNERSHIP_NOT_FOUND",
                        "message": "큐브 소유권 정보를 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def read_conversation_archive(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> ConversationArchiveResponse:
    """GET /api/v1/users/me/conversation-archive"""
    return get_conversation_archive(
        db=db,
        current_user_id=current_user_id,
    )


@router.delete(
    "/conversation-messages/{conversationMessageId}/unsave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="대화 보관함 삭제",
    description=(
        "현재 사용자의 마지막 접근 활성 큐브 소유권에 속한 보관 메시지의 "
        "is_text_saved를 false로 변경합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "대화 메시지가 없거나 이미 보관 해제된 메시지임",
            "content": {
                "application/json": {
                    "example": {
                        "code": "CONVERSATION_MESSAGE_NOT_FOUND",
                        "message": "대화 메시지를 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def delete_conversation_archive_message(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    conversation_message_id: Annotated[
        int,
        Path(alias="conversationMessageId", ge=1),
    ],
) -> Response:
    """DELETE /api/v1/users/me/conversation-messages/{conversationMessageId}/unsave"""
    unsave_conversation_archive_message(
        db=db,
        current_user_id=current_user_id,
        conversation_message_id=conversation_message_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/conversation-sessions",
    response_model=ConversationSessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="대화 세션 생성",
    description=(
        "현재 사용자의 마지막 활성 큐브 소유권에 텍스트 또는 음성 대화 "
        "세션을 생성합니다."
    ),
)
def create_new_conversation_session(
    body: ConversationSessionCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> ConversationSessionCreateResponse:
    """POST /api/v1/users/me/conversation-sessions"""
    return create_conversation_session(
        db=db,
        current_user_id=current_user_id,
        conversation_type=body.conversation_type,
    )


@router.delete(
    "/conversation-sessions/{conversationSessionId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="대화 세션 삭제",
    description=(
        "현재 사용자의 활성 큐브 소유권에 속한 텍스트 또는 음성 "
        "대화 세션을 deleted_at 저장 방식으로 소프트 딜리트합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "삭제할 대화 세션이 없거나 이미 삭제된 세션임",
            "content": {
                "application/json": {
                    "example": {
                        "code": "CONVERSATION_SESSION_NOT_FOUND",
                        "message": "삭제할 대화 세션을 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def delete_existing_conversation_session(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    conversation_session_id: Annotated[
        int,
        Path(alias="conversationSessionId", ge=1),
    ],
) -> Response:
    """DELETE /api/v1/users/me/conversation-sessions/{conversationSessionId}"""
    delete_conversation_session(
        db=db,
        current_user_id=current_user_id,
        conversation_session_id=conversation_session_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/conversation-messages/{conversationMessageId}/save",
    response_model=ConversationMessageSaveResponse,
    summary="대화 텍스트 보관",
    description=(
        "현재 사용자의 활성 큐브 소유권에 속한 아바타 텍스트 대화 "
        "메시지의 보관 여부를 토글합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "대화 메시지를 찾을 수 없거나 보관할 수 없는 메시지임",
            "content": {
                "application/json": {
                    "examples": {
                        "conversationMessageNotFound": {
                            "value": {
                                "code": "CONVERSATION_MESSAGE_NOT_FOUND",
                                "message": "대화 메시지를 찾을 수 없습니다.",
                            }
                        },
                        "userConversationMessageSaveNotAvailable": {
                            "value": {
                                "code": (
                                    "USER_CONVERSATION_MESSAGE_SAVE_NOT_AVAILABLE"
                                ),
                                "message": "사용자 대화는 보관이 불가합니다.",
                            }
                        },
                        "voiceConversationMessageSaveNotAvailable": {
                            "value": {
                                "code": (
                                    "VOICE_CONVERSATION_MESSAGE_SAVE_NOT_AVAILABLE"
                                ),
                                "message": "음성 대화는 보관이 불가합니다.",
                            }
                        },
                    }
                }
            },
        },
    },
)
def save_conversation_message(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    conversation_message_id: Annotated[
        int,
        Path(alias="conversationMessageId", ge=1),
    ],
) -> ConversationMessageSaveResponse:
    """PATCH /api/v1/users/me/conversation-messages/{conversationMessageId}/save"""
    return toggle_conversation_message_save(
        db=db,
        current_user_id=current_user_id,
        conversation_message_id=conversation_message_id,
    )


@router.post(
    "/conversation-messages/{conversationMessageId}/reports",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="텍스트 응답 오류 신고",
    description="현재 사용자의 아바타 대화 메시지에 대한 오류 신고를 저장합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "대화 메시지가 없거나 현재 사용자의 메시지가 아니거나 "
                "삭제된 세션 또는 USER 발신 메시지임"
            ),
            "content": {
                "application/json": {
                    "example": {
                        "code": "CONVERSATION_MESSAGE_NOT_FOUND",
                        "message": "대화 메시지를 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def create_text_response_report(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    conversation_message_id: Annotated[
        int,
        Path(alias="conversationMessageId", ge=1),
    ],
    body: ConversationReportCreateRequest,
) -> Response:
    """POST /api/v1/users/me/conversation-messages/{conversationMessageId}/reports"""
    create_conversation_report(
        db=db,
        current_user_id=current_user_id,
        conversation_message_id=conversation_message_id,
        reason=body.reason,
        detail_reason=body.detail_reason,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/conversation-sessions/{conversationSessionId}",
    response_model=ConversationDetailResponse,
    summary="대화 세션 상세 조회",
    description=(
        "현재 사용자의 활성 큐브 소유권에 속한 텍스트 대화 세션의 "
        "전체 메시지를 sequenceNumber 내림차순으로 조회합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "대화 세션이 없거나 음성 대화 세션이라 상세 조회가 불가능함",
            "content": {
                "application/json": {
                    "examples": {
                        "conversationSessionNotFound": {
                            "value": {
                                "code": "CONVERSATION_SESSION_NOT_FOUND",
                                "message": "대화 세션을 찾을 수 없습니다.",
                            }
                        },
                        "voiceConversationDetailNotAvailable": {
                            "value": {
                                "code": "VOICE_CONVERSATION_DETAIL_NOT_AVAILABLE",
                                "message": "음성 대화는 세션 상세 조회가 불가능합니다.",
                            }
                        },
                    }
                }
            },
        },
    },
)
def read_conversation_session_detail(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    conversation_session_id: Annotated[
        int,
        Path(alias="conversationSessionId", ge=1),
    ],
) -> ConversationDetailResponse:
    """GET /api/v1/users/me/conversation-sessions/{conversationSessionId}"""
    return get_conversation_session_detail(
        db=db,
        current_user_id=current_user_id,
        conversation_session_id=conversation_session_id,
    )


@router.post(
    "/conversation-sessions/{conversationSessionId}/messages",
    response_model=ConversationMessageReplyResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    summary="대화 메시지 응답",
    description=(
        "현재 사용자의 텍스트 또는 음성 대화 세션에 사용자 메시지를 받고, "
        "OpenAI GPT로 아바타 응답을 생성한 뒤 USER/AVATAR 메시지를 함께 "
        "저장해 반환합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "대화 세션이 없거나 전송할 이미지를 찾을 수 없음",
            "content": {
                "application/json": {
                    "examples": {
                        "conversationSessionNotFound": {
                            "value": {
                                "code": "CONVERSATION_SESSION_NOT_FOUND",
                                "message": "대화 세션을 찾을 수 없습니다.",
                            }
                        },
                        "conversationImageNotFound": {
                            "value": {
                                "code": "CONVERSATION_IMAGE_NOT_FOUND",
                                "message": "전송할 이미지를 찾을 수 없습니다.",
                            }
                        },
                    }
                }
            },
        },
    },
)
def create_conversation_message_reply(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    conversation_session_id: Annotated[
        int,
        Path(alias="conversationSessionId", ge=1),
    ],
    body: ConversationMessageReplyRequest,
) -> ConversationMessageReplyResponse:
    """POST /api/v1/users/me/conversation-sessions/{conversationSessionId}/messages"""
    return reply_to_conversation_message(
        db=db,
        current_user_id=current_user_id,
        conversation_session_id=conversation_session_id,
        body=body,
    )


@router.patch(
    "/conversation-sessions/{conversationSessionId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="대화 세션 상태 저장",
    description=(
        "현재 사용자의 대화 세션을 NOT_ACTIVE로 변경하고 종료 시각을 저장합니다. "
        "제목이 없고 메시지가 있으면 첫 메시지 2개로 GPT 제목을 생성합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "대화 세션이 없거나 현재 사용자의 세션이 아님",
            "content": {
                "application/json": {
                    "example": {
                        "code": "CONVERSATION_SESSION_NOT_FOUND",
                        "message": "대화 세션을 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def update_conversation_session(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    conversation_session_id: Annotated[
        int,
        Path(alias="conversationSessionId", ge=1),
    ],
    audio: Annotated[
        UploadFile | None,
        File(description="M4A, MP3, WAV 또는 WebM 오디오 파일"),
    ] = None,
    audio_duration_seconds: Annotated[
        int | None,
        Form(alias="audioDurationSeconds"),
    ] = None,
) -> Response:
    """PATCH /api/v1/users/me/conversation-sessions/{conversationSessionId}"""
    save_conversation_session(
        db=db,
        current_user_id=current_user_id,
        conversation_session_id=conversation_session_id,
        audio_file=audio.file if audio is not None else None,
        audio_content_type=audio.content_type if audio is not None else None,
        audio_duration_seconds=audio_duration_seconds,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
