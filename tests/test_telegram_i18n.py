from telegram_bot.i18n import (
    BTN_APPLY,
    BTN_SUBMIT,
    STRINGS,
    button_regex,
    normalize_ui_lang,
    t,
)
from telegram_bot.keyboards import agent_menu_keyboard, guest_actions_keyboard, guest_menu_keyboard


def test_all_langs_have_same_keys() -> None:
    assert set(STRINGS["en"]) == set(STRINGS["am"]) == set(STRINGS["om"])


def test_normalize_ui_lang() -> None:
    assert normalize_ui_lang("AM") == "am"
    assert normalize_ui_lang("om") == "om"
    assert normalize_ui_lang("oromo") == "om"
    assert normalize_ui_lang(None) == "en"


def test_guest_menu_has_no_invite() -> None:
    for lang in ("en", "am", "om"):
        labels = [btn.text for row in guest_menu_keyboard(lang).keyboard for btn in row]
        joined = " ".join(labels).lower()
        assert "invite" not in joined
        assert BTN_APPLY  # sanity
        assert t(BTN_APPLY, lang) in labels


def test_agent_menu_has_no_apply() -> None:
    for lang in ("en", "am", "om"):
        labels = [btn.text for row in agent_menu_keyboard(lang).keyboard for btn in row]
        assert t(BTN_APPLY, lang) not in labels
        assert t(BTN_SUBMIT, lang) in labels


def test_guest_actions_no_invite() -> None:
    texts = [
        btn.text
        for row in guest_actions_keyboard("en").inline_keyboard
        for btn in row
    ]
    assert any("Apply" in text for text in texts)
    assert not any("invite" in text.lower() for text in texts)


def test_button_regex_matches_all_langs() -> None:
    pattern = button_regex(BTN_SUBMIT)
    for lang in ("en", "am", "om"):
        assert pattern.match(t(BTN_SUBMIT, lang))
