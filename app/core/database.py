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
