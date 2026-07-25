from __future__ import annotations

import logging
import re

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

from telegram_bot.keyboards import (
    other_market_prompt_keyboard,
    other_market_voice_lang_keyboard,
    voice_label_confirm_keyboard,
    agent_menu_keyboard,
    commodities_keyboard,
    confirm_keyboard,
    consent_keyboard,
    guest_actions_keyboard,
    guest_menu_keyboard,
    markets_keyboard,
    score_actions_keyboard,
)
from telegram_bot.reference import (
    CONSENT_VERSION,
    OTHER_MARKET_CODE,
    commodity_by_code,
    market_by_code,
)
from telegram_bot.config import TelegramBotSettings
from telegram_bot.services.agents import AgentRegistry
from telegram_bot.services.reputation import ContributorReputation, ReputationStore
from telegram_bot.services.score_api import AgentScoreAPI
from telegram_bot.services.addis_stt import AddisSTTError
from telegram_bot.services.submission_client import DraftSubmission, SubmissionClient
from telegram_bot.services.voice_intake import transcribe_message_audio
from telegram_bot.states import SubmitState

logger = logging.getLogger(__name__)

PRICE_RE = re.compile(r"^\d+(?:[.,]\d{1,2})?$")


def _client(context: ContextTypes.DEFAULT_TYPE) -> SubmissionClient:
    return context.application.bot_data["submission_client"]


def _reputation_store(context: ContextTypes.DEFAULT_TYPE) -> ReputationStore:
    return context.application.bot_data["reputation"]


def _agents(context: ContextTypes.DEFAULT_TYPE) -> AgentRegistry:
    return context.application.bot_data["agents"]


def _score_api(context: ContextTypes.DEFAULT_TYPE) -> AgentScoreAPI:
    return context.application.bot_data["score_api"]


def _settings(context: ContextTypes.DEFAULT_TYPE) -> TelegramBotSettings:
    return context.application.bot_data["settings"]


