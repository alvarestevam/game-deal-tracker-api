import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.sync_service import _is_valid_deal
from app.schemas.game_deal import GameDealSchema
import httpx

@pytest.mark.asyncio
async def test_validation_stage1_native_type():
    client = AsyncMock(spec=httpx.AsyncClient)
    # Valid native type
    item_ok = GameDealSchema(title="Valid Game", sale_price=0, store="Steam", url="http", native_type="game")
    assert await _is_valid_deal(item_ok, client) is True

    # Invalid native type
    item_bad = GameDealSchema(title="DLC Pack", sale_price=0, store="Steam", url="http", native_type="DLC")
    assert await _is_valid_deal(item_bad, client) is False

@pytest.mark.asyncio
async def test_validation_stage2_steam_api():
    # Missing native_type, has steam_appid
    item = GameDealSchema(title="Steam Game", sale_price=0, store="Steam", url="http", steam_appid="123")
    client = AsyncMock(spec=httpx.AsyncClient)

    # Mocking Steam API response for DLC
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"123": {"success": True, "data": {"type": "dlc"}}}
    client.get.return_value = mock_resp

    assert await _is_valid_deal(item, client) is False

    # Mocking Steam API response for Game
    mock_resp.json.return_value = {"123": {"success": True, "data": {"type": "game"}}}
    assert await _is_valid_deal(item, client) is True

@pytest.mark.asyncio
async def test_validation_stage3_blacklist_and_regex():
    client = AsyncMock(spec=httpx.AsyncClient)
    # Blacklisted store
    item_store = GameDealSchema(title="Some Game", sale_price=0, store="Itch.io", url="http")
    assert await _is_valid_deal(item_store, client) is False

    # Regex title: giveaway suffix
    item_regex1 = GameDealSchema(title="Cool Game giveaway", sale_price=0, store="Steam", url="http")
    assert await _is_valid_deal(item_regex1, client) is False

    # Regex title: dlc suffix
    item_regex2 = GameDealSchema(title="Cool Game DLC", sale_price=0, store="Steam", url="http")
    assert await _is_valid_deal(item_regex2, client) is False

    # Regex title: indiegala tag
    item_regex3 = GameDealSchema(title="Cool Game (indiegala)", sale_price=0, store="Steam", url="http")
    assert await _is_valid_deal(item_regex3, client) is False

    # Valid game passes stage 3
    item_valid = GameDealSchema(title="Cyberpunk 2077", sale_price=0, store="Steam", url="http")
    assert await _is_valid_deal(item_valid, client) is True

@pytest.mark.asyncio
async def test_validation_stage2_to_stage3_flow():
    # Jogo no Steam, mas com "giveaway" no título.
    # Stage 2 deve aprovar (ou não descartar), Stage 3 deve barrar.
    item = GameDealSchema(title="Valid Steam Game giveaway", sale_price=0, store="Steam", url="http", steam_appid="123")
    client = AsyncMock(spec=httpx.AsyncClient)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"123": {"success": True, "data": {"type": "game"}}}
    client.get.return_value = mock_resp

    assert await _is_valid_deal(item, client) is False # Deve ser barrado pelo Stage 3 (regex)
