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
