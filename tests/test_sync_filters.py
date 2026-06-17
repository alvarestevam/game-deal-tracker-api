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
async def test_purist_pipeline_no_price_barrier():
    """Verifica que a barreira de preço original para giveaways foi removida."""
    client = AsyncMock(spec=httpx.AsyncClient)

    # Giveaway with original price < 20.00 (Should be TRUE now)
    item_cheap = GameDealSchema(title="Cheap Giveaway", sale_price=0.0, original_price=5.0, store="Steam", url="http")
    assert await _is_valid_deal(item_cheap, client) is True

    # Giveaway with missing original price (Should be TRUE now)
    item_missing = GameDealSchema(title="Unknown Giveaway", sale_price=0.0, store="Steam", url="http")
    assert await _is_valid_deal(item_missing, client) is True

@pytest.mark.asyncio
async def test_type_exclusion_rules_purist():
    """Verifica as novas regras de exclusão por tipo (purista)."""
    client = AsyncMock(spec=httpx.AsyncClient)

    # Blocked native types: ["dlc", "music", "advertising", "series"]
    assert await _is_valid_deal(GameDealSchema(title="DLC", sale_price=10.0, store="Steam", url="http", native_type="dlc"), client) is False
    assert await _is_valid_deal(GameDealSchema(title="Series", sale_price=10.0, store="Steam", url="http", native_type="series"), client) is False

    # Allowed native types (e.g. hardware was removed from blacklist)
    assert await _is_valid_deal(GameDealSchema(title="Hardware", sale_price=10.0, store="Steam", url="http", native_type="hardware"), client) is True

    # Blocked Steam types via API
    item_steam_series = GameDealSchema(title="Steam Series", sale_price=10.0, store="Steam", url="http", steam_appid="123")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"123": {"success": True, "data": {"type": "series"}}}
    client.get.return_value = mock_resp
    assert await _is_valid_deal(item_steam_series, client) is False

@pytest.mark.asyncio
async def test_trust_rule_logic():
    client = AsyncMock(spec=httpx.AsyncClient)

    # No native_type, no steam_appid, but valid store and price
    item = GameDealSchema(title="Trusted Game", sale_price=10.0, store="Steam", url="http")
    assert await _is_valid_deal(item, client) is True

    # No native_type, no steam_appid, but invalid store
    item_bad_store = GameDealSchema(title="Untrusted Store", sale_price=10.0, store="Unknown", url="http")
    assert await _is_valid_deal(item_bad_store, client) is False
