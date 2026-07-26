from __future__ import annotations

import logging
import re

import httpx
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from telegram_bot.config import TelegramBotSettings, get_bot_settings
from telegram_bot.i18n import BTN_APPLY, button_regex, get_ui_lang, t
from telegram_bot.keyboards import (
    ADDIS_SUBCITIES,
    agent_menu_keyboard,
    apply_city_keyboard,
    apply_confirm_keyboard,
    apply_consent_keyboard,
    apply_frequency_keyboard,
    apply_languages_keyboard,
    apply_market_keyboard,
    apply_subcity_keyboard,
    guest_menu_keyboard,
    other_market_prompt_keyboard,
    other_market_voice_lang_keyboard,
    voice_label_confirm_keyboard,
)
from telegram_bot.reference import OTHER_MARKET_CODE
from telegram_bot.services.agents import AgentRegistry
from telegram_bot.services.addis_stt import AddisSTTError
from telegram_bot.services.score_api import AgentScoreAPI
from telegram_bot.services.voice_intake import transcribe_message_audio
from telegram_bot.states import ApplyState

logger = logging.getLogger(__name__)

SUBCITY_BY_CODE = {
    name.lower().replace(" ", "_").replace("-", "_"): name
    for name in ADDIS_SUBCITIES
}
LANG_LABELS = {
    "amharic": "Amharic",
    "afaan_oromo": "Afaan Oromo",
    "english": "English",
}
PHONE_RE = re.compile(r"^\+?[0-9][0-9\s\-]{7,20}$")


def _settings(context: ContextTypes.DEFAULT_TYPE) -> TelegramBotSettings:
    return context.application.bot_data.get("settings") or get_bot_settings()


def _agents(context: ContextTypes.DEFAULT_TYPE) -> AgentRegistry:
    return context.application.bot_data["agents"]


def _score_api(context: ContextTypes.DEFAULT_TYPE) -> AgentScoreAPI:
    return context.application.bot_data["score_api"]


async def _sync_agent_from_api(
    context: ContextTypes.DEFAULT_TYPE, user_id: int, display_name: str | None
) -> bool:
    agents = _agents(context)
    if agents.is_agent(user_id):
        return True
    settings = _settings(context)
    if settings.telegram_dry_run:
        return False
    try:
        data = await _score_api(context).get_score(str(user_id))
    except Exception:
        return False
    if not data.get("is_agent") or data.get("banned"):
        return False
    agents.mark_approved(user_id, display_name=display_name, via="api_sync")
    return True


async def apply_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_ui_lang(context)
    user = update.effective_user
    if user is not None:
        if not _agents(context).is_agent(user.id):
            await _sync_agent_from_api(context, user.id, user.full_name)
        if _agents(context).is_agent(user.id):
            text = t("apply_blocked", lang)
            menu = agent_menu_keyboard(lang)
            if update.callback_query is not None:
                await update.callback_query.answer()
                if update.callback_query.message is not None:
                    await update.callback_query.message.reply_text(text, reply_markup=menu)
            elif update.effective_message is not None:
                await update.effective_message.reply_text(text, reply_markup=menu)
            return ConversationHandler.END

    context.user_data["apply"] = {"languages_selected": []}
    text = (
        "Apply to become a Waga market agent.\n\n"
        "Step 1 - Full name\n"
        "Type your full name:"
    )
    if update.callback_query is not None:
        await update.callback_query.answer()
        if update.callback_query.message is not None:
            await update.callback_query.message.reply_text(text)
    elif update.effective_message is not None:
        await update.effective_message.reply_text(text)
    return ApplyState.FULL_NAME


async def apply_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.effective_message is not None
    name = (update.effective_message.text or "").strip()
    if len(name) < 2:
        await update.effective_message.reply_text("Please send your full name.")
        return ApplyState.FULL_NAME
    context.user_data.setdefault("apply", {})["full_name"] = name
    await update.effective_message.reply_text(
        "Step 2 - Phone number\n"
        "Type your phone (example: 0911234567):"
    )
    return ApplyState.PHONE


async def apply_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.effective_message is not None
    phone = (update.effective_message.text or "").strip()
    if not PHONE_RE.match(phone):
        await update.effective_message.reply_text(
            "That phone number looks invalid. Try again."
        )
        return ApplyState.PHONE
    context.user_data["apply"]["phone_number"] = phone
    await update.effective_message.reply_text(
        "Step 3 - City\nChoose one:",
        reply_markup=apply_city_keyboard(),
    )
    return ApplyState.CITY


