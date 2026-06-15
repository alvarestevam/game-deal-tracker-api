import uuid
from datetime import datetime
from typing import List
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String, index=True, unique=True)
    slug: Mapped[str | None] = mapped_column(String, index=True, unique=True, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metacritic_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    offers: Mapped[List["GameOffer"]] = relationship(
        "GameOffer",
        back_populates="game",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

class GameOffer(Base):
    __tablename__ = "game_offers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"))
    store_name: Mapped[str] = mapped_column(String)
    store_icon_url: Mapped[str | None] = mapped_column(String, nullable=True)
    original_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_price: Mapped[float] = mapped_column(Float)
    estimated_final_price: Mapped[float] = mapped_column(Float)
    historical_low: Mapped[float] = mapped_column(Float)
    deal_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    promo_start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    promo_end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notified_telegram: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    game: Mapped["Game"] = relationship("Game", back_populates="offers")
