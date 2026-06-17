from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from app.core.database import get_db
from app.models.game import Game, GameOffer
from app.schemas.telegram import TelegramPreviewResponse

router = APIRouter()

@router.get("/deals/telegram-preview", response_model=List[TelegramPreviewResponse])
async def get_telegram_preview(db: AsyncSession = Depends(get_db)):
    """
    Exibe um preview de todas as ofertas ativas no banco para envio ao Telegram.
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
        # Purismo: Todas as ofertas ativas são consideradas candidatas
        preview_list.append(
            TelegramPreviewResponse(
                id=offer.id,
                title=offer.game.title,
                current_price=offer.current_price,
                store_name=offer.store_name,
                notified_telegram=offer.notified_telegram
            )
        )

    return preview_list
