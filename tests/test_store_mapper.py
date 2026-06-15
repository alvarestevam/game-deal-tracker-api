from app.utils.store_mapper import map_store
from app.schemas.game import GameResponse, GameAuditResponse, OfferResponse
from uuid import uuid4
from datetime import datetime

def test_map_store_steam_id():
    result = map_store("1")
    assert result["name"] == "Steam"
    assert "google.com/s2/favicons" in result["store_icon_url"]

def test_map_store_epic_substring():
    result = map_store("Epic Games Store")
    assert result["name"] == "Epic Games Store"
    assert "google.com/s2/favicons" in result["store_icon_url"]

def test_map_store_gog_substring():
    result = map_store("GOG.com")
    assert result["name"] == "GOG"
    assert "google.com/s2/favicons" in result["store_icon_url"]

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

def test_offer_response_mapping():
    offer = OfferResponse(
        store_name="1",
        current_price=10.0,
        historical_low=5.0,
        is_active=True,
        updated_at=datetime.now()
    )
    assert offer.store_name == "Steam"
    assert offer.store_icon_url is not None
    assert "google.com/s2/favicons" in offer.store_icon_url

def test_game_response_image_fallback():
    game = GameResponse(
        id=uuid4(),
        title="Test Game",
        image_url=None,
        updated_at=datetime.now(),
        offers=[]
    )
    assert game.image_url == "https://via.placeholder.com/600x300.png?text=GamesInDeal+No+Image"

    game_empty = GameResponse(
        id=uuid4(),
        title="Test Game",
        image_url="",
        updated_at=datetime.now(),
        offers=[]
    )
    assert game_empty.image_url == "https://via.placeholder.com/600x300.png?text=GamesInDeal+No+Image"

def test_game_audit_response_mapping():
    offer = OfferResponse(
        store_name="epic games",
        current_price=10.0,
        historical_low=10.0,
        is_active=True,
        updated_at=datetime.now()
    )
    game = GameAuditResponse(
        title="Test Game",
        offers=[offer]
    )
    assert game.offers[0].store_name == "Epic Games Store"
    assert game.offers[0].store_icon_url is not None
    assert "google.com/s2/favicons" in game.offers[0].store_icon_url
    assert game.is_historical_low == True

def test_game_audit_response_image_fallback():
    game = GameAuditResponse(
        title="Test Game",
        image_url=None,
        offers=[]
    )
    assert game.image_url == "https://via.placeholder.com/600x300.png?text=GamesInDeal+No+Image"
