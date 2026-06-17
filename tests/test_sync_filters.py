import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.sync_service import _is_valid_deal
from app.schemas.game_deal import GameDealSchema
import httpx

@pytest.mark.asyncio
async def test_store_whitelist_validation():
    client = AsyncMock(spec=httpx.AsyncClient)

    # Valid elite stores
    assert await _is_valid_deal(GameDealSchema(title="Game 1", sale_price=10.0, store="Steam", url="http"), client) is True
    assert await _is_valid_deal(GameDealSchema(title="Game 2", sale_price=10.0, store="Epic Games Store", url="http"), client) is True
    assert await _is_valid_deal(GameDealSchema(title="Game 4", sale_price=10.0, store="Nuuvem", url="http"), client) is True

    # Invalid stores
    assert await _is_valid_deal(GameDealSchema(title="Game 3", sale_price=10.0, store="GOG", url="http"), client) is False
    assert await _is_valid_deal(GameDealSchema(title="Game 5", sale_price=10.0, store="Itch.io", url="http"), client) is False
    assert await _is_valid_deal(GameDealSchema(title="Game 6", sale_price=10.0, store="IndieGala", url="http"), client) is False

@pytest.mark.asyncio
async def test_giveaway_price_barrier():
    client = AsyncMock(spec=httpx.AsyncClient)

    # Giveaway with original price >= 20.00
    item_ok = GameDealSchema(title="Good Giveaway", sale_price=0.0, original_price=25.0, store="Steam", url="http")
    assert await _is_valid_deal(item_ok, client) is True

    # Giveaway with original price < 20.00
    item_bad = GameDealSchema(title="Cheap Giveaway", sale_price=0.0, original_price=15.0, store="Steam", url="http")
    assert await _is_valid_deal(item_bad, client) is False

    # Giveaway with missing original price (defaults to 0.0)
    item_missing = GameDealSchema(title="Unknown Giveaway", sale_price=0.0, store="Steam", url="http")
    assert await _is_valid_deal(item_missing, client) is False

@pytest.mark.asyncio
async def test_type_exclusion_rules():
    client = AsyncMock(spec=httpx.AsyncClient)

    # Blocked native types
    assert await _is_valid_deal(GameDealSchema(title="DLC", sale_price=10.0, store="Steam", url="http", native_type="dlc"), client) is False
    assert await _is_valid_deal(GameDealSchema(title="Music", sale_price=10.0, store="Steam", url="http", native_type="music"), client) is False

    # Blocked Steam types
    item_steam = GameDealSchema(title="Steam Item", sale_price=10.0, store="Steam", url="http", steam_appid="123")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"123": {"success": True, "data": {"type": "hardware"}}}
    client.get.return_value = mock_resp
    assert await _is_valid_deal(item_steam, client) is False

@pytest.mark.asyncio
async def test_trust_rule_logic():
    client = AsyncMock(spec=httpx.AsyncClient)

    # No native_type, no steam_appid, but valid store and price
    item = GameDealSchema(title="Trusted Game", sale_price=10.0, store="Steam", url="http")
    assert await _is_valid_deal(item, client) is True

    # No native_type, no steam_appid, but invalid store
    item_bad_store = GameDealSchema(title="Untrusted Store", sale_price=10.0, store="Unknown", url="http")
    assert await _is_valid_deal(item_bad_store, client) is False
