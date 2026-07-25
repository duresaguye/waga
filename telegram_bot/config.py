from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramBotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="WAGA_",
        extra="ignore",
    )

    telegram_bot_token: SecretStr
    api_base_url: str = "http://127.0.0.1:8000/api/v1"
    telegram_dry_run: bool = True
    # polling = local/dev; webhook = Render free web service
    telegram_mode: str = "polling"
    # Public base URL of the bot service, e.g. https://waga-bot.onrender.com
    # Also accepts RENDER_EXTERNAL_URL if this is unset.
    telegram_webhook_url: str = ""
    telegram_webhook_path: str = "telegram"
    telegram_webhook_secret: str = ""
    # Only approved agents may submit for score/rewards (anti-fraud).
    telegram_require_agent: bool = True
    # Comma-separated Telegram numeric user IDs pre-approved by the team.
    telegram_agent_ids: str = ""
    # Comma-separated invite codes handed out after meeting someone.
    telegram_agent_invite_codes: str = "WAGA-ADDIS-01"
    # Support phone shown on Help.
    telegram_help_phone: str = "+251994445412"
    # Addis AI speech-to-text (optional — voice notes for Other market).
    addis_ai_api_key: SecretStr | None = None
    addis_ai_stt_url: str = "https://api.addisassistant.com/api/v2/stt"
    addis_ai_default_lang: str = "am"  # am | om

    @field_validator("telegram_agent_ids", "telegram_agent_invite_codes", mode="before")
    @classmethod
    def blank_to_empty(cls, value: object) -> object:
        if value is None:
            return ""
        return value

    @field_validator("addis_ai_api_key", mode="before")
    @classmethod
    def empty_secret_to_none(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("addis_ai_default_lang")
    @classmethod
    def validate_lang(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"am", "om"}:
            raise ValueError("addis_ai_default_lang must be 'am' or 'om'")
        return normalized

    @field_validator("telegram_mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"polling", "webhook"}:
            raise ValueError("telegram_mode must be 'polling' or 'webhook'")
        return normalized

    @field_validator("telegram_webhook_url", "telegram_webhook_path", "telegram_webhook_secret", mode="before")
    @classmethod
    def blank_webhook_strings(cls, value: object) -> object:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return value

    def webhook_base_url(self) -> str:
        import os

        base = self.telegram_webhook_url.strip().rstrip("/")
        if not base:
            base = (os.environ.get("RENDER_EXTERNAL_URL") or "").strip().rstrip("/")
        return base

    def webhook_full_url(self) -> str:
        base = self.webhook_base_url()
        path = self.telegram_webhook_path.strip().strip("/")
        if not base:
            raise ValueError(
                "Webhook mode needs WAGA_TELEGRAM_WEBHOOK_URL or RENDER_EXTERNAL_URL"
            )
        return f"{base}/{path}" if path else base

    def addis_stt_enabled(self) -> bool:
        return (
            self.addis_ai_api_key is not None
            and bool(self.addis_ai_api_key.get_secret_value().strip())
        )

    def parsed_agent_ids(self) -> set[int]:
        ids: set[int] = set()
        for part in self.telegram_agent_ids.split(","):
            part = part.strip()
            if not part:
                continue
            ids.add(int(part))
        return ids

    def parsed_invite_codes(self) -> set[str]:
        return {
            part.strip()
            for part in self.telegram_agent_invite_codes.split(",")
            if part.strip()
        }


@lru_cache
def get_bot_settings() -> TelegramBotSettings:
    return TelegramBotSettings()
