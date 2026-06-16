from pydantic import BaseModel, ConfigDict
from uuid import UUID

class TelegramPreviewResponse(BaseModel):
    id: UUID
    title: str
    deal_score: float
    current_price: float
    store_name: str
    notified_telegram: bool

    model_config = ConfigDict(from_attributes=True)