async def apply_city_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None
    await query.answer()
    data = query.data or ""
    if data == "apply_cancel":
        return await apply_cancel(update, context)
    if data == "apply_city:other":
        await query.edit_message_text("Type your city name:")
        return ApplyState.CITY_OTHER
    context.user_data["apply"]["city"] = "Addis Ababa"
    await query.edit_message_text("City: Addis Ababa")
    assert query.message is not None
    await query.message.reply_text(
        "Step 4 - Subcity / area\nTap one, or Skip:",
        reply_markup=apply_subcity_keyboard(),
    )
    return ApplyState.SUBCITY


async def apply_city_other_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    assert update.effective_message is not None
    city = (update.effective_message.text or "").strip()
    if len(city) < 2:
        await update.effective_message.reply_text("Please type a city name.")
        return ApplyState.CITY_OTHER
    context.user_data["apply"]["city"] = city
    await update.effective_message.reply_text(
        "Step 4 - Subcity / area (optional)\nType area, or send skip:"
    )
    return ApplyState.SUBCITY_OTHER


async def apply_subcity_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    assert query is not None
    await query.answer()
    data = query.data or ""
    if data == "apply_cancel":
        return await apply_cancel(update, context)
    code = data.removeprefix("apply_subcity:")
    if code == "other":
        await query.edit_message_text("Type your subcity / area:")
        return ApplyState.SUBCITY_OTHER
    if code != "skip":
        context.user_data["apply"]["subcity"] = SUBCITY_BY_CODE.get(code, code)
    await query.edit_message_text(
        f"Area: {context.user_data['apply'].get('subcity', 'skipped')}"
    )
    assert query.message is not None
    await query.message.reply_text(
        "Step 5 - Preferred market\nWhich market can you cover?",
        reply_markup=apply_market_keyboard(),
    )
    return ApplyState.MARKET


async def apply_subcity_other_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    assert update.effective_message is not None
    text_value = (update.effective_message.text or "").strip()
    if text_value.lower() != "skip" and text_value:
        context.user_data["apply"]["subcity"] = text_value
    await update.effective_message.reply_text(
        "Step 5 - Preferred market\nWhich market can you cover?",
        reply_markup=apply_market_keyboard(),
    )
    return ApplyState.MARKET


