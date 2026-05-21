from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.api.v1.health import router as health_router
from app.api.v1.games import router as games_router
from app.core.config import settings
from app.core.database import engine, Base
from app.models.game import Game
from app.services.sync_service import sync_games

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Configure and start APScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(sync_games, 'interval', hours=6)
    # Execute once on startup to populate database
    scheduler.add_job(sync_games)
    scheduler.start()
    yield
    # Shutdown: Stop APScheduler
    scheduler.shutdown()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(games_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to GameDeal Tracker API"}
