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
