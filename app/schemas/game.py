from pydantic import BaseModel, ConfigDict, model_validator
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.utils.store_mapper import map_store

class GameResponse(BaseModel):
    id: UUID
    title: str
    current_price: float
    historical_low: float
    is_free: bool
    store_name: str | None = None
    store_icon_url: Optional[str] = None
    deal_url: str | None = None
    promo_start_date: datetime | None = None
    promo_end_date: datetime | None = None
    is_active: bool
    image_url: str | None = None
    estimated_final_price: float = 0.0
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def apply_store_mapping(self) -> 'GameResponse':
        # 1. Store Mapping
        mapped = map_store(self.store_name)
        self.store_name = mapped["name"]
        self.store_icon_url = mapped["store_icon_url"]

        # 2. Image Fallback
        if not self.image_url:
            self.image_url = "https://via.placeholder.com/600x300.png?text=GamesInDeal+No+Image"

        # 3. Estimated Final Price Calculation
        if self.is_free or self.current_price == 0:
            self.estimated_final_price = 0.0
        elif self.store_name == "Nuuvem":
            self.estimated_final_price = self.current_price
        else:
            # International stores: apply 6.38% (IOF + Spread)
            self.estimated_final_price = round(self.current_price * 1.0638, 2)

        return self

class GameAuditResponse(BaseModel):
    title: str
    current_price: float
    historical_low: float
    is_historical_low: bool
    store_name: str | None = None
    store_icon_url: Optional[str] = None
    deal_url: str | None = None
    promo_start_date: datetime | None = None
    promo_end_date: datetime | None = None
    is_active: bool
    image_url: str | None = None
    estimated_final_price: float = 0.0

    @model_validator(mode='after')
    def apply_store_mapping(self) -> 'GameAuditResponse':
        # 1. Store Mapping
        mapped = map_store(self.store_name)
        self.store_name = mapped["name"]
        self.store_icon_url = mapped["store_icon_url"]

        # 2. Image Fallback
        if not self.image_url:
            self.image_url = "https://via.placeholder.com/600x300.png?text=GamesInDeal+No+Image"

        # 3. Estimated Final Price Calculation
        # GameAuditResponse doesn't have is_free field, use current_price only
        if self.current_price == 0:
            self.estimated_final_price = 0.0
        elif self.store_name == "Nuuvem":
            self.estimated_final_price = self.current_price
        else:
            # International stores: apply 6.38% (IOF + Spread)
            self.estimated_final_price = round(self.current_price * 1.0638, 2)

        return self