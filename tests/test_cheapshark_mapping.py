import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.cheapshark_client import CheapSharkClient

@pytest.mark.asyncio
async def test_cheapshark_store_mapping():
    with patch.dict("os.environ", {
        "POSTGRES_SERVER": "localhost",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "password",
        "POSTGRES_DB": "testdb",
        "POSTGRES_PORT": "5432",
        "API_KEY": "test",
        "SYNC_API_KEY": "test"
    }):
        client = CheapSharkClient()
        mock_deals = [
            {
                "gameID": "123",
                "title": "Steam Game",
                "storeID": "1",
                "salePrice": "10.00",
                "normalPrice": "20.00",
                "dealRating": "9.5",
                "dealID": "abc",
                "thumb": "http://test.com/img.jpg"
            },
            {
                "gameID": "456",
                "title": "Epic Game",
                "storeID": "25",
                "salePrice": "0.00",
                "normalPrice": "50.00",
                "dealRating": "10.0",
                "dealID": "def",
                "thumb": "http://test.com/img2.jpg"
            },
            {
                "gameID": "789",
                "title": "Unknown Store Game",
                "storeID": "999",
                "salePrice": "5.00",
                "normalPrice": "10.00",
                "dealRating": "9.0",
                "dealID": "ghi",
                "thumb": "http://test.com/img3.jpg"
            }
        ]

        with patch("app.services.cheapshark_client.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_deals
            mock_resp.raise_for_status = MagicMock()

            # For the deals request
            mock_client_instance.get.return_value = mock_resp

            deals = await client.get_deals()

            assert len(deals) == 3

            # Map results by title for easier assertion
            results = {d.title: d.store for d in deals}

            assert results["Steam Game"] == "Steam"
            assert results["Epic Game"] == "Epic Games Store"
            assert results["Unknown Store Game"] == "Loja Desconhecida"
