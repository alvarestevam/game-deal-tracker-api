import httpx
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.config import settings
from app.models.game import Game, GameOffer
from app.schemas.telegram import TelegramUpdate
from app.services.alert_service import calculate_deal_score

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/telegram/webhook")
async def telegram_webhook(update: TelegramUpdate, db: AsyncSession = Depends(get_db)):
    if not update.message or not update.message.text:
        return {"status": "ignored"}

    text = update.message.text.lower().strip()
    chat_id = update.message.chat.id

    store_map = {
        "/steam": "Steam",
        "/epic": "Epic Games Store",
        "/gog": "GOG"
    }

    if text == "/start":
        message = "Bem-vindo ao GameDeal Tracker! 🎮\n\nEu monitoro as melhores ofertas de jogos para você.\n\nComandos:\n/steam - Ofertas na Steam\n/epic - Ofertas na Epic Games\n/gog - Ofertas na GOG\n/help - Lista de comandos"
    elif text == "/help":
        message = "🔍 <b>Comandos Disponíveis:</b>\n\n/steam - Melhores ofertas ativas na Steam\n/epic - Melhores ofertas ativas na Epic Games Store\n/gog - Melhores ofertas ativas na GOG\n/sobre - Sobre este projeto"
    elif text == "/sobre":
        message = "🚀 <b>GameDeal Tracker</b>\n\nDesenvolvido para encontrar as melhores promoções de jogos em diversas lojas.\nVersão 1.0"
    elif text in store_map:
        target_store = store_map[text]

        # Query active offers for the requested store
        stmt = (
            select(GameOffer)
            .options(selectinload(GameOffer.game))
            .where(GameOffer.is_active == True, GameOffer.store_name.ilike(f"%{target_store}%"))
        )
        result = await db.execute(stmt)
        offers = result.scalars().all()

        # Calculate scores and sort
        scored_offers = []
        for offer in offers:
            score = calculate_deal_score(offer.game, offer)
            scored_offers.append((offer, score))

        # Sort by score descending and limit 15
        scored_offers.sort(key=lambda x: x[1], reverse=True)
        top_offers = scored_offers[:15]

        if not top_offers:
            message = f"Nenhuma oferta ativa encontrada para <b>{target_store}</b> no momento."
        else:
            message = f"🔍 <b>Auditoria de Ofertas: {target_store}</b>\n\n"
            for offer, score in top_offers:
                price_str = "GRÁTIS" if offer.current_price == 0 else f"R$ {offer.current_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                message += f"🎮 <b>{offer.game.title}</b>\n"
                message += f"💰 Preço: {price_str} | ⭐ Nota: {score}/10\n"
                message += f"🔗 <a href='{offer.deal_url}'>Ver Oferta</a>\n\n"
    else:
        return {"status": "command_not_found"}

    # Send message back to Telegram
    telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        async with httpx.AsyncClient() as client:
            # All outgoing httpx requests to external APIs must include the header: headers={"User-Agent": "GameDealTracker/1.0 (contato@teste.com)"}
            headers = {"User-Agent": "GameDealTracker/1.0 (contato@teste.com)"}
            response = await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()
    except Exception as e:
        logger.error(f"Erro ao enviar resposta de auditoria para o Telegram: {str(e)}")

    return {"status": "success"}
