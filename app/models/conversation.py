"""아바타 대화, 신고와 인터랙션 모델."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin
from app.models.enums import (
    ConversationSessionStatus,
    ConversationType,
    InteractionStatus,
    MessageStatus,
    ReportReason,
    SenderType,
    ViolationType,
    enum_type,
)


class AvatarConversationSession(TimestampMixin, Base):
    """큐브 아바타와 진행한 텍스트·음성 대화 세션."""

    __tablename__ = "avatar_conversation_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cube_ownership_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cube_ownerships.id"), nullable=False, index=True
    )
    conversation_type: Mapped[ConversationType] = mapped_column(
        enum_type(ConversationType, name="conversation_type", length=20),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    audio_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conversation_title: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[ConversationSessionStatus] = mapped_column(
        enum_type(
            ConversationSessionStatus,
            name="conversation_session_status",
            length=20,
        ),
        nullable=False,
        default=ConversationSessionStatus.ACTIVE,
        server_default=ConversationSessionStatus.ACTIVE.value,
    )


class AvatarConversationMessage(TimestampMixin, Base):
    """아바타 대화 세션의 순서가 있는 메시지."""

    __tablename__ = "avatar_conversation_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("avatar_conversation_sessions.id"),
        nullable=False,
        index=True,
    )
    sender_type: Mapped[SenderType] = mapped_column(
        enum_type(SenderType, name="conversation_sender_type", length=20),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_text_saved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    status: Mapped[MessageStatus] = mapped_column(
        enum_type(MessageStatus, name="conversation_message_status", length=20),
        nullable=False,
        default=MessageStatus.ALLOWED,
        server_default=MessageStatus.ALLOWED.value,
    )
    violation_type: Mapped[ViolationType | None] = mapped_column(
        enum_type(ViolationType, name="conversation_violation_type", length=20),
        nullable=True,
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )


class AvatarConversationImage(TimestampMixin, Base):
    """대화 세션 중 사용자가 전송한 이미지."""

    __tablename__ = "avatar_conversation_images"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("avatar_conversation_sessions.id"),
        nullable=False,
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    sent_image_url: Mapped[str] = mapped_column(String(500), nullable=False)


class ConversationReport(TimestampMixin, Base):
    """아바타 답변 메시지에 대한 사용자 신고."""

    __tablename__ = "conversation_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("avatar_conversation_messages.id"),
        nullable=False,
        unique=True,
    )
    reason: Mapped[ReportReason] = mapped_column(
        enum_type(ReportReason, name="conversation_report_reason", length=50),
        nullable=False,
    )
    detail_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)


class AvatarInteractionSession(TimestampMixin, Base):
    """아바타와 진행한 비대화형 인터랙션 세션."""

    __tablename__ = "avatar_interaction_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cube_ownership_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cube_ownerships.id"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[InteractionStatus] = mapped_column(
        enum_type(InteractionStatus, name="avatar_interaction_status", length=20),
        nullable=False,
        default=InteractionStatus.ACTIVE,
        server_default=InteractionStatus.ACTIVE.value,
    )


class AvatarInteractionPicture(TimestampMixin, SoftDeleteMixin, Base):
    """아바타 인터랙션에서 촬영한 이미지."""

    __tablename__ = "avatar_interaction_pictures"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    interaction_session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("avatar_interaction_sessions.id"),
        nullable=False,
        index=True,
    )
    picture_img_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pictured_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
