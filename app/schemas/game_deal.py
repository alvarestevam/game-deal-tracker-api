from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GameDealSchema(BaseModel):
    title: str
    original_price: Optional[float] = None
    sale_price: float
    metacritic_score: Optional[int] = None
    store: str
    deal_rating: Optional[float] = None
    deal_id: Optional[str] = None
    url: str
    is_giveaway: bool = False
    historical_low: Optional[float] = None
    promo_start_date: Optional[datetime] = None
    promo_end_date: Optional[datetime] = None
    image_url: Optional[str] = None
