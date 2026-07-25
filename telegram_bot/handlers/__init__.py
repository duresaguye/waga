from telegram.ext import Application

from telegram_bot.handlers.apply import register_apply_handlers
from telegram_bot.handlers.submit import register_submit_handlers


def register_handlers(application: Application) -> None:
    register_apply_handlers(application)
    register_submit_handlers(application)
