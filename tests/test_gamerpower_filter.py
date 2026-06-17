import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.gamerpower_client import GamerPowerClient

@pytest.mark.asyncio
async def test_gamerpower_type_filter():
    with patch.dict("os.environ", {
        "POSTGRES_SERVER": "localhost",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "password",
        "POSTGRES_DB": "testdb",
        "POSTGRES_PORT": "5432",
        "API_KEY": "test",
        "SYNC_API_KEY": "test"
    }):
        client = GamerPowerClient()
        mock_response = [
            {"id": 1, "title": "Real Game", "type": "Game", "platforms": "PC", "open_giveaway_url": "http://test.com/1"},
            {"id": 2, "title": "Some DLC", "type": "DLC", "platforms": "PC", "open_giveaway_url": "http://test.com/2"},
            {"id": 3, "title": "Some Loot", "type": "Loot", "platforms": "PC", "open_giveaway_url": "http://test.com/3"},
        ]

        with patch("app.services.gamerpower_client.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status = MagicMock()

            mock_client_instance.get.return_value = mock_resp

            deals = await client.get_pc_giveaways()

            # Now returns all items, filtering is handled by the sync service
            assert len(deals) == 3
            assert deals[0].title == "Real Game"
            assert deals[1].title == "Some DLC"
            assert deals[2].title == "Some Loot"
