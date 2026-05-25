from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models.game import Game
from app.schemas.game import GameResponse, GameAuditResponse
from app.services.sync_service import sync_games
from app.core.limiter import limiter

router = APIRouter()

@router.post("/sync")
@limiter.limit("5/minute")
async def manual_sync(request: Request):
    # This route will be protected by the global API key dependency in main.py
    # and will have a stricter rate limit
    try:
        await sync_games()
        return {"message": "Sincronização iniciada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na sincronização: {str(e)}")

@router.get("/giveaways", response_model=List[GameResponse])
async def get_giveaways(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Game.id,
            Game.title,
            Game.current_price,
            Game.historical_low,
            Game.is_free,
            Game.store_name,
            Game.deal_url,
            Game.promo_start_date,
            Game.promo_end_date,
            Game.updated_at
        ).where(Game.is_free == True)
    )
    return result.all()

@router.get("/deals", response_model=List[GameResponse])
async def get_deals(request: Request, db: AsyncSession = Depends(get_db)):
    # Sorted from lowest price (greatest discount) to highest
    result = await db.execute(
        select(
            Game.id,
            Game.title,
            Game.current_price,
            Game.historical_low,
            Game.is_free,
            Game.store_name,
            Game.deal_url,
            Game.promo_start_date,
            Game.promo_end_date,
            Game.updated_at
        ).order_by(Game.current_price.asc())
    )
    return result.all()

@router.get("/games/{title}/audit", response_model=GameAuditResponse)
async def audit_game(request: Request, title: str, db: AsyncSession = Depends(get_db)):
    # Find game in DB
    result = await db.execute(
        select(
            Game.title,
            Game.current_price,
            Game.historical_low,
            Game.store_name,
            Game.deal_url,
            Game.promo_start_date,
            Game.promo_end_date
        ).where(Game.title.ilike(f"%{title}%"))
    )
    game = result.first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found in database")

    return GameAuditResponse(
        title=game.title,
        current_price=game.current_price,
        historical_low=game.historical_low,
        is_historical_low=game.current_price <= game.historical_low,
        store_name=game.store_name,
        deal_url=game.deal_url,
        promo_start_date=game.promo_start_date,
        promo_end_date=game.promo_end_date
    )
