"""블록체인 작업 상태 ORM 매핑."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.cube import enum_values
from app.models.enums import BlockchainOperationStatus, BlockchainOperationType


class BlockchainOperation(Base):
    __tablename__ = "blockchain_operation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    operation_type: Mapped[BlockchainOperationType] = mapped_column(
        Enum(
            BlockchainOperationType,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    status: Mapped[BlockchainOperationStatus] = mapped_column(
        Enum(
            BlockchainOperationStatus,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
        )
    )
    # 시리얼 형식 오류처럼 접수 전에 실패하면 토큰 번호가 없을 수 있습니다.
    token_id: Mapped[int | None] = mapped_column(Integer)
    cube_id: Mapped[int | None] = mapped_column(ForeignKey("cube.id"))
    trade_id: Mapped[int | None] = mapped_column(ForeignKey("trade.id"))
    idempotency_key: Mapped[str] = mapped_column(String(36), unique=True)
    # 접수에 실패하면 작업 id를 받지 못하므로 NULL이 됩니다.
    operation_id: Mapped[str | None] = mapped_column(String(36), unique=True)
    notification_id: Mapped[str | None] = mapped_column(String(36), unique=True)
    tx_hash: Mapped[str | None] = mapped_column(String(200))
    final_owner_address: Mapped[str | None] = mapped_column(String(42))
    failure_reason: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
