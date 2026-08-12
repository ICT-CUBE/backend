"""대화 도메인 API 라우터."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.enums import ConversationType
from app.schemas.common import ErrorResponse
from app.schemas.conversation import (
    ConversationDetailResponse,
    ConversationSessionCreateRequest,
    ConversationSessionCreateResponse,
    ConversationSessionsResponse,
)
from app.services.conversation import (
    CONVERSATION_PAGE_SIZE,
    create_conversation_session,
    delete_conversation_session,
    get_conversation_session_detail,
    get_conversation_sessions,
)

router = APIRouter()


@router.get(
    "/conversation-sessions",
    response_model=ConversationSessionsResponse,
    summary="텍스트 및 음성 대화 조회",
    description=(
        "고정 사용자 ID 1의 활성 큐브 소유권에 속한 텍스트 또는 음성 대화 "
        "세션 목록을 마지막 메시지 최신순으로 조회합니다."
    ),
)
def read_conversation_sessions(
    db: Annotated[Session, Depends(get_db)],
    conversation_type: Annotated[
        ConversationType,
        Query(alias="conversationType"),
    ],
    page: Annotated[int, Query(ge=0)] = 0,
    size: Annotated[
        int,
        Query(ge=CONVERSATION_PAGE_SIZE, le=CONVERSATION_PAGE_SIZE),
    ] = CONVERSATION_PAGE_SIZE,
) -> ConversationSessionsResponse:
    """GET /api/v1/users/me/conversation-sessions"""
    _ = size
    return get_conversation_sessions(
        db=db,
        conversation_type=conversation_type,
        page=page,
    )


@router.post(
    "/conversation-sessions",
    response_model=ConversationSessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="대화 세션 생성",
    description=(
        "고정 사용자 ID 1의 마지막 활성 큐브 소유권에 텍스트 또는 음성 대화 "
        "세션을 생성합니다."
    ),
)
def create_new_conversation_session(
    body: ConversationSessionCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ConversationSessionCreateResponse:
    """POST /api/v1/users/me/conversation-sessions"""
    return create_conversation_session(
        db=db,
        conversation_type=body.conversationType,
    )


@router.delete(
    "/conversation-sessions/{conversationSessionId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="대화 세션 삭제",
    description=(
        "고정 사용자 ID 1의 활성 큐브 소유권에 속한 텍스트 또는 음성 "
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
    conversation_session_id: Annotated[
        int,
        Path(alias="conversationSessionId", ge=1),
    ],
) -> Response:
    """DELETE /api/v1/users/me/conversation-sessions/{conversationSessionId}"""
    delete_conversation_session(
        db=db,
        conversation_session_id=conversation_session_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/conversation-sessions/{conversationSessionId}",
    response_model=ConversationDetailResponse,
    summary="대화 세션 상세 조회",
    description=(
        "고정 사용자 ID 1의 활성 큐브 소유권에 속한 텍스트 대화 세션의 "
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
    conversation_session_id: Annotated[
        int,
        Path(alias="conversationSessionId", ge=1),
    ],
) -> ConversationDetailResponse:
    """GET /api/v1/users/me/conversation-sessions/{conversationSessionId}"""
    return get_conversation_session_detail(
        db=db,
        conversation_session_id=conversation_session_id,
    )
