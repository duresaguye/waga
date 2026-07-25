from functools import lru_cache
from typing import Self

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_JWT_SECRET = "development-only-change-this-jwt-secret"


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
    jwt_secret_key: SecretStr = SecretStr(DEVELOPMENT_JWT_SECRET)
    jwt_issuer: str = "waga-index"
    jwt_audience: str = "waga-api"
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    max_failed_login_attempts: int = 5
    login_lock_minutes: int = 15
    password_min_length: int = 8
    password_max_length: int = 128

    # Addis AI — voice STT (bot) + review assist LLM (API)
    addis_ai_api_key: SecretStr | None = None
    addis_ai_chat_url: str = "https://api.addisassistant.com/api/v1/chat_generate"
    addis_ai_default_lang: str = "am"
    review_ai_enabled: bool = True

    @field_validator("addis_ai_api_key", mode="before")
    @classmethod
    def empty_addis_key_as_none(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def use_asyncpg_driver(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        return value

    @model_validator(mode="after")
    def validate_auth_settings(self) -> Self:
        secret = self.jwt_secret_key.get_secret_value()
        is_production = self.environment.strip().lower() == "production"
        if is_production and (secret == DEVELOPMENT_JWT_SECRET or len(secret.encode("utf-8")) < 32):
            raise ValueError("WAGA_JWT_SECRET_KEY must be set to at least 32 bytes in production")
        if self.access_token_minutes <= 0:
            raise ValueError("WAGA_ACCESS_TOKEN_MINUTES must be positive")
        if self.refresh_token_days <= 0:
            raise ValueError("WAGA_REFRESH_TOKEN_DAYS must be positive")
        if self.max_failed_login_attempts <= 0:
            raise ValueError("WAGA_MAX_FAILED_LOGIN_ATTEMPTS must be positive")
        if self.login_lock_minutes <= 0:
            raise ValueError("WAGA_LOGIN_LOCK_MINUTES must be positive")
        if self.password_min_length < 8:
            raise ValueError("WAGA_PASSWORD_MIN_LENGTH must be at least 8")
        if self.password_max_length < self.password_min_length:
            raise ValueError(
                "WAGA_PASSWORD_MAX_LENGTH must be greater than or equal to WAGA_PASSWORD_MIN_LENGTH"
            )
        if not self.jwt_issuer.strip():
            raise ValueError("WAGA_JWT_ISSUER must not be blank")
        if not self.jwt_audience.strip():
            raise ValueError("WAGA_JWT_AUDIENCE must not be blank")
        if not self.addis_ai_chat_url.strip():
            raise ValueError("WAGA_ADDIS_AI_CHAT_URL must not be blank")
        return self

    def addis_chat_enabled(self) -> bool:
        return (
            self.review_ai_enabled
            and self.addis_ai_api_key is not None
            and bool(self.addis_ai_api_key.get_secret_value().strip())
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
