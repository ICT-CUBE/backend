"""텍스트·음성 대화 목록 조회 API 응답 스키마."""

from datetime import datetime

from pydantic import Field, field_validator

from app.models.enums import ConversationType
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


class ConversationMessageReplyRequest(ApiSchema):
    content: str
    image_urls: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content must not be blank")
        return value


class ConversationMessageReplyItemResponse(ApiSchema):
    id: int
    sender_type: str
    content: str
    image_urls: list[str] | None = None
    sequence_number: int
    sent_at: datetime


class ConversationMessageReplyResponse(ApiSchema):
    user_message: ConversationMessageReplyItemResponse
    avatar_message: ConversationMessageReplyItemResponse
