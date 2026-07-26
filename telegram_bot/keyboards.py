from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from telegram_bot.i18n import (
    BTN_APPLY,
    BTN_HELP,
    BTN_LANGUAGE,
    BTN_REDEEM,
    BTN_SCORE,
    BTN_SUBMIT,
    DEFAULT_UI_LANG,
    btn,
    t,
)
from telegram_bot.reference import COMMODITIES, MARKETS


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("እስማማለሁ / I agree", callback_data="consent:yes"),
            ],
            [
                InlineKeyboardButton("አልስማማም / Decline", callback_data="consent:no"),
            ],
        ]
    )


def markets_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                f"{market.name_am} / {market.name_en}",
                callback_data=f"market:{market.code}",
            )
        ]
        for market in MARKETS
    ]
    rows.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(rows)


def commodities_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                f"{commodity.name_am} / {commodity.name_en}",
                callback_data=f"commodity:{commodity.code}",
            )
        ]
        for commodity in COMMODITIES
    ]
    rows.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(rows)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Confirm ✅", callback_data="confirm:yes"),
                InlineKeyboardButton("Edit price", callback_data="confirm:edit_price"),
            ],
            [InlineKeyboardButton("Cancel", callback_data="cancel")],
        ]
    )


def language_picker_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("English", callback_data="ui_lang:en")],
            [InlineKeyboardButton("አማርኛ", callback_data="ui_lang:am")],
            [InlineKeyboardButton("Afaan Oromoo", callback_data="ui_lang:om")],
        ]
    )


def guest_menu_keyboard(lang: str = DEFAULT_UI_LANG) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [btn(BTN_APPLY, lang)],
            [btn(BTN_HELP, lang), btn(BTN_LANGUAGE, lang)],
        ],
        resize_keyboard=True,
    )


def agent_menu_keyboard(lang: str = DEFAULT_UI_LANG) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [btn(BTN_SUBMIT, lang), btn(BTN_SCORE, lang)],
            [btn(BTN_REDEEM, lang), btn(BTN_HELP, lang)],
            [btn(BTN_LANGUAGE, lang)],
        ],
        resize_keyboard=True,
    )


def main_menu_keyboard(*, is_agent: bool = False, lang: str = DEFAULT_UI_LANG) -> ReplyKeyboardMarkup:
    return agent_menu_keyboard(lang) if is_agent else guest_menu_keyboard(lang)


def guest_actions_keyboard(lang: str = DEFAULT_UI_LANG) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(btn(BTN_APPLY, lang), callback_data="ui:apply")],
            [
                InlineKeyboardButton(
                    t("how_to_join_btn", lang), callback_data="ui:how_to_join"
                )
            ],
        ]
    )


def apply_market_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                f"{market.name_am} / {market.name_en}",
                callback_data=f"apply_market:{market.code}",
            )
        ]
        for market in MARKETS
    ]
    rows.append(
        [InlineKeyboardButton("Either / flexible", callback_data="apply_market:either")]
    )
    rows.append([InlineKeyboardButton("Cancel", callback_data="apply_cancel")])
    return InlineKeyboardMarkup(rows)


def apply_frequency_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Daily", callback_data="apply_freq:daily")],
            [
                InlineKeyboardButton(
                    "Few times a week", callback_data="apply_freq:few_times_week"
                )
            ],
            [InlineKeyboardButton("Weekends", callback_data="apply_freq:weekends")],
            [InlineKeyboardButton("Cancel", callback_data="apply_cancel")],
        ]
    )


def apply_consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "I agree — real market prices only",
                    callback_data="apply_consent:yes",
                )
            ],
            [InlineKeyboardButton("Cancel", callback_data="apply_cancel")],
        ]
    )


def apply_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Submit application ✅", callback_data="apply_confirm:yes"),
                InlineKeyboardButton("Cancel", callback_data="apply_cancel"),
            ]
        ]
    )


def score_actions_keyboard(*, can_redeem: bool, lang: str = DEFAULT_UI_LANG) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if can_redeem:
        rows.append(
            [InlineKeyboardButton(f"🎁 {btn(BTN_REDEEM, lang)}", callback_data="ui:redeem")]
        )
    rows.append(
        [InlineKeyboardButton(f"📤 {btn(BTN_SUBMIT, lang)}", callback_data="ui:submit")]
    )
    return InlineKeyboardMarkup(rows)


def voice_label_confirm_keyboard(*, prefix: str = "voice_mkt") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Use this name — continue", callback_data=f"{prefix}:yes")],
            [InlineKeyboardButton("Record again", callback_data=f"{prefix}:retry")],
            [InlineKeyboardButton("Type instead", callback_data=f"{prefix}:type")],
        ]
    )


def other_market_prompt_keyboard(*, prefix: str = "voice_mkt") -> InlineKeyboardMarkup:
    cancel = "cancel" if prefix == "voice_mkt" else "apply_cancel"
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Type the name", callback_data=f"{prefix}:mode:type")],
            [InlineKeyboardButton("Record voice", callback_data=f"{prefix}:mode:voice")],
            [InlineKeyboardButton("Cancel", callback_data=cancel)],
        ]
    )


def other_market_voice_lang_keyboard(*, prefix: str = "voice_mkt") -> InlineKeyboardMarkup:
    cancel = "cancel" if prefix == "voice_mkt" else "apply_cancel"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Amharic", callback_data=f"{prefix}:lang:am"),
                InlineKeyboardButton("Afaan Oromo", callback_data=f"{prefix}:lang:om"),
            ],
            [InlineKeyboardButton("Back", callback_data=f"{prefix}:mode:choose")],
            [InlineKeyboardButton("Cancel", callback_data=cancel)],
        ]
    )


ADDIS_SUBCITIES: tuple[str, ...] = (
    "Addis Ketema",
    "Arada",
    "Bole",
    "Gulele",
    "Kirkos",
    "Kolfe Keranio",
    "Lideta",
    "Nifas Silk-Lafto",
    "Yeka",
    "Akaky Kaliti",
    "Lemi Kura",
)


def apply_city_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Addis Ababa", callback_data="apply_city:addis_ababa")],
            [InlineKeyboardButton("Other city (type)", callback_data="apply_city:other")],
            [InlineKeyboardButton("Cancel", callback_data="apply_cancel")],
        ]
    )


def apply_subcity_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for name in ADDIS_SUBCITIES:
        code = name.lower().replace(" ", "_").replace("-", "_")
        row.append(InlineKeyboardButton(name, callback_data=f"apply_subcity:{code}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [
            InlineKeyboardButton("Skip", callback_data="apply_subcity:skip"),
            InlineKeyboardButton("Other (type)", callback_data="apply_subcity:other"),
        ]
    )
    rows.append([InlineKeyboardButton("Cancel", callback_data="apply_cancel")])
    return InlineKeyboardMarkup(rows)


def apply_languages_keyboard(selected: set[str] | None = None) -> InlineKeyboardMarkup:
    chosen = selected or set()
    options = (
        ("amharic", "Amharic"),
        ("afaan_oromo", "Afaan Oromo"),
        ("english", "English"),
    )
    rows: list[list[InlineKeyboardButton]] = []
    for code, label in options:
        mark = "[x] " if code in chosen else ""
        rows.append(
            [
                InlineKeyboardButton(
                    f"{mark}{label}", callback_data=f"apply_lang_toggle:{code}"
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton("Done", callback_data="apply_lang:done"),
            InlineKeyboardButton("Skip", callback_data="apply_lang:skip"),
        ]
    )
    rows.append([InlineKeyboardButton("Cancel", callback_data="apply_cancel")])
    return InlineKeyboardMarkup(rows)
