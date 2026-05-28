import logging
import httpx
import re
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, update
from app.core.database import AsyncSessionLocal
from app.models.game import Game
from app.services.gamerpower_client import GamerPowerClient
from app.services.cheapshark_client import CheapSharkClient
from app.services.itad_client import ITADClient

logger = logging.getLogger(__name__)

def _sanitize_steam_image_url(image_url: str | None) -> str | None:
    """Transforma URLs de miniaturas da Steam em imagens de alta resolução."""
    if not image_url:
        return image_url

    if "steamstatic" in image_url or "steam" in image_url:
        # Substitui sufixos de baixa resolução (como capsule_sm_120.jpg) pelo padrão de alta resolução
        return re.sub(r"capsule_.*\.jpg", "header.jpg", image_url)

    return image_url

def _sanitize_gamesplanet_image_url(image_url: str | None) -> str | None:
    """Transforma URLs de miniaturas da Gamesplanet em imagens de alta resolução."""
    if not image_url:
        return image_url

    if "gamesplanet.com" in image_url or "gpstatic.com" in image_url:
        # Substitui prefixos de dimensões pelo padrão de alta resolução 'packshot-'
        # Conforme a instrução, usa-se .replace() para a substituição
        new_url = image_url.replace("t280x115-", "packshot-")
        new_url = new_url.replace("t500x500-", "packshot-")
        new_url = new_url.replace("t620x300-", "packshot-")
        new_url = new_url.replace("t300x170-", "packshot-")

        # Remove sufixos de baixa resolução
        new_url = new_url.replace("_small", "")
        new_url = new_url.replace("_thumb", "")

        return new_url

    return image_url

