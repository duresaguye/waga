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

    # Subscription billing (Chapa)
    trial_days: int = 14
    pro_exports_per_day: int = 1
    history_days_monthly: int = 30
    history_days_annual: int = 90
    pro_monthly_etb: int = 1600
    pro_annual_etb: int = 16000
    chapa_test_secret_key: SecretStr | None = None
    chapa_test_public_key: SecretStr | None = None
    chapa_webhook_secret: SecretStr | None = None
    chapa_base_url: str = "https://api.chapa.co/v1"
    chapa_callback_url: str = "http://127.0.0.1:8000/api/v1/webhooks/chapa/callback"
    chapa_return_url: str = "http://localhost:5173/account/billing"

    # Index computation
    index_window_hours: int = 72
    publication_threshold: int = 3
    method_version: str = "waga-index-v1"
    heat_method_version: str = "waga-heat-v1"
    affordability_method_version: str = "waga-affordability-v1"
    spike_method_version: str = "waga-spike-v1"
    cost_index_method_version: str = "waga-cost-index-v1"
    city_code: str = "addis_ababa"
    currency_code: str = "ETB"
    public_history_days: int = 30

    # Demo admin seed (development / waga-seed-admin)
    seed_admin_email: str = "admin@waga.com"
    seed_admin_password: SecretStr = SecretStr("AdminPassword12!")
    seed_admin_display_name: str = "Super Admin"

    # ECWG MEB reference figures (static; label as_of honestly in responses)
    ecwg_meb_source: str = "ECWG MEB National Reference Guide, June 2025"
    ecwg_national_meb_full_etb: float = 17700.0
    ecwg_national_meb_food_etb: float = 16135.0
    ecwg_as_of: str = "2025-12-01"
    ecwg_review_cadence_months: int = 3
    ecwg_revision_trigger: str = (
        "Six consecutive months of price movement in one direction"
    )

    @field_validator(
        "addis_ai_api_key",
        "chapa_test_secret_key",
        "chapa_test_public_key",
        "chapa_webhook_secret",
        mode="before",
    )
    @classmethod
    def empty_secret_as_none(cls, value: object) -> object:
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

    def chapa_enabled(self) -> bool:
        return (
            self.chapa_test_secret_key is not None
            and bool(self.chapa_test_secret_key.get_secret_value().strip())
        )

    def chapa_secret_key(self) -> str | None:
        if self.chapa_test_secret_key is None:
            return None
        value = self.chapa_test_secret_key.get_secret_value().strip()
        return value or None

    def chapa_webhook_secret_value(self) -> str | None:
        if self.chapa_webhook_secret is None:
            return None
        value = self.chapa_webhook_secret.get_secret_value().strip()
        return value or None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
