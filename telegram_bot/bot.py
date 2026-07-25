from __future__ import annotations

import logging

from telegram.ext import Application

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


def build_application() -> Application:
    settings = get_bot_settings()
    reputation = ReputationStore()
    agents = AgentRegistry(
        require_agent=settings.telegram_require_agent,
        allowed_ids=settings.parsed_agent_ids(),
        invite_codes=settings.parsed_invite_codes(),
    )
    application = (
        Application.builder()
        .token(settings.telegram_bot_token.get_secret_value())
        .build()
    )
    application.bot_data["settings"] = settings
    application.bot_data["reputation"] = reputation
    application.bot_data["agents"] = agents
    application.bot_data["score_api"] = AgentScoreAPI(settings)
    application.bot_data["submission_client"] = SubmissionClient(settings, reputation)
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
