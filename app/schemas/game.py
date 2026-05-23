from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

class GameResponse(BaseModel):
    id: UUID
    title: str
    current_price: float
    historical_low: float
    is_free: bool
    store_name: str | None = None
    deal_url: str | None = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class GameAuditResponse(BaseModel):
    title: str
    current_price: float
    historical_low: float
    is_historical_low: bool
    store_name: str | None = None
    deal_url: str | None = None
