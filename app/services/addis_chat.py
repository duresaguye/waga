"""Addis AI text generation client for review assist."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


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
        lang = (target_language or self._settings.addis_ai_default_lang).strip().lower()

        payload = {
            "prompt": prompt,
            "target_language": lang,
            "persona": persona,
            "system": system,
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

        model = str(data.get("modelVersion") or "Addis-1-Alef")
        return ChatResult(text=text.strip(), model=model)


def _extract_text(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    for key in ("response_text", "text", "content"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content.strip()
    return ""
