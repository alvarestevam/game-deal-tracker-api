import httpx
import logging
import time
from typing import Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.config import settings
from app.models.game import Game, GameOffer
from app.models.user_alert import UserAlert
from app.schemas.telegram import TelegramUpdate

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
        message = (
            "Bem-vindo ao GameDeal Tracker! 🎮\n\n"
            "Eu monitoro as melhores ofertas de jogos para você.\n\n"
            "<b>Comandos:</b>\n"
            "/steam - Ofertas na Steam\n"
            "/epic - Ofertas na Epic Games Store\n"
            "/gog - Ofertas na GOG\n"
            "/buscar &lt;termo&gt; - Pesquisar ofertas ativas\n"
            "/alerta &lt;termo&gt; - Criar alerta personalizado\n"
            "/meus_alertas - Listar meus alertas\n"
            "/remover_alerta &lt;termo&gt; - Remover alerta\n"
            "/help - Lista de comandos"
        )
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
        async with httpx.AsyncClient() as client:
            await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)
    elif text == "/help":
        message = (
            "🔍 <b>Comandos Disponíveis:</b>\n\n"
            "/steam - Melhores ofertas ativas na Steam\n"
            "/epic - Melhores ofertas ativas na Epic Games Store\n"
            "/gog - Melhores ofertas ativas na GOG\n"
            "/buscar &lt;termo&gt; - Pesquisar ofertas ativas por título\n"
            "/alerta &lt;termo&gt; - Receber notificação na DM quando o jogo entrar em promoção\n"
            "/meus_alertas - Listar todos os seus alertas ativos\n"
            "/remover_alerta &lt;termo&gt; - Remover um alerta existente\n"
            "/sobre - Sobre este projeto"
        )
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
        async with httpx.AsyncClient() as client:
            await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)
    elif text == "/sobre":
        message = "🚀 <b>GameDeal Tracker</b>\n\nDesenvolvido para encontrar as melhores promoções de jogos em diversas lojas.\nVersão 1.0"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
        async with httpx.AsyncClient() as client:
            await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)
    elif text.startswith("/buscar "):
        term = text.replace("/buscar ", "").strip()
        if not term:
            message = "⚠️ Por favor, digite um termo para buscar. Ex: <code>/buscar witcher</code>"
            payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
            async with httpx.AsyncClient() as client:
                await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)
        else:
            stmt = (
                select(GameOffer)
                .join(Game)
                .options(selectinload(GameOffer.game))
                .where(GameOffer.is_active == True, Game.title.ilike(f"%{term}%"))
                .order_by(desc(GameOffer.updated_at))
                .limit(5)
            )
            result = await db.execute(stmt)
            offers = result.scalars().all()

            if not offers:
                message = f"Não encontrei nenhuma oferta ativa para '<b>{term}</b>'. Vou continuar monitorando! 🧐"
                payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
                async with httpx.AsyncClient() as client:
                    await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)
            else:
                header_msg = f"🔎 <b>Resultados para: {term}</b>"
                async with httpx.AsyncClient() as client:
                    await client.post(telegram_url, json={"chat_id": chat_id, "text": header_msg, "parse_mode": "HTML"}, headers=headers, timeout=10.0)

                async with httpx.AsyncClient() as client:
                    for offer in offers:
                        price_str = "GRÁTIS" if offer.current_price == 0 else f"R$ {offer.current_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        msg = (
                            f'<a href="{offer.deal_url}">&#8203;</a>'
                            f"🎮 <b>{offer.game.title}</b>\n"
                            f"💰 Preço: {price_str}\n"
                            f"🏪 Loja: {offer.store_name}"
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
                            "disable_web_page_preview": False,
                            "reply_markup": reply_markup
                        }
                        await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)

    elif text == "/meus_alertas":
        stmt = select(UserAlert).where(UserAlert.chat_id == chat_id)
        result = await db.execute(stmt)
        alerts = result.scalars().all()

        if not alerts:
            message = "Você não possui alertas configurados. Use <code>/alerta &lt;termo&gt;</code> para criar um!"
        else:
            message = "🔔 <b>Seus Alertas Ativos:</b>\n\n"
            for alert in alerts:
                message += f"• <code>{alert.keyword}</code>\n"
            message += "\nPara remover, use <code>/remover_alerta &lt;termo&gt;</code>"

        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        async with httpx.AsyncClient() as client:
            await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)

    elif text.startswith("/alerta "):
        term = text.replace("/alerta ", "").strip()
        if not term:
            message = "⚠️ Por favor, digite um termo para o alerta. Ex: <code>/alerta cyberpunk</code>"
        else:
            # Verifica se já existe
            stmt = select(UserAlert).where(UserAlert.chat_id == chat_id, UserAlert.keyword == term.lower())
            result = await db.execute(stmt)
            if result.scalars().first():
                message = f"✅ Você já tem um alerta para '<b>{term}</b>'!"
            else:
                new_alert = UserAlert(chat_id=chat_id, keyword=term.lower())
                db.add(new_alert)
                await db.commit()
                message = f"🔔 Alerta criado! Vou te avisar na DM assim que '<b>{term}</b>' entrar em promoção."

        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        async with httpx.AsyncClient() as client:
            await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)

    elif text.startswith("/remover_alerta"):
        term = text.replace("/remover_alerta", "").strip()
        if not term:
            message = "⚠️ Por favor, digite o termo do alerta a remover. Ex: <code>/remover_alerta cyberpunk</code>"
        else:
            stmt = delete(UserAlert).where(UserAlert.chat_id == chat_id, UserAlert.keyword == term.lower())
            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount > 0:
                message = f"🗑️ Alerta para '<b>{term}</b>' removido com sucesso."
            else:
                message = f"❌ Não encontrei nenhum alerta ativo para '<b>{term}</b>'."

        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        async with httpx.AsyncClient() as client:
            await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)

    elif text in store_map:
        target_store = store_map[text]

        # Query active offers for the requested store
        stmt = (
            select(GameOffer)
            .options(selectinload(GameOffer.game))
            .where(GameOffer.is_active == True, GameOffer.store_name.ilike(f"%{target_store}%"))
            .order_by(desc(GameOffer.updated_at))
            .limit(15)
        )
        result = await db.execute(stmt)
        offers = result.scalars().all()

        if not offers:
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
                for offer in offers:
                    price_str = "GRÁTIS" if offer.current_price == 0 else f"R$ {offer.current_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    msg = (
                        f'<a href="{offer.deal_url}">&#8203;</a>'
                        f"🎮 <b>{offer.game.title}</b>\n"
                        f"💰 Preço: {price_str}\n"
                        f"🏪 Loja: {offer.store_name}"
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
                        "disable_web_page_preview": False,
                        "reply_markup": reply_markup
                    }
                    await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)
    else:
        return {"status": "command_not_found"}

    return {"status": "success"}
