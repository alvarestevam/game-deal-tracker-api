import httpx
import logging
import time
from typing import Dict, List
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

# Memória para Rate Limiting: {chat_id: [timestamps]}
request_history: Dict[int, List[float]] = {}

@router.post("/telegram/webhook")
async def telegram_webhook(update: TelegramUpdate, db: AsyncSession = Depends(get_db)):
    if not update.message or not update.message.text:
        return {"status": "ignored"}

    text = update.message.text.lower().strip()
    chat_id = update.message.chat.id

    # --- Camada de Segurança: Rate Limiting ---
    now = time.time()
    if chat_id not in request_history:
        request_history[chat_id] = []

    # Limpa histórico antigo (mais de 5 segundos)
    request_history[chat_id] = [ts for ts in request_history[chat_id] if now - ts < 5]

    if len(request_history[chat_id]) >= 3:
        logger.warning(f"Rate limit atingido para chat_id: {chat_id}")

        # Opcionalmente devolve uma mensagem curta conforme instruções
        blocked_msg = "⚠️ Operação bloqueada temporariamente por excesso de requisições. Aguarde alguns segundos."
        telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": blocked_msg,
            "parse_mode": "HTML"
        }
        try:
            async with httpx.AsyncClient() as client:
                headers = {"User-Agent": "GameDealTracker/1.0 (contato@teste.com)"}
                await client.post(telegram_url, json=payload, headers=headers, timeout=5.0)
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de rate limit: {str(e)}")

        return {"status": "rate_limited"}

    # Registra a requisição atual
    request_history[chat_id].append(now)

    store_map = {
        "/steam": "Steam",
        "/epic": "Epic Games Store",
        "/gog": "GOG"
    }

    telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    headers = {"User-Agent": "GameDealTracker/1.0 (contato@teste.com)"}

    if text == "/start":
        message = "Bem-vindo ao GameDeal Tracker! 🎮\n\nEu monitoro as melhores ofertas de jogos para você.\n\nComandos:\n/steam - Ofertas na Steam\n/epic - Ofertas na Epic Games\n/gog - Ofertas na GOG\n/help - Lista de comandos"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
        async with httpx.AsyncClient() as client:
            await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)
    elif text == "/help":
        message = "🔍 <b>Comandos Disponíveis:</b>\n\n/steam - Melhores ofertas ativas na Steam\n/epic - Melhores ofertas ativas na Epic Games Store\n/gog - Melhores ofertas ativas na GOG\n/sobre - Sobre este projeto"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
        async with httpx.AsyncClient() as client:
            await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)
    elif text == "/sobre":
        message = "🚀 <b>GameDeal Tracker</b>\n\nDesenvolvido para encontrar as melhores promoções de jogos em diversas lojas.\nVersão 1.0"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
        async with httpx.AsyncClient() as client:
            await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)
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
            payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
            async with httpx.AsyncClient() as client:
                await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)
        else:
            # Envia cabeçalho da auditoria
            header_msg = f"🔍 <b>Auditoria de Ofertas: {target_store}</b>"
            async with httpx.AsyncClient() as client:
                await client.post(telegram_url, json={"chat_id": chat_id, "text": header_msg, "parse_mode": "HTML"}, headers=headers, timeout=10.0)

            # Envia cada oferta individualmente com botão inline
            async with httpx.AsyncClient() as client:
                for offer, score in top_offers:
                    price_str = "GRÁTIS" if offer.current_price == 0 else f"R$ {offer.current_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    msg = (
                        f"🎮 <b>{offer.game.title}</b>\n"
                        f"💰 Preço: {price_str} | ⭐ Nota: {score}/10"
                    )

                    button_text = "🎁 Resgatar Jogo" if offer.current_price == 0 else "▶️ Ir para a Oferta"
                    reply_markup = {
                        "inline_keyboard": [
                            [{"text": button_text, "url": offer.deal_url}]
                        ]
                    }

                    payload = {
                        "chat_id": chat_id,
                        "text": msg,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                        "reply_markup": reply_markup
                    }
                    await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)
    else:
        return {"status": "command_not_found"}

    return {"status": "success"}
