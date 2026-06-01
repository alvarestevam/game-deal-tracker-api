from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.core.database import get_db
from app.core.config import settings
from app.models.game import Game, GameOffer
from app.schemas.game import GameResponse, GameAuditResponse
from app.services.sync_service import sync_games
from app.core.limiter import limiter

router = APIRouter()

async def verify_sync_key(x_sync_api_key: str = Header(...)):
    if x_sync_api_key != settings.SYNC_API_KEY:
        raise HTTPException(status_code=401, detail="Sync API Key inválida ou ausente")

@router.post("/sync", dependencies=[Depends(verify_sync_key)])
@limiter.limit("5/minute")
async def manual_sync(request: Request):
    try:
        await sync_games()
        return {"message": "Sincronização iniciada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na sincronização: {str(e)}")

@router.get("/giveaways", response_model=List[GameResponse])
async def get_giveaways(request: Request, db: AsyncSession = Depends(get_db)):
    # Find games that have at least one active offer with current_price == 0
    # Or based on our previous logic where giveaways are specifically marked.
    # Now we have offers. We should return games that have at least one active offer with price 0.
    stmt = (
        select(Game)
        .join(Game.offers)
        .where(GameOffer.is_active == True, GameOffer.current_price == 0)
        .distinct()
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/deals", response_model=List[GameResponse])
async def get_deals(request: Request, db: AsyncSession = Depends(get_db)):
    # Return games that have at least one active offer.
    # Sorting is a bit tricky now since a game can have multiple offers with different prices.
    # Usually we want to sort by the best deal (lowest price).

    # Subquery to get the minimum active price per game
    min_price_sub = (
        select(GameOffer.game_id, func.min(GameOffer.current_price).label("min_price"))
        .where(GameOffer.is_active == True)
        .group_by(GameOffer.game_id)
        .subquery()
    )

    stmt = (
        select(Game)
        .join(min_price_sub, Game.id == min_price_sub.c.game_id)
        .order_by(min_price_sub.c.min_price.asc())
    )

    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/games/{title}/audit", response_model=List[GameAuditResponse])
async def audit_game(request: Request, title: str, db: AsyncSession = Depends(get_db)):
    # Find game in DB by title
    result = await db.execute(
        select(Game).where(Game.title.ilike(f"%{title}%"))
    )
    games = result.scalars().all()

    if not games:
        raise HTTPException(status_code=404, detail="Game not found in database")

    return games
