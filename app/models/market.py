"""마켓 상품, 판매글, 거래, 거래 이미지, 디지털 인증서 ORM 매핑."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.cube import Cube, enum_values
from app.models.enums import SellListingStatus, TradeStatus
from app.models.user import User


class MarketProduct(Base):
    __tablename__ = "market_product"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cube_id: Mapped[int] = mapped_column(ForeignKey("cube.id"))
    product_image_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    cube: Mapped[Cube] = relationship(back_populates="market_products")
    sell_listings: Mapped[list["SellListing"]] = relationship(
        back_populates="market_product"
    )


class SellListing(Base):
    __tablename__ = "sell_listing"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    market_product_id: Mapped[int] = mapped_column(ForeignKey("market_product.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    product_status: Mapped[str | None] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(500))
    price: Mapped[int] = mapped_column(Integer)
    status: Mapped[SellListingStatus] = mapped_column(
        Enum(
            SellListingStatus,
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

    market_product: Mapped[MarketProduct] = relationship(
        back_populates="sell_listings"
    )
    user: Mapped[User] = relationship(back_populates="sell_listings")
    trades: Mapped[list["Trade"]] = relationship(back_populates="sell_listing")
    media: Mapped[list["ListingMedia"]] = relationship(back_populates="sell_listing")


class Trade(Base):
    __tablename__ = "trade"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sell_listing_id: Mapped[int] = mapped_column(ForeignKey("sell_listing.id"))
    buyer_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    buyer_phone_number: Mapped[str] = mapped_column(String(20))
    buyer_address: Mapped[str] = mapped_column(String(100))
    total_price: Mapped[int] = mapped_column(Integer)
    paid_time: Mapped[datetime | None] = mapped_column(DateTime)
    sent_time: Mapped[datetime | None] = mapped_column(DateTime)
    shipped_time: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_time: Mapped[datetime | None] = mapped_column(DateTime)
    completed_time: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[TradeStatus] = mapped_column(
        Enum(
            TradeStatus,
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

    sell_listing: Mapped[SellListing] = relationship(back_populates="trades")
    buyer: Mapped[User] = relationship(back_populates="bought_trades")
    digital_certificate: Mapped["DigitalCertificate"] = relationship(
        back_populates="trade", uselist=False
    )


class ListingMedia(Base):
    __tablename__ = "listing_media"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sell_listing_id: Mapped[int] = mapped_column(ForeignKey("sell_listing.id"))
    image_url: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    sell_listing: Mapped[SellListing] = relationship(back_populates="media")


class DigitalCertificate(Base):
    __tablename__ = "digital_certificate"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    trade_id: Mapped[int] = mapped_column(ForeignKey("trade.id"), unique=True)
    network: Mapped[str] = mapped_column(String(200))
    token_standard: Mapped[str] = mapped_column(String(200))
    token_id: Mapped[str] = mapped_column(String(200))
    contract_address: Mapped[str] = mapped_column(String(200))
    tx_hash: Mapped[str] = mapped_column(String(200))
    metadata_url: Mapped[str] = mapped_column(String(200))

    trade: Mapped[Trade] = relationship(back_populates="digital_certificate")
