"""Best-effort Telegram DMs from the API (e.g. application approved)."""

from __future__ import annotations

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


async def notify_telegram_user(telegram_id: str, text: str) -> bool:
    """Send a message via Bot API. Returns False if skipped/failed."""
    settings = get_settings()
    token = settings.telegram_bot_token
    if token is None:
        logger.info("Skip Telegram notify — WAGA_TELEGRAM_BOT_TOKEN not set on API")
        return False
    secret = token.get_secret_value().strip()
    if not secret:
        return False
    chat_id = telegram_id.strip()
    if not chat_id:
        return False
    url = f"https://api.telegram.org/bot{secret}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                json={"chat_id": chat_id, "text": text},
            )
            if response.status_code >= 400:
                logger.warning(
                    "Telegram notify failed status=%s body=%s",
                    response.status_code,
                    response.text[:200],
                )
                return False
            return True
    except Exception:
        logger.exception("Telegram notify error for telegram_id=%s", chat_id)
        return False


async def notify_agent_approved(*, telegram_id: str, full_name: str) -> bool:
    name = full_name.strip() or "there"
    text = (
        f"Hi {name} — your Waga market agent application was approved.\n\n"
        "You can submit prices now:\n"
        "• Open this bot\n"
        "• Tap Submit price (or /submit)\n"
        "• Earn score when reports are accepted\n\n"
        "No invite code needed."
    )
    return await notify_telegram_user(telegram_id, text)