async def apply_market(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None
    await query.answer()
    if query.data == "apply_cancel":
        return await apply_cancel(update, context)
    code = (query.data or "").removeprefix("apply_market:")
    context.user_data["apply"]["preferred_market_code"] = code
    if code == OTHER_MARKET_CODE:
        await query.edit_message_text("Other market")
        assert query.message is not None
        await query.message.reply_text(
            "How do you want to enter the market name?",
            reply_markup=other_market_prompt_keyboard(prefix="apply_voice"),
        )
        return ApplyState.MARKET_OTHER

    await query.edit_message_text(f"Preferred market: {code}")
    assert query.message is not None
    await query.message.reply_text(
        "Step 6 - Visit frequency\nHow often can you visit?",
        reply_markup=apply_frequency_keyboard(),
    )
    return ApplyState.FREQUENCY


async def apply_market_other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.effective_message is not None
    label = (update.effective_message.text or "").strip()
    if len(label) < 2:
        await update.effective_message.reply_text("Please type a market name.")
        return ApplyState.MARKET_OTHER
    context.user_data["apply"]["preferred_market_code"] = OTHER_MARKET_CODE
    context.user_data["apply"]["preferred_market_label"] = label
    await update.effective_message.reply_text(f"Preferred market: {label}")
    await update.effective_message.reply_text(
        "Step 6 - Visit frequency\nHow often can you visit?",
        reply_markup=apply_frequency_keyboard(),
    )
    return ApplyState.FREQUENCY



async def apply_market_other_mode(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    assert query is not None
    await query.answer()
    data = query.data or ""
    apply_data = context.user_data.setdefault("apply", {})
    if data == "apply_cancel":
        return await apply_cancel(update, context)
    if data == "apply_voice:mode:type":
        await query.edit_message_text(
            "Type the market name in Amharic, Afaan Oromo, or English."
        )
        return ApplyState.MARKET_OTHER
    if data == "apply_voice:mode:choose":
        await query.edit_message_text(
            "How do you want to enter the market name?",
            reply_markup=other_market_prompt_keyboard(prefix="apply_voice"),
        )
        return ApplyState.MARKET_OTHER
    if data == "apply_voice:mode:voice":
        await query.edit_message_text(
            "Choose language, then send a voice note with the market name.",
            reply_markup=other_market_voice_lang_keyboard(prefix="apply_voice"),
        )
        return ApplyState.MARKET_OTHER
    if data.startswith("apply_voice:lang:"):
        lang = data.rsplit(":", 1)[-1]
        apply_data["voice_lang"] = lang
        await query.edit_message_text(
            "Language set.\nSend a voice note with the market name now."
        )
    return ApplyState.MARKET_OTHER


async def apply_market_other_voice(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    assert update.effective_message is not None
    settings = _settings(context)
    if not settings.addis_stt_enabled():
        await update.effective_message.reply_text(
            "Voice is unavailable right now.\n"
            "Please type the market name instead."
        )
        return ApplyState.MARKET_OTHER

    apply_data = context.user_data.setdefault("apply", {})
    lang = str(apply_data.get("voice_lang") or settings.addis_ai_default_lang)
    await update.effective_message.reply_text("Listening to your voice note...")
    try:
        result = await transcribe_message_audio(
            bot=context.bot,
            message=update.effective_message,
            settings=settings,
            language_code=lang,
        )
    except AddisSTTError as error:
        await update.effective_message.reply_text(str(error))
        return ApplyState.MARKET_OTHER
    except Exception:
        logger.exception("Apply voice transcription failed")
        await update.effective_message.reply_text(
            "Could not read that voice note. Type the market name instead."
        )
        return ApplyState.MARKET_OTHER

    label = result.text.strip()
    if len(label) < 2:
        await update.effective_message.reply_text(
            "I could not hear a clear market name. Please send the voice note again."
        )
        return ApplyState.MARKET_OTHER

    apply_data["pending_market_label"] = label
    conf = ""
    if result.confidence is not None:
        conf = f"\nConfidence: {result.confidence:.0%}"
    await update.effective_message.reply_text(
        f"I heard:\n\n{label}{conf}\n\nUse this market name?",
        reply_markup=voice_label_confirm_keyboard(prefix="apply_voice"),
    )
    return ApplyState.MARKET_OTHER_CONFIRM


async def apply_market_other_voice_confirm(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    assert query is not None
    await query.answer()
    data = query.data or ""
    apply_data = context.user_data.setdefault("apply", {})

    if data == "apply_cancel":
        return await apply_cancel(update, context)

    if data.startswith("apply_voice:lang:"):
        lang = data.rsplit(":", 1)[-1]
        apply_data["voice_lang"] = lang
        await query.edit_message_text(
            "Language set.\nSend a voice note with the market name now."
        )
        return ApplyState.MARKET_OTHER

    if data == "apply_voice:retry":
        await query.edit_message_text("Send another voice note with the market name.")
        return ApplyState.MARKET_OTHER

    if data == "apply_voice:type":
        await query.edit_message_text("Type the market name now.")
        return ApplyState.MARKET_OTHER

    if data != "apply_voice:yes":
        return ApplyState.MARKET_OTHER_CONFIRM

    label = str(apply_data.get("pending_market_label") or "").strip()
    if len(label) < 2:
        await query.edit_message_text("Missing name. Send a voice note or type it.")
        return ApplyState.MARKET_OTHER

    apply_data["preferred_market_code"] = OTHER_MARKET_CODE
    apply_data["preferred_market_label"] = label
    apply_data.pop("pending_market_label", None)
    await query.edit_message_text(f"Preferred market: {label}")
    assert query.message is not None
    await query.message.reply_text(
        "Step 6 - Visit frequency\nHow often can you visit?",
        reply_markup=apply_frequency_keyboard(),
    )
    return ApplyState.FREQUENCY


async def apply_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None
    await query.answer()
    if query.data == "apply_cancel":
        return await apply_cancel(update, context)
    freq = (query.data or "").removeprefix("apply_freq:")
    context.user_data["apply"]["visit_frequency"] = freq
    await query.edit_message_text(f"Visit frequency: {freq}")
    assert query.message is not None
    await query.message.reply_text(
        "Step 7 - Languages (optional)\nTap all that apply, then Done:",
        reply_markup=apply_languages_keyboard(),
    )
    return ApplyState.LANGUAGES


async def apply_languages_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    assert query is not None
    await query.answer()
    data = query.data or ""
    apply_data = context.user_data.setdefault("apply", {})
    selected = set(apply_data.get("languages_selected") or [])

    if data == "apply_cancel":
        return await apply_cancel(update, context)

    if data.startswith("apply_lang_toggle:"):
        code = data.removeprefix("apply_lang_toggle:")
        if code in selected:
            selected.remove(code)
        else:
            selected.add(code)
        apply_data["languages_selected"] = sorted(selected)
        await query.edit_message_text(
            "Step 7 - Languages (optional)\nTap all that apply, then Done:",
            reply_markup=apply_languages_keyboard(selected),
        )
        return ApplyState.LANGUAGES

    if data == "apply_lang:skip":
        apply_data.pop("languages", None)
        apply_data["languages_selected"] = []
    elif data == "apply_lang:done":
        if selected:
            apply_data["languages"] = ", ".join(
                LANG_LABELS.get(code, code) for code in sorted(selected)
            )
        else:
            apply_data.pop("languages", None)

    await query.edit_message_text(
        f"Languages: {apply_data.get('languages', 'skipped')}"
    )
    assert query.message is not None
    await query.message.reply_text(
        "Step 8 - Consent\n"
        "I will visit the market and submit only real observed prices.",
        reply_markup=apply_consent_keyboard(),
    )
    return ApplyState.CONSENT


async def apply_consent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None
    await query.answer()
    if query.data == "apply_cancel":
        return await apply_cancel(update, context)
    context.user_data["apply"]["consent_honest_reporting"] = True
    data = context.user_data["apply"]
    summary = (
        "Confirm your application:\n"
        f"- Name: {data.get('full_name')}\n"
        f"- Phone: {data.get('phone_number')}\n"
        f"- City: {data.get('city')}\n"
        f"- Area: {data.get('subcity') or '-'}\n"
        f"- Market: {data.get('preferred_market_label') or data.get('preferred_market_code')}\n"
        f"- Visits: {data.get('visit_frequency')}\n"
        f"- Languages: {data.get('languages') or '-'}\n"
    )
    await query.edit_message_text(summary)
    assert query.message is not None
    await query.message.reply_text(
        "Submit this application?",
        reply_markup=apply_confirm_keyboard(),
    )
    return ApplyState.CONFIRM


async def apply_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None
    await query.answer()
    if query.data == "apply_cancel":
        return await apply_cancel(update, context)

    user = update.effective_user
    assert user is not None
    data = context.user_data.get("apply", {})
    settings = context.application.bot_data["settings"]
    payload = {
        "telegram_id": str(user.id),
        "telegram_username": user.username,
        "full_name": data.get("full_name"),
        "phone_number": data.get("phone_number"),
        "city": data.get("city", "Addis Ababa"),
        "subcity": data.get("subcity"),
        "preferred_market_code": data.get("preferred_market_code"),
        "visit_frequency": data.get("visit_frequency"),
        "languages": data.get("languages"),
        "notes": data.get("preferred_market_label"),
        "consent_honest_reporting": True,
    }

    if settings.telegram_dry_run:
        logger.warning(
            "Dry-run agent application (NOT saved to API/DB): %s", payload
        )
        await query.edit_message_text(
            "Application recorded in practice mode only.\n"
            "It was NOT saved to the server.\n"
            "Ask the team to set WAGA_TELEGRAM_DRY_RUN=false and restart the bot."
        )
        context.user_data.pop("apply", None)
        return ConversationHandler.END

    api_url = f"{settings.api_base_url.rstrip('/')}/agents/applications"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, json=payload)
            if response.status_code == 409:
                detail = "Conflict"
                try:
                    detail = str(response.json().get("detail", detail))
                except Exception:  # noqa: BLE001
                    pass
                await query.edit_message_text(detail)
                context.user_data.pop("apply", None)
                return ConversationHandler.END
            if response.status_code >= 400:
                logger.error(
                    "Application API error status=%s body=%s url=%s",
                    response.status_code,
                    response.text[:500],
                    api_url,
                )
                await query.edit_message_text(
                    "Could not save application on the server.\n"
                    f"Error {response.status_code}. Please try again."
                )
                context.user_data.pop("apply", None)
                return ConversationHandler.END
    except Exception:
        logger.exception("Failed to submit application to %s", api_url)
        await query.edit_message_text(
            "Could not reach the server to save your application.\n"
            "Please try again in a moment."
        )
        context.user_data.pop("apply", None)
        return ConversationHandler.END

    logger.info("Application saved for telegram_id=%s via %s", user.id, api_url)
    lang = get_ui_lang(context)
    await query.edit_message_text(
        "Application submitted. Thank you!\n"
        "Our team will review it."
    )
    context.user_data.pop("apply", None)
    if query.message is not None:
        await query.message.reply_text(
            t("menu", lang),
            reply_markup=guest_menu_keyboard(lang),
        )
    return ConversationHandler.END


async def apply_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("apply", None)
    query = update.callback_query
    message = update.effective_message
    lang = get_ui_lang(context)
    user = update.effective_user
    is_agent = bool(user and _agents(context).is_agent(user.id))
    menu = agent_menu_keyboard(lang) if is_agent else guest_menu_keyboard(lang)
    text = "Application cancelled."
    if query is not None:
        await query.answer()
        await query.edit_message_text(text)
        if query.message is not None:
            await query.message.reply_text(t("menu", lang), reply_markup=menu)
    elif message is not None:
        await message.reply_text(text, reply_markup=menu)
    return ConversationHandler.END


def register_apply_handlers(application: Application) -> None:
    conversation = ConversationHandler(
        entry_points=[
            CommandHandler("apply", apply_start),
            MessageHandler(filters.Regex(button_regex(BTN_APPLY)), apply_start),
            CallbackQueryHandler(apply_start, pattern=r"^ui:apply$"),
        ],
        states={
            ApplyState.FULL_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, apply_full_name)
            ],
            ApplyState.PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, apply_phone)
            ],
            ApplyState.CITY: [
                CallbackQueryHandler(
                    apply_city_callback, pattern=r"^(apply_city:.+|apply_cancel)$"
                )
            ],
            ApplyState.CITY_OTHER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, apply_city_other_message)
            ],
            ApplyState.SUBCITY: [
                CallbackQueryHandler(
                    apply_subcity_callback,
                    pattern=r"^(apply_subcity:.+|apply_cancel)$",
                )
            ],
            ApplyState.SUBCITY_OTHER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, apply_subcity_other_message
                )
            ],
            ApplyState.MARKET: [
                CallbackQueryHandler(
                    apply_market, pattern=r"^(apply_market:.+|apply_cancel)$"
                )
            ],
            ApplyState.MARKET_OTHER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, apply_market_other),
                MessageHandler(filters.VOICE | filters.AUDIO, apply_market_other_voice),
                CallbackQueryHandler(
                    apply_market_other_mode,
                    pattern=r"^(apply_voice:(mode|lang):.+|apply_cancel)$",
                ),
            ],
            ApplyState.MARKET_OTHER_CONFIRM: [
                CallbackQueryHandler(
                    apply_market_other_voice_confirm,
                    pattern=r"^(apply_voice:.+|apply_cancel)$",
                ),
            ],
            ApplyState.FREQUENCY: [
                CallbackQueryHandler(
                    apply_frequency, pattern=r"^(apply_freq:.+|apply_cancel)$"
                )
            ],
            ApplyState.LANGUAGES: [
                CallbackQueryHandler(
                    apply_languages_callback,
                    pattern=r"^(apply_lang_toggle:.+|apply_lang:.+|apply_cancel)$",
                )
            ],
            ApplyState.CONSENT: [
                CallbackQueryHandler(
                    apply_consent, pattern=r"^(apply_consent:.+|apply_cancel)$"
                )
            ],
            ApplyState.CONFIRM: [
                CallbackQueryHandler(
                    apply_confirm, pattern=r"^(apply_confirm:.+|apply_cancel)$"
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", apply_cancel),
            CallbackQueryHandler(apply_cancel, pattern=r"^apply_cancel$"),
        ],
        allow_reentry=True,
    )
    application.add_handler(conversation)
