import logging
import httpx
import re
import time
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, update
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.game import Game, GameOffer
from app.models.user_alert import UserAlert
from app.services.gamerpower_client import GamerPowerClient
from app.services.cheapshark_client import CheapSharkClient
from app.services.itad_client import ITADClient
from app.services.alert_service import calculate_deal_score
from app.services.telegram_service import send_telegram_alert
from app.utils.text_utils import normalize_title
from app.schemas.game_deal import GameDealSchema

logger = logging.getLogger(__name__)

ELITE_STORES = ["steam", "epic games", "gog", "prime gaming", "green man gaming", "gamesplanet", "nuuvem"]
BLOCKED_TYPES = ["dlc", "music", "advertising", "hardware"]

async def _is_valid_deal(item: GameDealSchema, client: httpx.AsyncClient) -> bool:
    """
    Pipeline de validação heurística:
    1. Whitelist de Lojas (Nível A)
    2. Barreira Econômica para Giveaways (> R$ 20)
    3. Filtro de Tipagem (DLCs, Music, etc.)
    4. Regra de Confiança (Fallback)
    """
    # 1. Whitelist de Lojas (Elite Stores)
    store_lower = item.store.lower() if item.store else ""
    if not any(elite in store_lower for elite in ELITE_STORES):
        logger.info(f"Discarding {item.title}: Store '{item.store}' is not in elite whitelist.")
        return False

    # 2. Barreira Econômica para Giveaways
    if item.sale_price == 0 or item.is_giveaway:
        original_price = item.original_price or 0.0
        if original_price < 20.00:
            logger.info(f"Discarding giveaway {item.title}: Original price {original_price} is below barrier (20.00).")
            return False

    # 3. Filtro de Tipagem (Nativo)
    if item.native_type:
        if item.native_type.lower() in BLOCKED_TYPES:
            logger.info(f"Discarding {item.title}: Native type '{item.native_type}' is blocked.")
            return False

    # 4. Filtro de Tipagem (Fallback Steam API)
    if item.steam_appid and item.steam_appid != "0":
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={item.steam_appid}"
            headers = {"User-Agent": "GameDealTracker/1.0 (contato@teste.com)"}
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                app_data = data.get(str(item.steam_appid))
                if app_data and app_data.get("success"):
                    steam_type = app_data.get("data", {}).get("type")
                    if steam_type in BLOCKED_TYPES:
                        logger.info(f"Discarding {item.title}: Steam type '{steam_type}' is blocked.")
                        return False
        except Exception as e:
            logger.warning(f"Error checking Steam API for {item.title} ({item.steam_appid}): {str(e)}")

    # 5. Regra de Confiança: Se passou pelos filtros acima, é aprovado
    return True

def _sanitize_steam_image_url(image_url: str | None) -> str | None:
    """
    Transforma URLs de miniaturas da Steam em imagens de alta resolução e aplica
    rewrite estrutural para a CDN da Akamai (bypass de bloqueio WAF/Hotlink).
    """
    if not image_url:
        return image_url

    # 1. Rewrite estrutural para Akamai (Padrão: .../steam/apps/{app_id}/...)
    steam_app_match = re.search(r"steam/apps/(\d+)", image_url)
    if steam_app_match and ("steamstatic" in image_url or "steam" in image_url):
        app_id = steam_app_match.group(1)
        return f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"

    # 2. Fallback para outros padrões steamstatic que não contenham /apps/
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

async def upsert_game(session: AsyncSession, title: str, price: float, is_free: bool, store_name: str | None = None, deal_url: str | None = None, promo_start_date: datetime | None = None, promo_end_date: datetime | None = None, is_active: bool = True, usd_rate: float | None = None, payload_historical_low: float | None = None, image_url: str | None = None, metacritic_score: int | None = None, original_price: float | None = None):
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
    actual_original_price = round(original_price * usd_rate, 2) if original_price and usd_rate else original_price
    actual_payload_low = round(payload_historical_low * usd_rate, 2) if payload_historical_low and usd_rate else payload_historical_low

    # Geração de slug para normalização e evitar duplicados
    slug = normalize_title(title)

    # Etapa 1: Find or Create Game
    result = await session.execute(select(Game).where(Game.slug == slug))
    game = result.scalars().first()

    if not game:
        game = Game(title=title, slug=slug, image_url=sanitized_image_url, metacritic_score=metacritic_score)
        session.add(game)
        await session.flush() # Ensure game.id is available
    else:
        # Update metadata if necessary
        if sanitized_image_url:
            game.image_url = sanitized_image_url
        if metacritic_score:
            game.metacritic_score = metacritic_score

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
        offer.original_price = actual_original_price
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
            original_price=actual_original_price,
            historical_low=initial_low,
            estimated_final_price=est_final_price,
            deal_url=deal_url,
            promo_start_date=promo_start_date,
            promo_end_date=promo_end_date,
            is_active=is_active
        )
        session.add(new_offer)

