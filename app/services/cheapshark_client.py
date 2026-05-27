import httpx
import logging
from datetime import datetime
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

                result_map = {}
                game_ids = []
                for item in deals:
                    deal_rating = float(item.get("dealRating", 0))
                    if deal_rating > 8.0:
                        game_id = str(item.get("gameID"))
                        game_ids.append(game_id)

                        last_change = item.get("lastChange")
                        promo_start_date = None
                        if last_change:
                            try:
                                promo_start_date = datetime.fromtimestamp(int(last_change))
                            except (ValueError, TypeError):
                                pass

                        result_map[game_id] = GameDealSchema(
                            title=item.get("title"),
                            original_price=float(item.get("normalPrice")),
                            sale_price=float(item.get("salePrice")),
                            store=str(item.get("storeID")), # Store ID from CheapShark
                            deal_rating=deal_rating,
                            deal_id=item.get("dealID"),
                            url=f"https://www.cheapshark.com/redirect?dealID={item.get('dealID')}",
                            promo_start_date=promo_start_date,
                            image_url=item.get("thumb")
                        )

                # Fetch historical lows in batches of 25
                for i in range(0, len(game_ids), 25):
                    batch = game_ids[i:i+25]
                    batch_ids = ",".join(batch)
                    batch_url = f"{self.base_url}/games?ids={batch_ids}"
                    try:
                        batch_response = await client.get(batch_url, headers=headers, timeout=10.0)
                        if batch_response.status_code == 200:
                            batch_data = batch_response.json()
                            for g_id, g_info in batch_data.items():
                                if g_id in result_map:
                                    low_price = g_info.get("cheapestPriceEver", {}).get("price")
                                    if low_price:
                                        result_map[g_id].historical_low = float(low_price)
                    except Exception as e:
                        logger.error(f"Error fetching historical low batch: {str(e)}")

                return list(result_map.values())
        except httpx.HTTPStatusError as e:
            logger.error(f"CheapShark API error: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.TimeoutException:
            logger.error("CheapShark API timeout")
            return []
        except Exception as e:
            logger.error(f"Unexpected error calling CheapShark API: {str(e)}")
            return []
