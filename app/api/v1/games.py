from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, or_
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
    stmt = (
        select(Game)
        .join(Game.offers)
        .where(GameOffer.is_active == True, GameOffer.current_price == 0)
        .distinct()
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/deals/best", response_model=List[GameResponse])
async def get_best_deals(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Retorna as 15 melhores ofertas baseadas em Metacritic >= 75 ou maior desconto.
    """
    # Cálculo de percentual de desconto para ordenação fallback
    discount_percent = case(
        (GameOffer.original_price > 0, (1.0 - (GameOffer.current_price / GameOffer.original_price))),
        else_=0.0
    )

    stmt = (
        select(Game)
        .join(Game.offers)
        .where(
            GameOffer.is_active == True,
            Game.metacritic_score >= 75
        )
        .group_by(Game.id)
        .order_by(func.max(discount_percent).desc(), Game.metacritic_score.desc())
        .limit(15)
    )

    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/deals", response_model=List[GameResponse])
async def get_deals(request: Request, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Game)
        .join(Game.offers)
        .where(GameOffer.is_active == True)
        .group_by(Game.id)
        .order_by(Game.updated_at.desc())
    )

    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/games/{title}/audit", response_model=List[GameAuditResponse])
async def audit_game(request: Request, title: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Game).where(Game.title.ilike(f"%{title}%"))
    )
    games = result.scalars().all()

    if not games:
        raise HTTPException(status_code=404, detail="Game not found in database")

    return games
