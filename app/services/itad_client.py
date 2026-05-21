import httpx
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class ITADClient:
    def __init__(self):
        self.base_url = settings.ITAD_BASE_URL
        self.api_key = settings.ITAD_API_KEY

    async def get_game_id_by_title(self, title: str) -> Optional[str]:
        """
        Searches for a game by title and returns its internal ITAD ID.
        Endpoint: /games/search/v1
        """
        url = f"{self.base_url}/games/search/v1"
        params = {"key": self.api_key, "title": title}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                if isinstance(data, list) and len(data) > 0:
                    # Return the first match's ID
                    return data[0].get("id")

                return None
        except Exception as e:
            logger.error(f"Error searching game ID on ITAD: {str(e)}")
            return None

    async def get_historical_low(self, game_id: str) -> Optional[float]:
        """
        Retrieves the historical low price for a game by its ID.
        Endpoint: /history/low/v1
        """
        url = f"{self.base_url}/history/low/v1"
        params = {"key": self.api_key}
        payload = [game_id]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, params=params, json=payload, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                # Format expected: list of objects with "id" and "low"
                if isinstance(data, list) and len(data) > 0:
                    low_info = data[0].get("low")
                    if low_info:
                        return float(low_info.get("amount", 0))

                return None
        except httpx.HTTPStatusError as e:
            logger.error(f"ITAD API error: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.TimeoutException:
            logger.error("ITAD API timeout")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling ITAD API: {str(e)}")
            return None
