from pydantic import BaseModel, ConfigDict
from uuid import UUID

class TelegramPreviewResponse(BaseModel):
    id: UUID
    title: str
    current_price: float
    store_name: str
    notified_telegram: bool

    model_config = ConfigDict(from_attributes=True)

class TelegramChat(BaseModel):
    id: int

class TelegramMessage(BaseModel):
    text: str | None = None
    chat: TelegramChat

class TelegramUpdate(BaseModel):
    update_id: int
    message: TelegramMessage | None = None
