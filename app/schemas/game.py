from pydantic import BaseModel, ConfigDict, model_validator
from datetime import datetime
from uuid import UUID
from typing import List, Optional
from app.utils.store_mapper import map_store

class OfferResponse(BaseModel):
    store_name: str | None = None
    store_icon_url: Optional[str] = None
    current_price: float
    historical_low: float
    estimated_final_price: float = 0.0
    deal_url: str | None = None
    promo_start_date: datetime | None = None
    promo_end_date: datetime | None = None
    is_active: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def apply_offer_logic(self) -> 'OfferResponse':
        # 1. Store Mapping & Icon Mapping
        mapped = map_store(self.store_name)
        self.store_name = mapped["name"]
        self.store_icon_url = mapped["store_icon_url"]

        # 2. Estimated Final Price Calculation (IOF/Spread)
        # Stores transacting natively in BRL
        brl_stores = ("Steam", "Epic Games Store", "Nuuvem")

        # Free games or native BRL stores are exempt from the 6.38% increase
        if self.current_price == 0:
            self.estimated_final_price = 0.0
        elif self.store_name in brl_stores:
            self.estimated_final_price = self.current_price
        else:
            # International stores in USD: add 6.38% (IOF + Spread)
            self.estimated_final_price = round(self.current_price * 1.0638, 2)

        return self

class GameResponse(BaseModel):
    id: UUID
    title: str
    image_url: str | None = None
    updated_at: datetime
    offers: List[OfferResponse] = []

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def apply_image_fallback(self) -> 'GameResponse':
        if not self.image_url:
            self.image_url = "https://via.placeholder.com/600x300.png?text=GamesInDeal+No+Image"
        return self

class GameAuditResponse(BaseModel):
    title: str
    image_url: str | None = None
    is_historical_low: bool = False # This might need special handling if we want to show it per game
    offers: List[OfferResponse] = []

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def apply_audit_logic(self) -> 'GameAuditResponse':
        if not self.image_url:
            self.image_url = "https://via.placeholder.com/600x300.png?text=GamesInDeal+No+Image"

        # Calculate if ANY offer is at historical low
        if self.offers:
            self.is_historical_low = any(o.current_price <= o.historical_low for o in self.offers)

        return self