async def sync_games():
    start_time = time.perf_counter()
    logger.info("Starting game synchronization...")

    # Telemetria
    total_processed_offers = 0
    external_apis = set()
    processed_stores = set()
    new_elite_offers = 0
    dm_alerts_sent = 0
    db_status = "Saudável"

    gp_client = GamerPowerClient()
    cs_client = CheapSharkClient()
    itad_client = ITADClient()

    try:
        usd_rate = await get_usd_brl_rate()
        logger.info(f"Cotação do dólar obtida: {usd_rate}")

        giveaways = await gp_client.get_pc_giveaways()
        if giveaways:
            external_apis.add("GamerPower")
            total_processed_offers += len(giveaways)

        deals = await cs_client.get_deals()
        if deals:
            external_apis.add("CheapShark")
            total_processed_offers += len(deals)

        itad_deals = await itad_client.get_deals()
        if itad_deals:
            external_apis.add("IsThereAnyDeal")
            total_processed_offers += len(itad_deals)

        async with httpx.AsyncClient() as http_client, AsyncSessionLocal() as session:
            # Teste de integridade do banco
            try:
                await session.execute(text("SELECT 1"))
            except Exception as e:
                db_status = f"Erro: {str(e)}"
                logger.error(f"Falha na integridade do banco: {str(e)}")

            try:
                # Deativa todas as ofertas antes de sincronizar
                await session.execute(text("UPDATE game_offers SET is_active = False"))

                # Process giveaways
                for item in giveaways:
                    if not await _is_valid_deal(item, http_client):
                        continue

                    processed_stores.add(item.store or "Unknown")
                    try:
                        async with session.begin_nested():
                            await upsert_game(
                                session,
                                item.title,
                                item.sale_price,
                                True,
                                item.store,
                                item.url,
                                item.promo_start_date,
                                item.promo_end_date,
                                is_active=True,
                                image_url=item.image_url,
                                metacritic_score=item.metacritic_score,
                                original_price=item.original_price
                            )
                    except Exception as e:
                        logger.error(f"Error syncing giveaway '{item.title}': {str(e)}")

                # Process deals
                for item in deals:
                    if not await _is_valid_deal(item, http_client):
                        continue

                    store_name = item.store
                    if store_name == "1": store_name = "Steam"
                    processed_stores.add(store_name or "Unknown")
                    try:
                        # Se for Steam na CheapShark, não converte (já vem em BRL)
                        effective_rate = 1.0 if item.store in ("1", "Steam") else usd_rate
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
                                usd_rate=effective_rate,
                                payload_historical_low=item.historical_low,
                                image_url=item.image_url,
                                metacritic_score=item.metacritic_score,
                                original_price=item.original_price
                            )
                    except Exception as e:
                        logger.error(f"Error syncing CheapShark deal '{item.title}': {str(e)}")

                # Process ITAD deals
                for item in itad_deals:
                    if not await _is_valid_deal(item, http_client):
                        continue

                    processed_stores.add(item.store or "Unknown")
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
                                image_url=item.image_url,
                                metacritic_score=item.metacritic_score,
                                original_price=item.original_price
                            )
                    except Exception as e:
                        logger.error(f"Error syncing ITAD deal '{item.title}': {str(e)}")

                await session.commit()
                logger.info("Game synchronization completed successfully. Starting Telegram notifications...")

                # Despacho de notificações Telegram
                try:
                    # Busca ofertas ativas não notificadas
                    stmt = (
                        select(GameOffer)
                        .options(selectinload(GameOffer.game))
                        .where(GameOffer.is_active == True, GameOffer.notified_telegram == False)
                    )
                    result = await session.execute(stmt)
                    pending_offers = result.scalars().all()

                    for offer in pending_offers:
                        deal_score = calculate_deal_score(offer.game, offer)

                        # Critérios de Elite: Preço 0 ou Deal Score >= 7.0
                        if offer.current_price == 0 or deal_score >= 7.0:
                            new_elite_offers += 1
                            success = await send_telegram_alert(
                                game_title=offer.game.title,
                                current_price=offer.current_price,
                                historical_low=offer.historical_low,
                                store_name=offer.store_name,
                                deal_url=offer.deal_url
                            )
                            if success:
                                offer.notified_telegram = True
                        else:
                            # Se não é elite, marcamos como notificado para não avaliar novamente
                            offer.notified_telegram = True

                    await session.commit()
                    logger.info("Processamento de notificações Telegram (Canal) finalizado.")

                    # --- Rotina de Alertas Privados ---
                    try:
                        # Busca todos os alertas ativos
                        stmt_alerts = select(UserAlert)
                        result_alerts = await session.execute(stmt_alerts)
                        user_alerts = result_alerts.scalars().all()

                        if user_alerts:
                            # Re-identifica ofertas de elite do ciclo atual (que acabaram de ser processadas)
                            # Para simplificar, usamos as mesmas pending_offers e aplicamos o filtro de elite
                            for offer in pending_offers:
                                deal_score = calculate_deal_score(offer.game, offer)
                                if offer.current_price == 0 or deal_score >= 7.0:
                                    game_title_lower = offer.game.title.lower()

                                    # Verifica matches para cada alerta
                                    for alert in user_alerts:
                                        if alert.keyword in game_title_lower:
                                            logger.info(f"Match de alerta privado! Usuário: {alert.chat_id}, Keyword: {alert.keyword}, Jogo: {offer.game.title}")
                                            success_dm = await send_telegram_alert(
                                                game_title=offer.game.title,
                                                current_price=offer.current_price,
                                                historical_low=offer.historical_low,
                                                store_name=offer.store_name,
                                                deal_url=offer.deal_url,
                                                chat_id=alert.chat_id
                                            )
                                            if success_dm:
                                                dm_alerts_sent += 1

                        logger.info("Processamento de alertas privados finalizado.")
                    except Exception as alert_error:
                        logger.error(f"Erro ao processar alertas privados: {str(alert_error)}")

                except Exception as e:
                    logger.error(f"Erro ao processar notificações Telegram: {str(e)}")

            except Exception as e:
                await session.rollback()
                logger.error(f"Database error during synchronization: {str(e)}")
                raise
    except Exception as e:
        logger.error(f"Error during game synchronization: {str(e)}")
    finally:
        # Disparo do Relatório Operacional (NOC Report)
        execution_time = round(time.perf_counter() - start_time, 2)
        apis_str = ", ".join(sorted(list(external_apis))) if external_apis else "Nenhuma"
        stores_str = ", ".join(sorted(list(processed_stores))) if processed_stores else "Nenhuma"

        noc_report = (
            "🤖 NOC - Relatório de Sync\n"
            f"⏱️ Tempo de execução: {execution_time}s\n"
            f"🔗 APIs Utilizadas: {apis_str}\n"
            f"🏪 Lojas Processadas: {stores_str}\n"
            f"📥 Ofertas processadas: {total_processed_offers}\n"
            f"✨ Novas de Elite inseridas: {new_elite_offers}\n"
            f"🔔 Alertas disparados na DM: {dm_alerts_sent}\n"
            f"🟢 Status do Banco: {db_status}"
        )

        if settings.ADMIN_CHAT_ID:
            try:
                telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
                payload = {
                    "chat_id": settings.ADMIN_CHAT_ID,
                    "text": noc_report,
                    "parse_mode": "HTML"
                }
                headers = {"User-Agent": "GameDealTracker/1.0 (contato@teste.com)"}
                async with httpx.AsyncClient() as client:
                    await client.post(telegram_url, json=payload, headers=headers, timeout=10.0)
                logger.info("Relatório NOC enviado para o administrador.")
            except Exception as e:
                logger.error(f"Erro ao enviar relatório NOC: {str(e)}")
        else:
            logger.warning("ADMIN_CHAT_ID não configurado. Relatório NOC não enviado.")
