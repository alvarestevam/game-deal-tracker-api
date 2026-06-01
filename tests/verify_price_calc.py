import uuid
from datetime import datetime
from app.schemas.game import GameResponse, GameAuditResponse

def test_game_response_price_calc():
    # 1. Free Game
    free_game = GameResponse(
        id=uuid.uuid4(),
        title="Free Game",
        current_price=0.0,
        historical_low=0.0,
        is_free=True,
        store_name="Steam",
        is_active=True,
        updated_at=datetime.utcnow()
    )
    print(f"Free Game: {free_game.estimated_final_price}")
    assert free_game.estimated_final_price == 0.0

    # 2. Nuuvem Game (National)
    nuuvem_game = GameResponse(
        id=uuid.uuid4(),
        title="Nuuvem Game",
        current_price=100.0,
        historical_low=80.0,
        is_free=False,
        store_name="Nuuvem",
        is_active=True,
        updated_at=datetime.utcnow()
    )
    print(f"Nuuvem Game: {nuuvem_game.estimated_final_price}")
    assert nuuvem_game.estimated_final_price == 100.0

    # 3. BRL National Store (Steam)
    steam_game = GameResponse(
        id=uuid.uuid4(),
        title="Steam Game",
        current_price=100.0,
        historical_low=80.0,
        is_free=False,
        store_name="Steam",
        is_active=True,
        updated_at=datetime.utcnow()
    )
    print(f"Steam Game: {steam_game.estimated_final_price}")
    assert steam_game.estimated_final_price == 100.0

    # 4. BRL National Store (Epic)
    epic_game = GameResponse(
        id=uuid.uuid4(),
        title="Epic Game",
        current_price=50.0,
        historical_low=40.0,
        is_free=False,
        store_name="Epic Games Store",
        is_active=True,
        updated_at=datetime.utcnow()
    )
    print(f"Epic Game: {epic_game.estimated_final_price}")
    assert epic_game.estimated_final_price == 50.0

    # 5. International Game (Gamesplanet)
    gp_game = GameResponse(
        id=uuid.uuid4(),
        title="Gamesplanet Game",
        current_price=100.0,
        historical_low=80.0,
        is_free=False,
        store_name="Gamesplanet",
        is_active=True,
        updated_at=datetime.utcnow()
    )
    print(f"Gamesplanet Game: {gp_game.estimated_final_price}")
    assert gp_game.estimated_final_price == 106.38

def test_game_audit_response_price_calc():
    # 1. Free Game
    free_game = GameAuditResponse(
        title="Free Game Audit",
        current_price=0.0,
        historical_low=0.0,
        is_historical_low=True,
        store_name="Steam",
        is_active=True
    )
    print(f"Free Game Audit: {free_game.estimated_final_price}")
    assert free_game.estimated_final_price == 0.0

    # 2. Nuuvem Game (National)
    nuuvem_game = GameAuditResponse(
        title="Nuuvem Game Audit",
        current_price=100.0,
        historical_low=80.0,
        is_historical_low=False,
        store_name="Nuuvem",
        is_active=True
    )
    print(f"Nuuvem Game Audit: {nuuvem_game.estimated_final_price}")
    assert nuuvem_game.estimated_final_price == 100.0

    # 3. BRL National Store (Steam)
    steam_game = GameAuditResponse(
        title="Steam Game Audit",
        current_price=100.0,
        historical_low=80.0,
        is_historical_low=False,
        store_name="Steam",
        is_active=True
    )
    print(f"Steam Game Audit: {steam_game.estimated_final_price}")
    assert steam_game.estimated_final_price == 100.0

if __name__ == "__main__":
    try:
        test_game_response_price_calc()
        test_game_audit_response_price_calc()
        print("All price calculation tests passed!")
    except AssertionError as e:
        print(f"Test failed!")
        raise e
