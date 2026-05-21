import httpx
import logging
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

                return [
                    GameDealSchema(
                        title=item.get("title"),
                        sale_price=0.0,
                        store=item.get("platforms"),
                        url=item.get("open_giveaway_url"),
                        is_giveaway=True,
                        deal_id=str(item.get("id"))
                    )
                    for item in giveaways
                ]
        except httpx.HTTPStatusError as e:
            logger.error(f"GamerPower API error: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.TimeoutException:
            logger.error("GamerPower API timeout")
            return []
        except Exception as e:
            logger.error(f"Unexpected error calling GamerPower API: {str(e)}")
            return []
