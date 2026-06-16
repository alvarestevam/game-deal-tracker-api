from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from app.core.database import get_db
from app.models.game import Game, GameOffer
from app.schemas.telegram import TelegramPreviewResponse
from app.services.alert_service import calculate_deal_score

router = APIRouter()

@router.get("/deals/telegram-preview", response_model=List[TelegramPreviewResponse])
async def get_telegram_preview(db: AsyncSession = Depends(get_db)):
    """
    Exibe um preview de quais ofertas ativas no banco cumprem os requisitos de elite
    e de filtragem para envio ao Telegram.
    """
    stmt = (
        select(GameOffer)
        .options(selectinload(GameOffer.game))
        .where(GameOffer.is_active == True)
    )
    result = await db.execute(stmt)
    offers = result.scalars().all()

    preview_list = []
    for offer in offers:
        deal_score = calculate_deal_score(offer.game, offer)

        # Critérios de Elite: Preço 0 ou Deal Score >= 8.5
        if offer.current_price == 0 or deal_score >= 8.5:
            preview_list.append(
                TelegramPreviewResponse(
                    id=offer.id,
                    title=offer.game.title,
                    deal_score=deal_score,
                    current_price=offer.current_price,
                    store_name=offer.store_name,
                    notified_telegram=offer.notified_telegram
                )
            )

    return preview_list
