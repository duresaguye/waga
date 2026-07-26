"""Addis AI text generation client for review assist."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

# chat_generate currently accepts only this target_language code.
# Desired output language is enforced via the system prompt instead.
_ADDIS_API_TARGET_LANGUAGE = "am"


class AddisChatError(Exception):
    """Raised when Addis chat generation fails."""


@dataclass(frozen=True)
class ChatResult:
    text: str
    model: str


class AddisChatClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def enabled(self) -> bool:
        return self._settings.addis_chat_enabled()

    async def generate(
        self,
        *,
        prompt: str,
        system: str,
        target_language: str | None = None,
        temperature: float = 0.2,
        max_output_tokens: int = 400,
        persona: str = "Waga market price review assistant",
    ) -> ChatResult:
        if not self.enabled:
            raise AddisChatError("Addis AI chat is not configured")

        api_key = self._settings.addis_ai_api_key
        assert api_key is not None
        desired = (target_language or self._settings.addis_ai_default_lang).strip().lower()
        # Addis chat_generate only accepts target_language="am". Output language is
        # controlled in prompt+system — English must be stated in the prompt body.
        if desired.startswith("am"):
            system_with_lang = (
                "You must write in Amharic only. "
                f"{system.strip()}"
            )
            prompt_with_lang = (
                "OUTPUT LANGUAGE: Amharic.\n"
                f"{prompt.strip()}"
            )
        else:
            system_with_lang = (
                "You must write in English only. "
                f"{system.strip()}"
            )
            prompt_with_lang = (
                "OUTPUT LANGUAGE: English. Write in English (Latin script).\n"
                f"{prompt.strip()}"
            )

        payload = {
            "prompt": prompt_with_lang,
            "target_language": _ADDIS_API_TARGET_LANGUAGE,
            "persona": persona,
            "system": system_with_lang,
            "generation_config": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                self._settings.addis_ai_chat_url,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key.get_secret_value(),
                },
                json=payload,
            )

        if response.status_code >= 400:
            logger.warning(
                "Addis chat failed status=%s body=%s",
                response.status_code,
                response.text[:500],
            )
            raise AddisChatError(
                f"Addis chat failed with status {response.status_code}"
            )

        data = response.json()
        text = _extract_text(data)
        if not text:
            raise AddisChatError("Addis chat returned empty text")

        model = _extract_model(data)
        return ChatResult(text=text.strip(), model=model)


def _extract_text(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    candidates: list[dict] = [payload]
    nested = payload.get("data")
    if isinstance(nested, dict):
        candidates.insert(0, nested)
    for obj in candidates:
        for key in ("response_text", "text", "content"):
            value = obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        choices = obj.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str) and content.strip():
                        return content.strip()
    return ""


def _extract_model(payload: object) -> str:
    if not isinstance(payload, dict):
        return "Addis-1-Alef"
    nested = payload.get("data")
    if isinstance(nested, dict):
        model = nested.get("modelVersion") or nested.get("model")
        if isinstance(model, str) and model.strip():
            return model.strip()
    model = payload.get("modelVersion") or payload.get("model")
    if isinstance(model, str) and model.strip():
        return model.strip()
    return "Addis-1-Alef"
