import httpx
import logging
from datetime import datetime
from typing import List
from app.core.config import settings
from app.schemas.game_deal import GameDealSchema

logger = logging.getLogger(__name__)

class GamerPowerClient:
    def __init__(self):
        self.base_url = settings.GAMERPOWER_BASE_URL

    async def get_pc_giveaways(self) -> List[GameDealSchema]:
        url = f"{self.base_url}/giveaways"
        params = {"platform": "pc"}

        try:
            headers = {"User-Agent": "GameDealTracker/1.0 (contato@teste.com)"}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers, timeout=10.0)
                response.raise_for_status()
                giveaways = response.json()

                # If no giveaways or unexpected format
                if not isinstance(giveaways, list):
                    return []

                result = []
                for item in giveaways:
                    # Filtro estrito: processa apenas itens do tipo "Game"
                    if item.get("type") != "Game":
                        continue

                    published_date_str = item.get("published_date")
                    end_date_str = item.get("end_date")

                    promo_start_date = None
                    if published_date_str:
                        try:
                            promo_start_date = datetime.strptime(published_date_str, "%Y-%m-%d %H:%M:%S")
                        except (ValueError, TypeError):
                            pass

                    promo_end_date = None
                    if end_date_str and end_date_str != "N/A":
                        try:
                            promo_end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
                        except (ValueError, TypeError):
                            pass

                    result.append(
                        GameDealSchema(
                            title=item.get("title", "Unknown"),
                            original_price=None,
                            sale_price=0.0,
                            metacritic_score=None,
                            store=item.get("platforms", "Unknown"),
                            url=item.get("open_giveaway_url", ""),
                            is_giveaway=True,
                            deal_id=str(item.get("id")) if item.get("id") else None,
                            promo_start_date=promo_start_date,
                            promo_end_date=promo_end_date,
                            image_url=item.get("image", None)
                        )
                    )
                return result
        except httpx.HTTPStatusError as e:
            logger.error(f"GamerPower API error: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.TimeoutException:
            logger.error("GamerPower API timeout")
            return []
        except Exception as e:
            logger.error(f"Unexpected error calling GamerPower API: {str(e)}")
            return []
