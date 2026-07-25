from __future__ import annotations

import asyncio
import logging
import os
import secrets

from telegram import Update
from telegram.error import NetworkError, TimedOut
from telegram.ext import Application, ContextTypes
from telegram.request import HTTPXRequest

from telegram_bot.config import get_bot_settings
from telegram_bot.handlers import register_handlers
from telegram_bot.services.agents import AgentRegistry
from telegram_bot.services.reputation import ReputationStore
from telegram_bot.services.score_api import AgentScoreAPI
from telegram_bot.services.submission_client import SubmissionClient

logging.basicConfig(
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    error = context.error
    if isinstance(error, (TimedOut, NetworkError)):
        logger.warning("Telegram network issue: %s", error)
        return
    logger.exception("Unhandled bot error", exc_info=error)


def build_application() -> Application:
    settings = get_bot_settings()
    reputation = ReputationStore()
    agents = AgentRegistry(
        require_agent=settings.telegram_require_agent,
        allowed_ids=settings.parsed_agent_ids(),
        invite_codes=settings.parsed_invite_codes(),
    )
    # Ethiopia / unstable networks often need longer Telegram API timeouts.
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0,
    )
    application = (
        Application.builder()
        .token(settings.telegram_bot_token.get_secret_value())
        .request(request)
        .get_updates_request(request)
        .build()
    )
    application.bot_data["settings"] = settings
    application.bot_data["reputation"] = reputation
    application.bot_data["agents"] = agents
    application.bot_data["score_api"] = AgentScoreAPI(settings)
    application.bot_data["submission_client"] = SubmissionClient(settings, reputation)
    application.add_error_handler(_on_error)
    register_handlers(application)
    return application


async def _run_webhook(application: Application) -> None:
    from aiohttp import web

    settings = get_bot_settings()
    port = int(os.environ.get("PORT", "8000"))
    path = settings.telegram_webhook_path.strip().strip("/") or "telegram"
    webhook_url = settings.webhook_full_url()
    secret = settings.telegram_webhook_secret.strip() or secrets.token_urlsafe(24)

    await application.initialize()
    await application.start()

    async def health(_: web.Request) -> web.Response:
        return web.Response(text="ok")

    async def telegram_webhook(request: web.Request) -> web.Response:
        header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if secret and header != secret:
            return web.Response(status=403, text="forbidden")
        data = await request.json()
        update = Update.de_json(data, application.bot)
        if update is not None:
            await application.process_update(update)
        return web.Response(text="ok")

    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    app.router.add_post(f"/{path}", telegram_webhook)

    await application.bot.set_webhook(
        url=webhook_url,
        secret_token=secret,
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )
    logger.info("Webhook set to %s (listening 0.0.0.0:%s)", webhook_url, port)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    finally:
        await application.bot.delete_webhook()
        await runner.cleanup()
        await application.stop()
        await application.shutdown()


def main() -> None:
    settings = get_bot_settings()
    application = build_application()
    logger.info(
        "Starting Waga Telegram bot (mode=%s, dry_run=%s, api=%s, require_agent=%s, agents=%s, invites=%s)",
        settings.telegram_mode,
        settings.telegram_dry_run,
        settings.api_base_url,
        settings.telegram_require_agent,
        len(settings.parsed_agent_ids()),
        len(settings.parsed_invite_codes()),
    )
    if settings.telegram_dry_run:
        logger.warning(
            "DRY RUN is ON — applications and submissions will NOT be saved to the API/DB"
        )

    if settings.telegram_mode == "webhook":
        asyncio.run(_run_webhook(application))
        return

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
