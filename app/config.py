from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="WAGA_",
        extra="ignore",
    )

    app_name: str = "Waga Index API"
    environment: str = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://waga:waga@localhost:5432/waga"
    telegram_bot_token: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
