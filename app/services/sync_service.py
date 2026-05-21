import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.game import Game
from app.services.gamerpower_client import GamerPowerClient
from app.services.cheapshark_client import CheapSharkClient

logger = logging.getLogger(__name__)

async def upsert_game(session: AsyncSession, title: str, price: float, is_free: bool):
    try:
        result = await session.execute(select(Game).where(Game.title == title))
        game = result.scalars().first()

        if game:
            game.current_price = price
            game.is_free = is_free
            if price < game.historical_low:
                game.historical_low = price
        else:
            new_game = Game(
                title=title,
                current_price=price,
                historical_low=price,
                is_free=is_free
            )
            session.add(new_game)
    except Exception as e:
        logger.error(f"Error upserting game {title}: {str(e)}")

async def sync_games():
    logger.info("Starting game synchronization...")
    gp_client = GamerPowerClient()
    cs_client = CheapSharkClient()

    try:
        giveaways = await gp_client.get_pc_giveaways()
        deals = await cs_client.get_deals()

        async with AsyncSessionLocal() as session:
            # Process giveaways
            for item in giveaways:
                await upsert_game(session, item.title, item.sale_price, True)

            # Process deals
            for item in deals:
                await upsert_game(session, item.title, item.sale_price, item.sale_price == 0)

            await session.commit()
        logger.info("Game synchronization completed successfully.")
    except Exception as e:
        logger.error(f"Error during game synchronization: {str(e)}")
