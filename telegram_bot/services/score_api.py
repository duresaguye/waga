"""HTTP client for backend agent score APIs."""

from __future__ import annotations

from typing import Any

import httpx

from telegram_bot.config import TelegramBotSettings


class AgentScoreAPI:
    def __init__(self, settings: TelegramBotSettings) -> None:
        self._base = settings.api_base_url.rstrip("/")

    async def activate(
        self,
        telegram_id: str,
        invite_code: str,
        *,
        display_name: str | None,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{self._base}/agents/activate",
                json={
                    "telegram_id": telegram_id,
                    "invite_code": invite_code,
                    "display_name": display_name,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_score(self, telegram_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(f"{self._base}/agents/{telegram_id}/score")
            response.raise_for_status()
            return response.json()

    async def redeem(self, telegram_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{self._base}/agents/{telegram_id}/redeem")
            response.raise_for_status()
            return response.json()

    async def record_pending(self, telegram_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{self._base}/agents/{telegram_id}/pending")
            response.raise_for_status()
            return response.json()
