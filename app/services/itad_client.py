import httpx
import logging
from typing import Optional, List
from datetime import datetime, timezone
from app.core.config import settings
from app.schemas.game_deal import GameDealSchema

logger = logging.getLogger(__name__)

class ITADClient:
    def __init__(self):
        self.base_url = settings.ITAD_BASE_URL
        self.api_key = settings.ITAD_API_KEY

    async def get_deals(self) -> List[GameDealSchema]:
        """
        Busca as ofertas atuais do IsThereAnyDeal.
        Endpoint: /deals/v2
        """
        url = f"{self.base_url}/deals/v2"
        # Usamos country=US para obter preços em dólar e converter no sync_service
        params = {"key": self.api_key, "country": "US", "limit": 100}

        try:
            headers = {"User-Agent": "GameDealTracker/1.0 (contato@teste.com)"}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers, timeout=15.0)
                response.raise_for_status()
                data = response.json()

                deals_list = data.get("list", [])
                result = []
                for item in deals_list:
                    deal = item.get("deal")
                    if not deal:
                        continue

                    assets = item.get("assets", {})
                    # Preferência por imagens de alta resolução
                    image_url = assets.get("banner600") or assets.get("boxart") or assets.get("banner400")

                    promo_start_date = None
                    timestamp = deal.get("timestamp")
                    if timestamp:
                        try:
                            # ISO format: 2024-10-01T15:25:52+02:00
                            promo_start_date = datetime.fromisoformat(timestamp)
                            if promo_start_date.tzinfo is None:
                                promo_start_date = promo_start_date.replace(tzinfo=timezone.utc)
                        except (ValueError, TypeError):
                            pass

                    promo_end_date = None
                    expiry = deal.get("expiry")
                    if expiry:
                        try:
                            promo_end_date = datetime.fromisoformat(expiry)
                            if promo_end_date.tzinfo is None:
                                promo_end_date = promo_end_date.replace(tzinfo=timezone.utc)
                        except (ValueError, TypeError):
                            pass

                    result.append(GameDealSchema(
                        title=item.get("title", "Unknown"),
                        original_price=float(deal.get("regular", {}).get("amount", 0)),
                        sale_price=float(deal.get("price", {}).get("amount", 0)),
                        store=deal.get("shop", {}).get("name", "Unknown"),
                        deal_id=item.get("id"),
                        url=deal.get("url", ""),
                        historical_low=float(deal.get("historyLow", {}).get("amount", 0)),
                        promo_start_date=promo_start_date,
                        promo_end_date=promo_end_date,
                        image_url=image_url
                    ))
                return result
        except Exception as e:
            logger.error(f"Error fetching deals from ITAD: {str(e)}")
            return []

    async def get_game_id_by_title(self, title: str) -> Optional[str]:
        """
        Searches for a game by title and returns its internal ITAD ID.
        Endpoint: /games/search/v1
        """
        url = f"{self.base_url}/games/search/v1"
        params = {"key": self.api_key, "title": title}

        try:
            headers = {"User-Agent": "GameDealTracker/1.0 (contato@teste.com)"}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers, timeout=10.0)
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
            headers = {"User-Agent": "GameDealTracker/1.0 (contato@teste.com)"}
            async with httpx.AsyncClient() as client:
                response = await client.post(url, params=params, json=payload, headers=headers, timeout=10.0)
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
