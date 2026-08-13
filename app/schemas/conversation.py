"""텍스트·음성 대화 목록 조회 API 응답 스키마."""

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ConversationType


class ConversationLastMessageResponse(BaseModel):
    id: int
    content: str | None
    sentAt: datetime


class ConversationSessionResponse(BaseModel):
    id: int
    conversationType: ConversationType
    conversationTitle: str | None
    audioUrl: str | None
    audioDurationSeconds: int | None
    lastMessage: ConversationLastMessageResponse


class ConversationPaginationResponse(BaseModel):
    page: int
    size: int
    hasNext: bool


class ConversationSessionsResponse(BaseModel):
    conversationSessions: list[ConversationSessionResponse]
    pagination: ConversationPaginationResponse


class ConversationSessionCreateRequest(BaseModel):
    conversationType: ConversationType


class ConversationSessionCreateItemResponse(BaseModel):
    id: int
    conversationType: ConversationType


class ConversationSessionCreateResponse(BaseModel):
    conversationSession: ConversationSessionCreateItemResponse


class ConversationDetailMessageResponse(BaseModel):
    id: int
    senderType: str
    content: str
    sequenceNumber: int
    sentAt: datetime


class ConversationDetailSessionResponse(BaseModel):
    id: int
    messages: list[ConversationDetailMessageResponse]


class ConversationDetailResponse(BaseModel):
    conversationSession: ConversationDetailSessionResponse


class ConversationMessageSaveItemResponse(BaseModel):
    id: int
    isTextSaved: bool


class ConversationMessageSaveResponse(BaseModel):
    conversationMessage: ConversationMessageSaveItemResponse
