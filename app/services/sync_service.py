import logging
import httpx
import re
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, update
from app.core.database import AsyncSessionLocal
from app.models.game import Game, GameOffer
from app.services.gamerpower_client import GamerPowerClient
from app.services.cheapshark_client import CheapSharkClient
from app.services.itad_client import ITADClient
from app.utils.text_utils import normalize_title

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
            # Use headers for all external requests as per memory
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            usd_brl = data.get("USDBRL", {})
            bid = usd_brl.get("bid")
            if bid:
                return float(bid)
            raise ValueError("Cotação 'bid' não encontrada na resposta.")
    except Exception as e:
        logger.warning(f"Erro ao obter cotação do dólar: {str(e)}. Usando fallback de 5.00.")
        return 5.00

async def upsert_game(session: AsyncSession, title: str, price: float, is_free: bool, store_name: str | None = None, deal_url: str | None = None, promo_start_date: datetime | None = None, promo_end_date: datetime | None = None, is_active: bool = True, usd_rate: float | None = None, payload_historical_low: float | None = None, image_url: str | None = None):
    # Padronização de datas para naive UTC
    if promo_start_date:
        if promo_start_date.tzinfo is not None:
            promo_start_date = promo_start_date.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            promo_start_date = promo_start_date.replace(tzinfo=None)

    if promo_end_date:
        if promo_end_date.tzinfo is not None:
            promo_end_date = promo_end_date.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            promo_end_date = promo_end_date.replace(tzinfo=None)

    # Tratamento de strings longas
    title = title[:255] if title else "Unknown Title"
    deal_url = deal_url[:500] if deal_url else None
    image_url = image_url[:500] if image_url else None

    sanitized_image_url = _sanitize_steam_image_url(image_url)
    sanitized_image_url = _sanitize_gamesplanet_image_url(sanitized_image_url)

    actual_price = round(price * usd_rate, 2) if usd_rate else price
    actual_payload_low = round(payload_historical_low * usd_rate, 2) if payload_historical_low and usd_rate else payload_historical_low

    # Geração de slug para normalização e evitar duplicados
    slug = normalize_title(title)

    # Etapa 1: Find or Create Game
    result = await session.execute(select(Game).where(Game.slug == slug))
    game = result.scalars().first()

    if not game:
        game = Game(title=title, slug=slug, image_url=sanitized_image_url)
        session.add(game)
        await session.flush() # Ensure game.id is available
    else:
        # Update metadata if necessary
        if sanitized_image_url:
            game.image_url = sanitized_image_url

    # Etapa 2: Upsert GameOffer (game_id + store_name)
    offer_result = await session.execute(
        select(GameOffer).where(
            GameOffer.game_id == game.id,
            GameOffer.store_name == store_name
        )
    )
    offer = offer_result.scalars().first()

    # Calculate estimated final price
    brl_stores = ("Steam", "Epic Games Store", "Nuuvem")
    if actual_price == 0:
        est_final_price = 0.0
    elif store_name in brl_stores:
        est_final_price = actual_price
    else:
        est_final_price = round(actual_price * 1.0638, 2)

    if offer:
        offer.current_price = actual_price
        offer.estimated_final_price = est_final_price
        offer.deal_url = deal_url
        offer.promo_start_date = promo_start_date
        offer.promo_end_date = promo_end_date
        offer.is_active = is_active

        # Update historical low
        candidates = [offer.historical_low, actual_price]
        if actual_payload_low is not None:
            candidates.append(actual_payload_low)
        offer.historical_low = round(min(candidates), 2)
    else:
        initial_low = actual_price
        if actual_payload_low is not None:
            initial_low = round(min(actual_price, actual_payload_low), 2)

        new_offer = GameOffer(
            game_id=game.id,
            store_name=store_name,
            current_price=actual_price,
            historical_low=initial_low,
            estimated_final_price=est_final_price,
            deal_url=deal_url,
            promo_start_date=promo_start_date,
            promo_end_date=promo_end_date,
            is_active=is_active
        )
        session.add(new_offer)

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
                # Deativa todas as ofertas antes de sincronizar
                await session.execute(text("UPDATE game_offers SET is_active = False"))

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

                await session.commit()
                logger.info("Game synchronization completed successfully.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Database error during synchronization: {str(e)}")
                raise
    except Exception as e:
        logger.error(f"Error during game synchronization: {str(e)}")
