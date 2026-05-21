import httpx
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class ITADClient:
    def __init__(self):
        self.base_url = settings.ITAD_BASE_URL
        self.api_key = settings.ITAD_API_KEY

    async def get_historical_low(self, game_id: str) -> Optional[float]:
        """
        In ITAD API v2, we first need the internal ITAD game ID if not provided,
        but assuming game_id is the ITAD ID for this implementation.
        Endpoint: /history/low/v1
        """
        url = f"{self.base_url}/history/low/v1"
        # ITAD v2 often requires POST for some endpoints, let's check common patterns.
        # Based on docs snippet: postHistory Low

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
