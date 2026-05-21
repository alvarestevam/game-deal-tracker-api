from pydantic import BaseModel
from typing import Optional

class GameDealSchema(BaseModel):
    title: str
    original_price: Optional[float] = None
    sale_price: float
    store: str
    deal_rating: Optional[float] = None
    deal_id: Optional[str] = None
    url: str
    is_giveaway: bool = False
    historical_low: Optional[float] = None
