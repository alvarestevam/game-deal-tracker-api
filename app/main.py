from fastapi import FastAPI
from app.api.v1.health import router as health_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(health_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to GameDeal Tracker API"}
