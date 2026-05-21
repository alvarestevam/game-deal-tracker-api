from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models.game import Game
from app.schemas.game import GameResponse, GameAuditResponse
from app.services.itad_client import ITADClient

router = APIRouter()

@router.get("/giveaways", response_model=List[GameResponse])
async def get_giveaways(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.is_free == True))
    return result.scalars().all()

@router.get("/deals", response_model=List[GameResponse])
async def get_deals(db: AsyncSession = Depends(get_db)):
    # Sorted from lowest price (greatest discount) to highest
    result = await db.execute(select(Game).order_by(Game.current_price.asc()))
    return result.scalars().all()

@router.get("/games/{title}/audit", response_model=GameAuditResponse)
async def audit_game(title: str, db: AsyncSession = Depends(get_db)):
    # Find game in DB
    result = await db.execute(select(Game).where(Game.title == title))
    game = result.scalars().first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found in database")

    # Real-time ITAD check
    itad_client = ITADClient()
    itad_id = await itad_client.get_game_id_by_title(title)

    if not itad_id:
        # Fallback to DB historical low if ITAD search fails
        return GameAuditResponse(
            title=game.title,
            current_price=game.current_price,
            historical_low=game.historical_low,
            is_historical_low=game.current_price <= game.historical_low
        )

    itad_low = await itad_client.get_historical_low(itad_id)

    if itad_low is None:
        itad_low = game.historical_low

    return GameAuditResponse(
        title=game.title,
        current_price=game.current_price,
        historical_low=itad_low,
        is_historical_low=game.current_price <= itad_low
    )
