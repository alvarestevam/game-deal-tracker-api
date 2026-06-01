from app.utils.store_mapper import map_store
from app.schemas.game import GameResponse, GameAuditResponse
from uuid import uuid4
from datetime import datetime

def test_map_store_steam_id():
    result = map_store("1")
    assert result["name"] == "Steam"
    assert "Steam_icon_logo.svg.png" in result["store_icon_url"]

def test_map_store_epic_substring():
    result = map_store("Epic Games Store")
    assert result["name"] == "Epic Games Store"
    assert "Epic_Games_logo.svg.png" in result["store_icon_url"]

def test_map_store_gog_substring():
    result = map_store("GOG.com")
    assert result["name"] == "GOG"
    assert "GOG.com_logo.svg.png" in result["store_icon_url"]

def test_map_store_unknown():
    result = map_store("My Super Store")
    assert result["name"] == "My Super Store"
    assert "5260478.png" in result["store_icon_url"]

def test_map_store_aggressive_cleaning():
    # Test cases for aggressive cleaning
    assert map_store("Itch.io, DRM-Free")["name"] == "Itch.io"
    assert map_store("Steam, Windows")["name"] == "Steam"
    assert map_store("GenericStore, PC, ")["name"] == "GenericStore"
    assert map_store("Epic Games, Steam Key")["name"] == "Epic Games Store" # Mapped via substring "epic"

def test_game_response_mapping():
    game = GameResponse(
        id=uuid4(),
        title="Test Game",
        current_price=10.0,
        historical_low=5.0,
        is_free=False,
        store_name="1",
        is_active=True,
        updated_at=datetime.now()
    )
    assert game.store_name == "Steam"
    assert game.store_icon_url is not None
    assert "Steam_icon_logo.svg.png" in game.store_icon_url

def test_game_response_image_fallback():
    game = GameResponse(
        id=uuid4(),
        title="Test Game",
        current_price=10.0,
        historical_low=5.0,
        is_free=False,
        store_name="Steam",
        is_active=True,
        image_url=None,
        updated_at=datetime.now()
    )
    assert game.image_url == "https://via.placeholder.com/600x300.png?text=GamesInDeal+No+Image"

    game_empty = GameResponse(
        id=uuid4(),
        title="Test Game",
        current_price=10.0,
        historical_low=5.0,
        is_free=False,
        store_name="Steam",
        is_active=True,
        image_url="",
        updated_at=datetime.now()
    )
    assert game_empty.image_url == "https://via.placeholder.com/600x300.png?text=GamesInDeal+No+Image"

def test_game_audit_response_mapping():
    game = GameAuditResponse(
        title="Test Game",
        current_price=10.0,
        historical_low=5.0,
        is_historical_low=False,
        store_name="epic games",
        is_active=True
    )
    assert game.store_name == "Epic Games Store"
    assert game.store_icon_url is not None
    assert "Epic_Games_logo.svg.png" in game.store_icon_url

def test_game_audit_response_image_fallback():
    game = GameAuditResponse(
        title="Test Game",
        current_price=10.0,
        historical_low=5.0,
        is_historical_low=False,
        store_name="Steam",
        is_active=True,
        image_url=None
    )
    assert game.image_url == "https://via.placeholder.com/600x300.png?text=GamesInDeal+No+Image"