def _menu_for(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    return (
        agent_menu_keyboard()
        if _agents(context).is_agent(user_id)
        else guest_menu_keyboard()
    )


async def _reject_if_not_agent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if user is None:
        return True
    agents = _agents(context)
    if agents.is_agent(user.id):
        return False
    message = update.effective_message
    if message is not None:
        await message.reply_text(
            agents.denial_message(),
            reply_markup=guest_actions_keyboard(),
        )
        await message.reply_text(
            "Use the buttons below.",
            reply_markup=guest_menu_keyboard(),
        )
    return True


async def _reject_if_banned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if user is None:
        return True
    profile = _client(context).reputation_for(user.id)
    if not profile.banned:
        return False
    text = (
        "🚫 Your agent account is suspended.\n"
        f"Reason: {profile.ban_reason or 'policy violation'}\n"
        f"Score: {profile.score}\n"
        "Contact the Waga team if you think this is a mistake."
    )
    message = update.effective_message
    if message is not None:
        await message.reply_text(text, reply_markup=_menu_for(context, user.id))
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.effective_message is not None
    user = update.effective_user
    if user is None:
        return ConversationHandler.END

    agents = _agents(context)
    if not agents.is_agent(user.id):
        await update.effective_message.reply_text(
            "Welcome to Waga.\n\n" + agents.denial_message(),
            reply_markup=guest_actions_keyboard(),
        )
        await update.effective_message.reply_text(
            "Menu:",
            reply_markup=guest_menu_keyboard(),
        )
        return ConversationHandler.END

    if await _reject_if_banned(update, context):
        return ConversationHandler.END

    context.user_data.clear()
    profile = _client(context).reputation_for(user.id)
    await update.effective_message.reply_text(
        "Welcome, Waga market agent.\n"
        f"Score: {profile.score} ({profile.status_label()})\n\n"
        "Visit your market, then submit real prices.\n"
        "Accepted reports raise your score.\n"
        "Score can be redeemed for rewards.\n\n"
        "Tap below to continue.",
        reply_markup=consent_keyboard(),
    )
    return SubmitState.CONSENT


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_message is not None
    user = update.effective_user
    is_agent = bool(user and _agents(context).is_agent(user.id))
    help_phone = _settings(context).telegram_help_phone
    await update.effective_message.reply_text(
        "Waga market agent bot\n\n"
        "Join:\n"
        "1) /apply — name, phone, city, market, visit schedule\n"
        "2) Or /agent CODE if you already have an invite\n\n"
        "Commands:\n"
        "• /submit — report a market price\n"
        "• /score — view score\n"
        "• /redeem — redeem score for birr rewards\n"
        "• /cancel — cancel current flow\n\n"
        f"Need help? Call {help_phone}",
        reply_markup=agent_menu_keyboard() if is_agent else guest_menu_keyboard(),
    )


async def agent_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_message is not None
    user = update.effective_user
    if user is None:
        return
    agents = _agents(context)
    if not context.args:
        if agents.is_agent(user.id):
            await update.effective_message.reply_text(
                "You are already a market agent.\nUse Submit price or /submit.",
                reply_markup=agent_menu_keyboard(),
            )
            return
        await update.effective_message.reply_text(
            agents.join_prompt(),
            reply_markup=guest_menu_keyboard(),
        )
        return

    code = " ".join(context.args)
    settings = _settings(context)
    if not settings.telegram_dry_run:
        try:
            data = await _score_api(context).activate(
                str(user.id),
                code,
                display_name=user.full_name,
            )
        except Exception:
            logger.exception("API agent activate failed")
            await update.effective_message.reply_text(
                "Could not activate via API. Check that the backend is running.",
                reply_markup=guest_menu_keyboard(),
            )
            return
        # Mirror into local registry so submit gating works this session.
        agents.activate_with_invite(user.id, code, display_name=user.full_name)
        score = data.get("score", {})
        await update.effective_message.reply_text(
            f"{data.get('message', 'Activated.')}\n"
            f"Score: {score.get('score', 0)} ({score.get('status', 'Active')})",
            reply_markup=agent_menu_keyboard(),
        )
        return

    ok, message = agents.activate_with_invite(
        user.id,
        code,
        display_name=user.full_name,
    )
    await update.effective_message.reply_text(
        message,
        reply_markup=agent_menu_keyboard() if ok else guest_menu_keyboard(),
    )
    if ok:
        logger.info("Activated agent telegram_user_id=%s via invite", user.id)


async def score_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_message is not None
    user = update.effective_user
    if user is None:
        return
    if not _agents(context).is_agent(user.id):
        await update.effective_message.reply_text(
            _agents(context).denial_message(),
            reply_markup=guest_actions_keyboard(),
        )
        return

    settings = _settings(context)
    if not settings.telegram_dry_run:
        try:
            data = await _score_api(context).get_score(str(user.id))
        except Exception:
            logger.exception("API score fetch failed")
            await update.effective_message.reply_text(
                "Could not load score from API.",
                reply_markup=agent_menu_keyboard(),
            )
            return
        pending = int(data.get("pending_count", 0) or 0)
        accepted = int(data.get("accepted_count", 0) or 0)
        text = (
            "Agent score\n"
            f"• Score: {data.get('score', 0)}\n"
            f"• Status: {data.get('status', 'Active')}\n"
            f"• Reports sent: {pending + accepted}\n"
            f"• Accepted: {accepted}\n"
            f"• Redeemed so far: {data.get('redeemed_total', 0)}\n"
            f"• Redeem from {data.get('redeem_threshold', 50)} points"
        )
        await update.effective_message.reply_text(
            text,
            reply_markup=score_actions_keyboard(can_redeem=bool(data.get("can_redeem"))),
        )
        await update.effective_message.reply_text("Menu:", reply_markup=agent_menu_keyboard())
        return

    store = _reputation_store(context)
    profile = store.get(user.id)
    await update.effective_message.reply_text(
        store.format_card(profile),
        reply_markup=score_actions_keyboard(can_redeem=profile.can_redeem()),
    )
    await update.effective_message.reply_text(
        "Menu:",
        reply_markup=agent_menu_keyboard(),
    )


async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_message is not None
    user = update.effective_user
    if user is None:
        return
    if not _agents(context).is_agent(user.id):
        await update.effective_message.reply_text(
            _agents(context).denial_message(),
            reply_markup=guest_menu_keyboard(),
        )
        return

    settings = _settings(context)
    if not settings.telegram_dry_run:
        try:
            data = await _score_api(context).redeem(str(user.id))
        except Exception as error:
            logger.exception("API redeem failed")
            detail = getattr(getattr(error, "response", None), "text", None)
            await update.effective_message.reply_text(
                detail or "Could not redeem via API.",
                reply_markup=agent_menu_keyboard(),
            )
            return
        score = data.get("score", {})
        await update.effective_message.reply_text(
            f"{data.get('message', 'Redeem recorded.')}\n"
            f"Score now: {score.get('score', 0)}",
            reply_markup=agent_menu_keyboard(),
        )
        return

    ok, message, profile = _reputation_store(context).redeem(user.id)
    await update.effective_message.reply_text(
        message,
        reply_markup=score_actions_keyboard(can_redeem=profile.can_redeem()),
    )
    await update.effective_message.reply_text(
        "Menu:",
        reply_markup=agent_menu_keyboard(),
    )
    if ok:
        logger.info(
            "Redeem request telegram_user_id=%s amount_was_redeemed_total=%s",
            user.id,
            profile.redeemed_total,
        )


async def enter_code_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_message is not None
    await update.effective_message.reply_text(
        _agents(context).join_prompt(),
        reply_markup=guest_menu_keyboard(),
    )


async def ui_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    query = update.callback_query
    assert query is not None
    await query.answer()
    data = query.data or ""

    if data == "ui:how_to_join":
        await query.edit_message_text(_agents(context).denial_message())
        return None

    if data == "ui:enter_code":
        await query.edit_message_text(_agents(context).join_prompt())
        return None

    if data == "ui:redeem":
        user = update.effective_user
        if user is None:
            return None
        ok, message, profile = _reputation_store(context).redeem(user.id)
        await query.edit_message_text(message)
        if ok:
            logger.info("Redeem via button telegram_user_id=%s", user.id)
        return None

    if data == "ui:submit":
        # Kick off submit flow from score card.
        if query.message is not None:
            # Create a synthetic path by asking user to tap Submit price
            await query.edit_message_text("Tap Submit price in the menu, or send /submit.")
        return None

    return None


async def consent_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None
    await query.answer()

    if query.data == "consent:no":
        await query.edit_message_text("Okay. No report started. Send /submit anytime.")
        return ConversationHandler.END

    user = update.effective_user
    if user is not None and _client(context).is_banned(user.id):
        await query.edit_message_text("Your agent account is suspended.")
        return ConversationHandler.END

    context.user_data["consent_version"] = CONSENT_VERSION
    await query.edit_message_text(
        "Consent saved. Accepted reports earn redeemable score.\nChoose the market:"
    )
    assert query.message is not None
    await query.message.reply_text("Select market:", reply_markup=markets_keyboard())
    return SubmitState.MARKET


async def market_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None
    await query.answer()

    if query.data == "cancel":
        return await cancel(update, context)

    code = (query.data or "").removeprefix("market:")
    market = market_by_code(code)
    if market is None:
        await query.edit_message_text("Unknown market. Send /submit to try again.")
        return ConversationHandler.END

    context.user_data["market_code"] = market.code
    context.user_data.pop("market_label", None)

    if market.code == OTHER_MARKET_CODE:
        await query.edit_message_text("Other market")
        assert query.message is not None
        await query.message.reply_text(
            "How do you want to enter the market name?",
            reply_markup=other_market_prompt_keyboard(prefix="voice_mkt"),
        )
        return SubmitState.MARKET_OTHER

    await query.edit_message_text(f"Market: {market.name_am} / {market.name_en}")
    assert query.message is not None
    await query.message.reply_text("Select commodity:", reply_markup=commodities_keyboard())
    return SubmitState.COMMODITY


async def market_other_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.effective_message is not None
    label = (update.effective_message.text or "").strip()
    if len(label) < 2:
        await update.effective_message.reply_text("Please type a market name.")
        return SubmitState.MARKET_OTHER
    context.user_data["market_code"] = OTHER_MARKET_CODE
    context.user_data["market_label"] = label
    await update.effective_message.reply_text(f"Market: {label}")
    await update.effective_message.reply_text(
        "Select commodity:", reply_markup=commodities_keyboard()
    )
    return SubmitState.COMMODITY



async def market_other_lang_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    assert query is not None
    await query.answer()
    data = query.data or ""
    if data == "cancel":
        return await cancel(update, context)
    if data == "voice_mkt:mode:type":
        await query.edit_message_text(
            "Type the market name in Amharic, Afaan Oromo, or English."
        )
        return SubmitState.MARKET_OTHER
    if data == "voice_mkt:mode:choose":
        await query.edit_message_text(
            "How do you want to enter the market name?",
            reply_markup=other_market_prompt_keyboard(prefix="voice_mkt"),
        )
        return SubmitState.MARKET_OTHER
    if data == "voice_mkt:mode:voice":
        await query.edit_message_text(
            "Choose language, then send a voice note with the market name.",
            reply_markup=other_market_voice_lang_keyboard(prefix="voice_mkt"),
        )
        return SubmitState.MARKET_OTHER
    if data.startswith("voice_mkt:lang:"):
        lang = data.rsplit(":", 1)[-1]
        context.user_data["voice_lang"] = lang
        await query.edit_message_text(
            "Language set.\nSend a voice note with the market name now."
        )
    return SubmitState.MARKET_OTHER


async def market_other_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.effective_message is not None
    settings = _settings(context)
    if not settings.addis_stt_enabled():
        await update.effective_message.reply_text(
            "Voice is unavailable right now.\n"
            "Please type the market name instead."
        )
        return SubmitState.MARKET_OTHER

    lang = str(context.user_data.get("voice_lang") or settings.addis_ai_default_lang)
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
        return SubmitState.MARKET_OTHER
    except Exception:
        logger.exception("Voice transcription failed")
        await update.effective_message.reply_text(
            "Could not read that voice note. Send the voice note again."
        )
        return SubmitState.MARKET_OTHER

    label = result.text.strip()
    if len(label) < 2:
        await update.effective_message.reply_text(
            "I could not hear a clear market name. Please send the voice note again."
        )
        return SubmitState.MARKET_OTHER

    context.user_data["pending_market_label"] = label
    conf = ""
    if result.confidence is not None:
        conf = f"\nConfidence: {result.confidence:.0%}"
    await update.effective_message.reply_text(
        f"I heard:\n\n{label}{conf}\n\nTap Use this name to continue to submit.",
        reply_markup=voice_label_confirm_keyboard(prefix="voice_mkt"),
    )
    return SubmitState.MARKET_OTHER_CONFIRM


async def market_other_voice_confirm(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    assert query is not None
    await query.answer()
    data = query.data or ""

    if data == "cancel":
        return await cancel(update, context)

    if data.startswith("voice_mkt:lang:"):
        lang = data.rsplit(":", 1)[-1]
        context.user_data["voice_lang"] = lang
        await query.edit_message_text(
            "Send a voice note with the market name now."
        )
        return SubmitState.MARKET_OTHER

    if data == "voice_mkt:retry":
        await query.edit_message_text("Send another voice note with the market name.")
        return SubmitState.MARKET_OTHER

    if data == "voice_mkt:type":
        await query.edit_message_text("Type the market name now.")
        return SubmitState.MARKET_OTHER

    if data != "voice_mkt:yes":
        return SubmitState.MARKET_OTHER_CONFIRM

    label = str(context.user_data.get("pending_market_label") or "").strip()
    if len(label) < 2:
        await query.edit_message_text("Missing name. Send a voice note or type it.")
        return SubmitState.MARKET_OTHER

    context.user_data["market_code"] = OTHER_MARKET_CODE
    context.user_data["market_label"] = label
    context.user_data.pop("pending_market_label", None)
    await query.edit_message_text(f"Market saved: {label}")
    assert query.message is not None
    await query.message.reply_text(
        "Next: choose the food, enter the price, then Confirm to submit.",
        reply_markup=commodities_keyboard(),
    )
    return SubmitState.COMMODITY


async def commodity_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None
    await query.answer()

    if query.data == "cancel":
        return await cancel(update, context)

    code = (query.data or "").removeprefix("commodity:")
    commodity = commodity_by_code(code)
    if commodity is None:
        await query.edit_message_text("Unknown commodity. Send /submit to try again.")
        return ConversationHandler.END

    context.user_data["commodity_code"] = commodity.code
    context.user_data["unit"] = commodity.unit
    await query.edit_message_text(
        f"Commodity: {commodity.name_am} / {commodity.name_en} ({commodity.unit})"
    )
    assert query.message is not None
    await query.message.reply_text(
        f"Type the price in ETB per {commodity.unit}.\n"
        "Example: 95 or 95.50\n"
        "Submit only prices observed at the market."
    )
    return SubmitState.PRICE


async def price_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.effective_message is not None
    text = (update.effective_message.text or "").strip().replace(",", ".")
    if not PRICE_RE.match(text):
        await update.effective_message.reply_text(
            "Please send numbers only. Example: 95 or 95.50"
        )
        return SubmitState.PRICE

    price = float(text)
    if price <= 0 or price > 1_000_000:
        await update.effective_message.reply_text("Price looks invalid. Try again.")
        return SubmitState.PRICE

    context.user_data["price"] = price
    return await _ask_confirm(update, context)


async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query is not None
    await query.answer()

    if query.data == "cancel":
        return await cancel(update, context)

    if query.data == "confirm:edit_price":
        await query.edit_message_text("Okay, type the price again.")
        return SubmitState.PRICE

    user = update.effective_user
    assert user is not None
    draft = DraftSubmission(
        telegram_user_id=user.id,
        telegram_username=user.username,
        market_code=str(context.user_data["market_code"]),
        commodity_code=str(context.user_data["commodity_code"]),
        price=float(context.user_data["price"]),
        unit=str(context.user_data["unit"]),
        consent_version=str(context.user_data["consent_version"]),
        market_label=context.user_data.get("market_label"),
    )

    client = _client(context)
    try:
        result = await client.submit(draft)
    except Exception:
        logger.exception("Failed to submit draft")
        await query.edit_message_text(
            "Could not save right now. Please try again with /submit."
        )
        context.user_data.clear()
        return ConversationHandler.END

    if result.get("status") == "banned":
        profile = result.get("reputation")
        reason = "policy violation"
        if isinstance(profile, ContributorReputation) and profile.ban_reason:
            reason = profile.ban_reason
        await query.edit_message_text(
            "🚫 Submission blocked — account suspended.\n"
            f"Reason: {reason}\n"
            "Use /score for details."
        )
        context.user_data.clear()
        return ConversationHandler.END

    if result.get("status") == "error":
        await query.edit_message_text(
            "Could not submit this report.\n"
            f"{result.get('message', 'Please try again.')}\n"
            "Use /submit to start over."
        )
        context.user_data.clear()
        return ConversationHandler.END

    profile = result.get("reputation")
    score_bit = ""
    can_redeem = False
    if isinstance(profile, ContributorReputation):
        can_redeem = profile.can_redeem()
        score_bit = f"\nScore: {profile.score}"

    await query.edit_message_text(
        f"Price report submitted. Thank you!{score_bit}"
    )
    if query.message is not None:
        await query.message.reply_text(
            "Menu:",
            reply_markup=agent_menu_keyboard(),
        )
        if can_redeem:
            await query.message.reply_text(
                "You can redeem now.",
                reply_markup=score_actions_keyboard(can_redeem=True),
            )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    message = update.effective_message
    query = update.callback_query
    user = update.effective_user
    menu = guest_menu_keyboard()
    if user is not None:
        menu = _menu_for(context, user.id)
    text = "Cancelled. Use the menu when you are ready."
    if query is not None:
        await query.answer()
        await query.edit_message_text(text)
    elif message is not None:
        await message.reply_text(text, reply_markup=menu)
    return ConversationHandler.END


async def menu_submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await start(update, context)


async def _ask_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    market_code = str(context.user_data["market_code"])
    market = market_by_code(market_code)
    commodity = commodity_by_code(str(context.user_data["commodity_code"]))
    price = context.user_data["price"]
    assert commodity is not None

    if market_code == OTHER_MARKET_CODE:
        market_name = str(context.user_data.get("market_label") or "Other")
    else:
        assert market is not None
        market_name = f"{market.name_am} / {market.name_en}"

    text = (
        "Confirm this market report:\n"
        f"• Market: {market_name}\n"
        f"• Commodity: {commodity.name_am} / {commodity.name_en}\n"
        f"• Price: {price:g} ETB / {commodity.unit}\n\n"
        "Confirm only if you observed this price at the market."
    )
    message = update.effective_message
    assert message is not None
    await message.reply_text(text, reply_markup=confirm_keyboard())
    return SubmitState.CONFIRM


def register_submit_handlers(application: Application) -> None:
    conversation = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("submit", start),
            MessageHandler(filters.Regex(r"^Submit price$"), menu_submit),
        ],
        states={
            SubmitState.CONSENT: [
                CallbackQueryHandler(consent_callback, pattern=r"^consent:"),
            ],
            SubmitState.MARKET: [
                CallbackQueryHandler(market_callback, pattern=r"^(market:.+|cancel)$"),
            ],
            SubmitState.MARKET_OTHER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, market_other_message),
                MessageHandler(filters.VOICE | filters.AUDIO, market_other_voice),
                CallbackQueryHandler(
                    market_other_lang_callback, pattern=r"^(voice_mkt:(mode|lang):.+|cancel)$"
                ),
            ],
            SubmitState.MARKET_OTHER_CONFIRM: [
                CallbackQueryHandler(
                    market_other_voice_confirm,
                    pattern=r"^(voice_mkt:.+|cancel)$",
                ),
            ],
            SubmitState.COMMODITY: [
                CallbackQueryHandler(commodity_callback, pattern=r"^(commodity:.+|cancel)$"),
            ],
            SubmitState.PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, price_message),
            ],
            SubmitState.CONFIRM: [
                CallbackQueryHandler(confirm_callback, pattern=r"^(confirm:.+|cancel)$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel, pattern=r"^cancel$"),
        ],
        allow_reentry=True,
    )
    application.add_handler(conversation)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("score", score_command))
    application.add_handler(CommandHandler("redeem", redeem_command))
    application.add_handler(CommandHandler("agent", agent_command))
    application.add_handler(CallbackQueryHandler(ui_callback, pattern=r"^ui:"))
    application.add_handler(MessageHandler(filters.Regex(r"^Help$"), help_command))
    application.add_handler(MessageHandler(filters.Regex(r"^My score$"), score_command))
    application.add_handler(
        MessageHandler(filters.Regex(r"^Redeem score$"), redeem_command)
    )
    application.add_handler(
        MessageHandler(filters.Regex(r"^Enter invite code$"), enter_code_prompt)
    )
