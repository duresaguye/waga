"""UI language for Telegram menus: English, Amharic, Afaan Oromo."""

from __future__ import annotations

import re
from typing import Any

from telegram.ext import ContextTypes

UI_LANGS = ("en", "am", "om")
DEFAULT_UI_LANG = "en"
UI_LANG_KEY = "ui_lang"

BTN_APPLY = "btn_apply"
BTN_HELP = "btn_help"
BTN_SUBMIT = "btn_submit"
BTN_SCORE = "btn_score"
BTN_REDEEM = "btn_redeem"
BTN_LANGUAGE = "btn_language"

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        BTN_APPLY: "Apply to be agent",
        BTN_HELP: "Help",
        BTN_SUBMIT: "Submit price",
        BTN_SCORE: "My score",
        BTN_REDEEM: "Redeem score",
        BTN_LANGUAGE: "Language",
        "lang_name": "English",
        "choose_language": "Choose your language / ቋንቋ ይምረጡ / Afaan filadhu:",
        "language_set": "Language set to English.",
        "menu": "Menu:",
        "use_buttons": "Use the buttons below.",
        "welcome_guest": "Welcome to Waga.",
        "welcome_agent": (
            "Welcome, Waga market agent.\n"
            "Score: {score} ({status})\n\n"
            "Visit your market, then submit real prices.\n"
            "Accepted reports raise your score.\n"
            "Score can be redeemed for rewards.\n\n"
            "Tap below to continue."
        ),
        "denial": (
            "To join as a market agent:\n"
            "Tap Apply to be agent and wait for approval."
        ),
        "how_to_join_btn": "How to join",
        "already_agent": (
            "You are already a Waga market agent.\n"
            "Use Submit price from the menu."
        ),
        "help_guest": (
            "Waga market agent bot\n\n"
            "Join:\n"
            "\u2022 Apply to be agent \u2014 name, phone, city, market, schedule\n\n"
            "Need help? Call {phone}"
        ),
        "help_agent": (
            "Waga market agent bot\n\n"
            "Commands:\n"
            "\u2022 Submit price \u2014 report a market price\n"
            "\u2022 My score \u2014 view score\n"
            "\u2022 Redeem score \u2014 redeem for birr rewards\n"
            "\u2022 /cancel \u2014 cancel current flow\n\n"
            "Need help? Call {phone}"
        ),
        "apply_blocked": "You are already an agent. Use the menu below.",
        "tap_submit": "Tap Submit price in the menu, or send /submit.",
    },
    "am": {
        BTN_APPLY: "ወኪል ለመሆን ያመልክቱ",
        BTN_HELP: "እገዛ",
        BTN_SUBMIT: "ዋጋ ሪፖርት",
        BTN_SCORE: "ውጤቴ",
        BTN_REDEEM: "ውጤት ቀይር",
        BTN_LANGUAGE: "ቋንቋ",
        "lang_name": "አማርኛ",
        "choose_language": "ቋንቋ ይምረጡ / Choose language / Afaan filadhu:",
        "language_set": "ቋንቋ ወደ አማርኛ ተቀይሯል።",
        "menu": "ሜኑ:",
        "use_buttons": "ከታች ያሉትን አዝራሮች ይጠቀሙ።",
        "welcome_guest": "እንካን ወደ ዋጋ በደህና መጡ።",
        "welcome_agent": (
            "እንካን ደህና መጡ፣ የዋጋ ገበያ ወኪል።\n"
            "ውጤት: {score} ({status})\n\n"
            "ገበያዎን ይጎብኙ፣ ከዚያ እውነተኛ ዋጋዎችን ይላኩ።\n"
            "የተቀበሉ ሪፖርቶች ውጤትዎን ያሳድጋሉ።\n"
            "ውጤትን ለሽልማት መቀየር ይችላሉ።\n\n"
            "ለመቀጠል ከታች ይጋኑ።"
        ),
        "denial": (
            "የገበያ ወኪል ለመሆን:\n"
            "«ወኪል ለመሆን ያመልክቱ»ን ይጋኑ እና ማጽደቅ ይጠብቁ።"
        ),
        "how_to_join_btn": "እንዴት መቀላቀል",
        "already_agent": (
            "እርሶ አስቀድመው የዋጋ ገበያ ወኪል ነዎት።\n"
            "ከሜኑ «ዋጋ ሪፖርት»ን ይጠቀሙ።"
        ),
        "help_guest": (
            "የዋጋ ገበያ ወኪል ቦት\n\n"
            "መቀላቀል:\n"
            "\u2022 ወኪል ለመሆን ያመልክቱ \u2014 ስም፣ ስልክ፣ ከተማ፣ ገበያ፣ መርሁግብር\n\n"
            "እገዛ? ይደውሉ {phone}"
        ),
        "help_agent": (
            "የዋጋ ገበያ ወኪል ቦት\n\n"
            "ትዕዛዞች:\n"
            "\u2022 ዋጋ ሪፖርት \u2014 የገበያ ዋጋ ሪፖርት\n"
            "\u2022 ውጤቴ \u2014 ውጤት ማየት\n"
            "\u2022 ውጤት ቀይር \u2014 ለብር ሽልማት\n"
            "\u2022 /cancel \u2014 ፍሰት ሰርዝ\n\n"
            "እገዛ? ይደውሉ {phone}"
        ),
        "apply_blocked": "እርሶ አስቀድመው ወኪል ነዎት። ከታች ያለውን ሜኑ ይጠቀሙ።",
        "tap_submit": "ከሜኑ «ዋጋ ሪፖርት»ን ይጋኑ፣ ወይም /submit ይላኩ።",
    },
    "om": {
        BTN_APPLY: "Agent ta'uuf galmaa'i",
        BTN_HELP: "Gargaarsa",
        BTN_SUBMIT: "Gatiin galchi",
        BTN_SCORE: "Qabxii koo",
        BTN_REDEEM: "Qabxii jijjiiri",
        BTN_LANGUAGE: "Afaan",
        "lang_name": "Afaan Oromoo",
        "choose_language": "Afaan filadhu / Choose language / ቋንቋ ይምረጡ:",
        "language_set": "Afaan gara Afaan Oromoootti jijjiirameera.",
        "menu": "Menu:",
        "use_buttons": "Buttonota armaan gadii fayyadami.",
        "welcome_guest": "Baga nagaan gara Waga dhuftan.",
        "welcome_agent": (
            "Baga nagaan dhufte, agent gabaa Waga.\n"
            "Qabxii: {score} ({status})\n\n"
            "Gabaa kee daawwadhu, sana booda gatii dhugaa ergi.\n"
            "Gabaasni fudhatame qabxii kee ol kaasuu danda'a.\n"
            "Qabxiin badhaasaaf jijjiiramuu danda'a.\n\n"
            "Itti fufuuf armaan gadi tuqi."
        ),
        "denial": (
            "Agent gabaa ta'uuf:\n"
            "\u00abAgent ta'uuf galmaa'i\u00bb tuqiitii eeyyama eegi."
        ),
        "how_to_join_btn": "Akkamitti makama",
        "already_agent": (
            "Ati duraanuu agent gabaa Waga dha.\n"
            "Menurii keessaa \u00abGatiin galchi\u00bb fayyadami."
        ),
        "help_guest": (
            "Bot agent gabaa Waga\n\n"
            "Makamuuf:\n"
            "\u2022 Agent ta'uuf galmaa'i \u2014 maqaa, bilbila, magaalaa, gabaa, sagantaa\n\n"
            "Gargaarsa? Bilbilii {phone}"
        ),
        "help_agent": (
            "Bot agent gabaa Waga\n\n"
            "Ajaja:\n"
            "\u2022 Gatiin galchi \u2014 gatii gabaa gabaasi\n"
            "\u2022 Qabxii koo \u2014 qabxii ilaali\n"
            "\u2022 Qabxii jijjiiri \u2014 badhaasa qarshiif\n"
            "\u2022 /cancel \u2014 haquu\n\n"
            "Gargaarsa? Bilbilii {phone}"
        ),
        "apply_blocked": "Ati duraanuu agent dha. Menu armaan gadii fayyadami.",
        "tap_submit": "Menurii keessaa \u00abGatiin galchi\u00bb tuqi, ykn /submit ergi.",
    },
}


