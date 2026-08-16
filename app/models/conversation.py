"""아바타 대화 세션과 메시지 테이블 ORM 매핑."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.cube import CubeOwnership, enum_values
from app.models.enums import (
    AvatarConversationSessionStatus,
    ConversationMessageSenderType,
    ConversationMessageStatus,
    ConversationMessageViolationType,
    ConversationReportReason,
    ConversationType,
)


class AvatarConversationSession(Base):
    __tablename__ = "avatar_conversation_session"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cube_ownership_id: Mapped[int] = mapped_column(ForeignKey("cube_ownership.id"))
    conversation_type: Mapped[ConversationType] = mapped_column(
        Enum(
            ConversationType,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    started_at: Mapped[datetime] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    audio_url: Mapped[str | None] = mapped_column(String(500))
    audio_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    conversation_title: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[AvatarConversationSessionStatus] = mapped_column(
        Enum(
            AvatarConversationSessionStatus,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    cube_ownership: Mapped[CubeOwnership] = relationship(
        back_populates="avatar_conversation_sessions"
    )
    messages: Mapped[list["AvatarConversationMessage"]] = relationship(
        back_populates="conversation_session"
    )


class AvatarConversationMessage(Base):
    __tablename__ = "avatar_conversation_message"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    conversation_session_id: Mapped[int] = mapped_column(
        ForeignKey("avatar_conversation_session.id")
    )
    sender_type: Mapped[ConversationMessageSenderType] = mapped_column(
        Enum(
            ConversationMessageSenderType,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    content: Mapped[str] = mapped_column(Text)
    sequence_number: Mapped[int] = mapped_column(Integer)
    is_text_saved: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[ConversationMessageStatus] = mapped_column(
        Enum(
            ConversationMessageStatus,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    violation_type: Mapped[ConversationMessageViolationType | None] = mapped_column(
        Enum(
            ConversationMessageViolationType,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    sent_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    conversation_session: Mapped[AvatarConversationSession] = relationship(
        back_populates="messages"
    )
    report: Mapped["ConversationReport"] = relationship(
        back_populates="conversation_message", uselist=False
    )


class ConversationReport(Base):
    __tablename__ = "conversation_report"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    conversation_message_id: Mapped[int] = mapped_column(
        ForeignKey("avatar_conversation_message.id")
    )
    reason: Mapped[ConversationReportReason] = mapped_column(
        Enum(
            ConversationReportReason,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    detail_reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    conversation_message: Mapped[AvatarConversationMessage] = relationship(
        back_populates="report"
    )
