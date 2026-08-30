"""텍스트·음성 대화 목록 조회 API 응답 스키마."""

from datetime import datetime

from pydantic import Field, field_validator

from app.models.enums import ConversationReportReason, ConversationType
from app.schemas.base import ApiSchema


class ConversationLastMessageResponse(ApiSchema):
    id: int
    content: str | None
    sent_at: datetime


class ConversationSessionResponse(ApiSchema):
    id: int
    conversation_type: ConversationType
    conversation_title: str | None
    audio_url: str | None
    audio_duration_seconds: int | None
    last_message: ConversationLastMessageResponse


class ConversationPaginationResponse(ApiSchema):
    page: int
    size: int
    has_next: bool


class ConversationSessionsResponse(ApiSchema):
    conversation_sessions: list[ConversationSessionResponse]
    pagination: ConversationPaginationResponse


class ConversationSessionCreateRequest(ApiSchema):
    conversation_type: ConversationType


class ConversationSessionCreateItemResponse(ApiSchema):
    id: int
    conversation_type: ConversationType


class ConversationSessionCreateResponse(ApiSchema):
    conversation_session: ConversationSessionCreateItemResponse


class ConversationDetailMessageResponse(ApiSchema):
    id: int
    sender_type: str
    content: str
    sequence_number: int
    sent_at: datetime


class ConversationDetailSessionResponse(ApiSchema):
    id: int
    messages: list[ConversationDetailMessageResponse]


class ConversationDetailResponse(ApiSchema):
    conversation_session: ConversationDetailSessionResponse


class ConversationMessageSaveItemResponse(ApiSchema):
    id: int
    is_text_saved: bool


class ConversationMessageSaveResponse(ApiSchema):
    conversation_message: ConversationMessageSaveItemResponse


class ConversationArchiveItemResponse(ApiSchema):
    id: int
    conversation_session_id: int
    content: str
    sequence_number: int
    sent_at: datetime


class ConversationArchiveResponse(ApiSchema):
    saved_texts: list[ConversationArchiveItemResponse]


class ConversationReportCreateRequest(ApiSchema):
    reason: ConversationReportReason
    detail_reason: str | None = Field(default=None, max_length=200)


class ConversationMessageReplyRequest(ApiSchema):
    conversation_type: ConversationType
    content: str
    image_urls: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content must not be blank")
        return value


class ConversationMessageReplyUserResponse(ApiSchema):
    id: int
    sender_type: str
    content: str
    image_urls: list[str]
    sequence_number: int
    sent_at: datetime


class ConversationMessageReplyAvatarResponse(ApiSchema):
    id: int
    sender_type: str
    content: str
    # 텍스트 대화에서는 음성을 만들지 않으므로 null로 반환합니다.
    audio_url: str | None
    sequence_number: int
    sent_at: datetime


class ConversationMessageReplyResponse(ApiSchema):
    user_message: ConversationMessageReplyUserResponse
    avatar_message: ConversationMessageReplyAvatarResponse
