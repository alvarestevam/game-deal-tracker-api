import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def ensure_image_url_column(engine):
    """Garante que a coluna image_url existe na tabela games."""
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE games ADD COLUMN IF NOT EXISTS image_url VARCHAR(500);"))

async def ensure_slug_column(engine):
    """Garante que a coluna slug existe na tabela games."""
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE games ADD COLUMN IF NOT EXISTS slug VARCHAR;"))
        # Criar índice único manualmente se não existir
        try:
            await conn.execute(text("CREATE UNIQUE INDEX ix_games_slug ON games (slug);"))
        except Exception:
            # Índice já existe ou erro ao criar
            pass

async def ensure_metacritic_column(engine):
    """Garante que a coluna metacritic_score existe na tabela games."""
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE games ADD COLUMN IF NOT EXISTS metacritic_score INTEGER;"))

async def ensure_original_price_column(engine):
    """Garante que a coluna original_price existe na tabela game_offers."""
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE game_offers ADD COLUMN IF NOT EXISTS original_price FLOAT;"))

async def ensure_notified_telegram_column(engine):
    """Garante que a coluna notified_telegram existe na tabela game_offers."""
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE game_offers ADD COLUMN IF NOT EXISTS notified_telegram BOOLEAN DEFAULT FALSE NOT NULL;"))

async def ensure_user_alerts_table(engine):
    """Garante que a tabela user_alerts existe."""
    async with engine.begin() as conn:
        # Chamada 1: Apenas a criação da tabela
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_alerts (
                id UUID PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                keyword VARCHAR NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc')
            );
        """))

        # Chamada 2: Apenas o índice do chat_id
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_alerts_chat_id ON user_alerts (chat_id);"))

        # Chamada 3: Apenas o índice da keyword
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_alerts_keyword ON user_alerts (keyword);"))

async def backfill_slugs(engine):
    """Gera slugs para registros existentes que ainda não possuem."""
    from app.utils.text_utils import normalize_title
    from app.models.game import Game

    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(text("SELECT id, title FROM games WHERE slug IS NULL"))
            rows = result.fetchall()

            for row_id, title in rows:
                slug = normalize_title(title)
                await session.execute(
                    text("UPDATE games SET slug = :slug WHERE id = :id"),
                    {"slug": slug, "id": row_id}
                )
