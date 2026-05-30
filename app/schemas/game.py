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
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def apply_store_mapping(self) -> 'GameResponse':
        mapped = map_store(self.store_name)
        self.store_name = mapped["name"]
        self.store_icon_url = mapped["icon"]
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

    @model_validator(mode='after')
    def apply_store_mapping(self) -> 'GameAuditResponse':
        mapped = map_store(self.store_name)
        self.store_name = mapped["name"]
        self.store_icon_url = mapped["icon"]
        return self
