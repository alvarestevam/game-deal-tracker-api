from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.api.v1.health import router as health_router
from app.api.v1.games import router as games_router
from app.api.v1.telegram import router as telegram_router
from app.core.config import settings
from app.core.database import (
    engine, Base, ensure_image_url_column, ensure_slug_column,
    ensure_metacritic_column, ensure_original_price_column,
    ensure_notified_telegram_column, backfill_slugs
)
from app.models.game import Game
from app.services.sync_service import sync_games
from app.core.limiter import limiter

async def verify_api_key(x_api_key: str | None = Header(None)):
    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Acesso não autorizado")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Migração automática de schema para novos campos
    await ensure_image_url_column(engine)
    await ensure_slug_column(engine)
    await ensure_metacritic_column(engine)
    await ensure_original_price_column(engine)
    await ensure_notified_telegram_column(engine)
    await backfill_slugs(engine)

    # Configure and start APScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(sync_games, 'interval', hours=2)
    # Execute once on startup to populate database
    scheduler.add_job(sync_games)
    scheduler.start()
    yield
    # Shutdown: Stop APScheduler
    scheduler.shutdown()

# Ocultar documentação em produção
docs_url = "/docs" if settings.ENV != "production" else None
redoc_url = "/redoc" if settings.ENV != "production" else None

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url=docs_url,
    redoc_url=redoc_url
)

# Integrar slowapi
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://api.alvarestevam.online",
        "https://alvarestevam.online"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(
    games_router,
    prefix=settings.API_V1_STR,
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    telegram_router,
    prefix=settings.API_V1_STR,
    dependencies=[Depends(verify_api_key)]
)

@app.get("/")
@limiter.limit("60/minute")
async def root(request: Request):
    return {"message": "Welcome to GameDeal Tracker API"}
