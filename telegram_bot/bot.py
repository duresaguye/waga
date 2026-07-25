from __future__ import annotations

import logging

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


def main() -> None:
    settings = get_bot_settings()
    application = build_application()
    logger.info(
        "Starting Waga Telegram bot (dry_run=%s, require_agent=%s, agents=%s, invites=%s)",
        settings.telegram_dry_run,
        settings.telegram_require_agent,
        len(settings.parsed_agent_ids()),
        len(settings.parsed_invite_codes()),
    )
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
