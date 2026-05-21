import httpx
import logging
from typing import List, Optional
from app.core.config import settings
from app.schemas.game_deal import GameDealSchema

logger = logging.getLogger(__name__)

class CheapSharkClient:
    def __init__(self):
        self.base_url = settings.CHEAPSHARK_BASE_URL

    async def get_deals(self, lower_price: Optional[float] = None) -> List[GameDealSchema]:
        url = f"{self.base_url}/deals"
        params = {"upperPrice": 50} # Default upper price to avoid too many results if needed
        if lower_price is not None:
            params["lowerPrice"] = lower_price

        try:
            headers = {"User-Agent": "GameDealTracker/1.0 (contato@teste.com)"}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers, timeout=10.0)
                response.raise_for_status()
                deals = response.json()

                if not isinstance(deals, list):
                    return []

                result = []
                for item in deals:
                    deal_rating = float(item.get("dealRating", 0))
                    if deal_rating > 8.0:
                        result.append(
                            GameDealSchema(
                                title=item.get("title"),
                                original_price=float(item.get("normalPrice")),
                                sale_price=float(item.get("salePrice")),
                                store=str(item.get("storeID")), # Store ID from CheapShark
                                deal_rating=deal_rating,
                                deal_id=item.get("dealID"),
                                url=f"https://www.cheapshark.com/redirect?dealID={item.get('dealID')}"
                            )
                        )
                return result
        except httpx.HTTPStatusError as e:
            logger.error(f"CheapShark API error: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.TimeoutException:
            logger.error("CheapShark API timeout")
            return []
        except Exception as e:
            logger.error(f"Unexpected error calling CheapShark API: {str(e)}")
            return []
