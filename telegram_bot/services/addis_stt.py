"""Addis AI speech-to-text client (Amharic / Afaan Oromo)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import httpx

from telegram_bot.config import TelegramBotSettings

logger = logging.getLogger(__name__)


class AddisSTTError(Exception):
    """Raised when transcription fails."""


@dataclass(slots=True)
class TranscriptionResult:
    text: str
    confidence: float | None
    language_code: str


class AddisSTTClient:
    def __init__(self, settings: TelegramBotSettings) -> None:
        self._settings = settings

    @property
    def enabled(self) -> bool:
        return self._settings.addis_stt_enabled()

    async def transcribe_file(
        self,
        path: Path,
        *,
        language_code: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> TranscriptionResult:
        if not self.enabled:
            raise AddisSTTError(
                "Voice is unavailable right now. Please type the market name instead."
            )

        lang = (language_code or self._settings.addis_ai_default_lang).strip().lower()
        api_key = self._settings.addis_ai_api_key
        assert api_key is not None
        name = filename or path.name
        mime = content_type or _guess_content_type(name)

        data = path.read_bytes()
        request_data = json.dumps({"language_code": lang})

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self._settings.addis_ai_stt_url,
                headers={"x-api-key": api_key.get_secret_value()},
                files={"audio": (name, data, mime)},
                data={"request_data": request_data},
            )

        if response.status_code >= 400:
            logger.warning(
                "Addis STT failed status=%s body=%s",
                response.status_code,
                response.text[:500],
            )
            raise AddisSTTError(
                "Could not read that voice note. Please send it again, or type the name."
            )

        payload = response.json()
        text = _extract_text(payload)
        if not text:
            raise AddisSTTError(
                "I could not hear a clear market name. Please try again or type it."
            )

        confidence = payload.get("confidence")
        if confidence is not None:
            try:
                confidence = float(confidence)
            except (TypeError, ValueError):
                confidence = None

        return TranscriptionResult(
            text=text.strip(),
            confidence=confidence,
            language_code=lang,
        )


def _extract_text(payload: dict[str, object]) -> str:
    data = payload.get("data")
    if isinstance(data, dict):
        for key in ("transcription", "transcription_clean", "text"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    for key in ("text", "transcription", "response_text"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _guess_content_type(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".wav"):
        return "audio/wav"
    if lower.endswith(".mp3"):
        return "audio/mpeg"
    if lower.endswith(".m4a"):
        return "audio/mp4"
    if lower.endswith(".webm"):
        return "audio/webm"
    if lower.endswith(".ogg") or lower.endswith(".oga"):
        return "audio/ogg"
    return "application/octet-stream"
