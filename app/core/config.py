from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "GameDeal Tracker API"
    API_V1_STR: str = "/api/v1"

    API_KEY: str = "dev-key-123"
    SYNC_API_KEY: str = "admin-sync-key-123"
    ENV: str = "development"

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"

    GAMERPOWER_BASE_URL: str = "https://www.gamerpower.com/api"
    CHEAPSHARK_BASE_URL: str = "https://www.cheapshark.com/api/1.0"
    ITAD_BASE_URL: str = "https://api.isthereanydeal.com"
    ITAD_API_KEY: str = ""

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

settings = Settings()
