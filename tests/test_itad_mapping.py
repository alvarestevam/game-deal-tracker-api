import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.itad_client import ITADClient
import httpx

@pytest.mark.asyncio
async def test_itad_get_deals_mapping():
    client = ITADClient()

    # Mock response data
    mock_response = {
        "list": [
            {
                "id": "game-123",
                "slug": "mortal-kombat-11",
                "title": "Mortal Kombat 11 Ultimate",
                "type": "game",
                "appid": 976310,
                "assets": {
                    "banner600": "http://image.com/600.jpg"
                },
                "deal": {
                    "shop": {"name": "Steam"},
                    "price": {"amount": 22.99, "currency": "BRL"},
                    "regular": {"amount": 229.99, "currency": "BRL"},
                    "url": "http://deal.com",
                    "historyLow": {"amount": 22.99, "currency": "BRL"},
                    "timestamp": "2024-10-01T15:25:52+02:00"
                }
            },
            {
                "id": "dlc-456",
                "slug": "mortal-kombat-11-kombat-pack",
                "title": "Mortal Kombat 11 Kombat Pack",
                "type": "dlc",
                "appid": 123456,
                "assets": {},
                "deal": {
                    "shop": {"name": "Steam"},
                    "price": {"amount": 10.00, "currency": "BRL"},
                    "regular": {"amount": 50.00, "currency": "BRL"},
                    "url": "http://deal-dlc.com",
                    "historyLow": {"amount": 5.00, "currency": "BRL"}
                }
            }
        ]
    }

    mock_httpx = MagicMock(spec=httpx.AsyncClient)
    mock_httpx.__aenter__.return_value = mock_httpx

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response
    mock_httpx.get.return_value = mock_resp

    # Patch httpx.AsyncClient in ITADClient.get_deals
    import app.services.itad_client
    original_client = app.services.itad_client.httpx.AsyncClient
    app.services.itad_client.httpx.AsyncClient = lambda: mock_httpx

    try:
        deals = await client.get_deals()

        assert len(deals) == 2

        # Test game mapping
        game = deals[0]
        assert game.title == "Mortal Kombat 11 Ultimate"
        assert game.sale_price == 22.99
        assert game.original_price == 229.99
        assert game.native_type == "game"
        assert game.steam_appid == "976310"
        assert game.store == "Steam"

        # Test DLC mapping
        dlc = deals[1]
        assert dlc.title == "Mortal Kombat 11 Kombat Pack"
        assert dlc.native_type == "dlc"
        assert dlc.steam_appid == "123456"

    finally:
        app.services.itad_client.httpx.AsyncClient = original_client

@pytest.mark.asyncio
async def test_itad_get_deals_params():
    client = ITADClient()

    mock_httpx = MagicMock(spec=httpx.AsyncClient)
    mock_httpx.__aenter__.return_value = mock_httpx

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"list": []}
    mock_httpx.get.return_value = mock_resp

    import app.services.itad_client
    original_client = app.services.itad_client.httpx.AsyncClient
    app.services.itad_client.httpx.AsyncClient = lambda: mock_httpx

    try:
        await client.get_deals()

        # Verify params
        args, kwargs = mock_httpx.get.call_args
        params = kwargs.get("params")
        assert params["country"] == "BR"
        assert params["currency"] == "BRL"
    finally:
        app.services.itad_client.httpx.AsyncClient = original_client