def normalize_ui_lang(value: str | None) -> str:
    if not value:
        return DEFAULT_UI_LANG
    code = value.strip().lower()
    if code in UI_LANGS:
        return code
    if code.startswith("am"):
        return "am"
    if code.startswith("om") or code.startswith("or"):
        return "om"
    return DEFAULT_UI_LANG


def get_ui_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return normalize_ui_lang(context.user_data.get(UI_LANG_KEY))


def set_ui_lang(context: ContextTypes.DEFAULT_TYPE, lang: str) -> str:
    code = normalize_ui_lang(lang)
    context.user_data[UI_LANG_KEY] = code
    return code


def has_ui_lang(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return UI_LANG_KEY in context.user_data


def t(key: str, lang: str | None = None, **kwargs: Any) -> str:
    code = normalize_ui_lang(lang)
    template = STRINGS.get(code, STRINGS[DEFAULT_UI_LANG]).get(key) or STRINGS[
        DEFAULT_UI_LANG
    ].get(key, key)
    if kwargs:
        return template.format(**kwargs)
    return template


def btn(key: str, lang: str | None = None) -> str:
    return t(key, lang)


def button_regex(*keys: str) -> re.Pattern[str]:
    labels: list[str] = []
    for key in keys:
        for lang in UI_LANGS:
            labels.append(re.escape(btn(key, lang)))
    return re.compile(rf"^({'|'.join(labels)})$")
