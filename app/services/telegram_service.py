import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def send_telegram_alert(game_title: str, current_price: float, historical_low: float, store_name: str, deal_url: str):
    """
    Envia um alerta de oferta para o canal do Telegram configurado.
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram Bot Token ou Chat ID não configurados. Pulando envio de alerta.")
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    # Formatação de preços
    price_str = f"{current_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    low_str = f"{historical_low:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Template HTML conforme instruções
    message = (
        "🔥 <b>OFERTA DE ELITE ENCONTRADA!</b> 🔥\n\n"
        f"🎮 <b>Jogo:</b> {game_title}\n"
        f"💰 <b>Preço Atual:</b> R$ {price_str}\n"
        f"📉 <b>Menor Preço Histórico:</b> R$ {low_str}\n"
        f"🏪 <b>Loja:</b> {store_name}"
    )

    # Configuração do Botão Inline
    button_text = "🎁 Resgatar Jogo" if current_price == 0 else "▶️ Ir para a Oferta"
    reply_markup = {
        "inline_keyboard": [
            [{"text": button_text, "url": deal_url}]
        ]
    }

    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": reply_markup
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.info(f"Alerta do Telegram enviado para o jogo: {game_title}")
            return True
    except Exception as e:
        logger.error(f"Erro ao enviar alerta para o Telegram: {str(e)}")
        return False