async def get_usd_brl_rate() -> float:
    """Consulta a AwesomeAPI para obter a cotação atual do USD para BRL."""
    url = "https://economia.awesomeapi.com.br/last/USD-BRL"
    headers = {"User-Agent": "GameDealTracker/1.0 (contato@teste.com)"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            # Uso robusto do .get() para acessar a cotação
            usd_brl = data.get("USDBRL", {})
            bid = usd_brl.get("bid")
            if bid:
                return float(bid)
            raise ValueError("Cotação 'bid' não encontrada na resposta.")
    except Exception as e:
        logger.warning(f"Erro ao obter cotação do dólar: {str(e)}. Usando fallback de 5.00.")
        return 5.00

async def upsert_game(session: AsyncSession, title: str, price: float, is_free: bool, store_name: str | None = None, deal_url: str | None = None, promo_start_date: datetime | None = None, promo_end_date: datetime | None = None, is_active: bool = True, usd_rate: float | None = None, payload_historical_low: float | None = None, image_url: str | None = None):
    # Padronização de datas para UTC
    if promo_start_date:
        if promo_start_date.tzinfo is None:
            promo_start_date = promo_start_date.replace(tzinfo=timezone.utc)
        else:
            promo_start_date = promo_start_date.astimezone(timezone.utc)

    if promo_end_date:
        if promo_end_date.tzinfo is None:
            promo_end_date = promo_end_date.replace(tzinfo=timezone.utc)
        else:
            promo_end_date = promo_end_date.astimezone(timezone.utc)

    # Tratamento de strings longas para evitar erros de DBAPI (estouro de limite de caracteres)
    title = title[:255] if title else "Unknown Title"
    deal_url = deal_url[:500] if deal_url else None
    image_url = image_url[:500] if image_url else None

    # Higienização de URL de imagem para Steam
    sanitized_image_url = _sanitize_steam_image_url(image_url)
    # Higienização de URL de imagem para Gamesplanet
    sanitized_image_url = _sanitize_gamesplanet_image_url(sanitized_image_url)

    # Converte o preço e o historical_low do payload se uma taxa for fornecida (vinda do CheapShark)
    actual_price = round(price * usd_rate, 2) if usd_rate else price
    actual_payload_low = round(payload_historical_low * usd_rate, 2) if payload_historical_low and usd_rate else payload_historical_low

    result = await session.execute(select(Game).where(Game.title == title))
    game = result.scalars().first()

    if game:
        game.current_price = actual_price
        game.is_free = is_free
        game.store_name = store_name
        game.deal_url = deal_url
        game.promo_start_date = promo_start_date
        game.promo_end_date = promo_end_date
        game.is_active = is_active
        # Atualiza image_url vinda do payload (thumb no CheapShark / image no GamerPower)
        game.image_url = sanitized_image_url

        # Atualiza o historical_low comparando o valor atual no DB com o do payload e o novo preço
        candidates = [game.historical_low, actual_price]
        if actual_payload_low is not None:
            candidates.append(actual_payload_low)
        game.historical_low = round(min(candidates), 2)
    else:
        # Se não houver payload_historical_low, usa o actual_price como inicial
        initial_low = actual_price
        if actual_payload_low is not None:
            initial_low = round(min(actual_price, actual_payload_low), 2)

        new_game = Game(
            title=title,
            current_price=actual_price,
            historical_low=initial_low,
            is_free=is_free,
            store_name=store_name,
            deal_url=deal_url,
            promo_start_date=promo_start_date,
            promo_end_date=promo_end_date,
            is_active=is_active,
            # Persiste image_url vinda do payload
            image_url=sanitized_image_url
        )
        session.add(new_game)

async def sync_games():
    logger.info("Starting game synchronization...")
    gp_client = GamerPowerClient()
    cs_client = CheapSharkClient()
    itad_client = ITADClient()

    try:
        usd_rate = await get_usd_brl_rate()
        logger.info(f"Cotação do dólar obtida: {usd_rate}")

        giveaways = await gp_client.get_pc_giveaways()
        deals = await cs_client.get_deals()
        itad_deals = await itad_client.get_deals()

        async with AsyncSessionLocal() as session:
            try:
                # Desativa temporariamente todos os jogos do CheapShark (identificados por store_name numérico)
                await session.execute(text("UPDATE games SET is_active = False WHERE store_name ~ '^[0-9]+$'"))

                # Process giveaways
                for item in giveaways:
                    try:
                        async with session.begin_nested():
                            await upsert_game(session, item.title, item.sale_price, True, item.store, item.url, item.promo_start_date, item.promo_end_date, is_active=True, image_url=item.image_url)
                    except Exception as e:
                        logger.error(f"Error syncing giveaway '{item.title}': {str(e)}")

                # Process deals
                for item in deals:
                    try:
                        async with session.begin_nested():
                            # Aplica a conversão de USD para BRL e define is_active = True
                            await upsert_game(
                                session,
                                item.title,
                                item.sale_price,
                                item.sale_price == 0,
                                item.store,
                                item.url,
                                item.promo_start_date,
                                item.promo_end_date,
                                is_active=True,
                                usd_rate=usd_rate,
                                payload_historical_low=item.historical_low,
                                image_url=item.image_url
                            )
                    except Exception as e:
                        logger.error(f"Error syncing CheapShark deal '{item.title}': {str(e)}")

                # Process ITAD deals
                for item in itad_deals:
                    try:
                        async with session.begin_nested():
                            await upsert_game(
                                session,
                                item.title,
                                item.sale_price,
                                item.sale_price == 0,
                                item.store,
                                item.url,
                                item.promo_start_date,
                                item.promo_end_date,
                                is_active=True,
                                usd_rate=usd_rate,
                                payload_historical_low=item.historical_low,
                                image_url=item.image_url
                            )
                    except Exception as e:
                        logger.error(f"Error syncing ITAD deal '{item.title}': {str(e)}")

                logger.info(f"ITAD sync: {len(itad_deals)} deals processed")

                await session.commit()
                logger.info("Game synchronization completed successfully.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Database error during synchronization: {str(e)}")
                raise
    except Exception as e:
        logger.error(f"Error during game synchronization: {str(e)}")
