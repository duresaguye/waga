"""Normalize free-text market/commodity labels (Amharic / Oromo / English)."""

from __future__ import annotations

import re
import unicodedata

from app.models.enums import Script
from telegram_bot.reference import COMMODITIES as BOT_COMMODITIES

_SPACE_RE = re.compile(r"\s+")
_LATIN_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)


def detect_script(text: str) -> Script:
    sample = text.strip()
    if not sample:
        return Script.ENGLISH
    ethiopic = sum(1 for ch in sample if "\u1200" <= ch <= "\u137F")
    if ethiopic >= max(1, len(sample) // 3):
        return Script.ETHIOPIC
    if any(ch.isalpha() and ord(ch) < 128 for ch in sample):
        return Script.ENGLISH
    return Script.LATIN


def normalize_label(text: str, *, script: Script | None = None) -> str:
    value = unicodedata.normalize("NFC", text).strip()
    value = _SPACE_RE.sub(" ", value)
    resolved = script or detect_script(value)
    if resolved in {Script.ENGLISH, Script.LATIN}:
        value = value.casefold()
        value = _LATIN_PUNCT_RE.sub("", value)
        value = _SPACE_RE.sub(" ", value).strip()
    return value


def looks_like_close_latin(a: str, b: str, *, max_distance: int = 1) -> bool:
    if a == b:
        return True
    if abs(len(a) - len(b)) > max_distance:
        return False
    if max(len(a), len(b)) > 24:
        return False
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            ins = curr[j - 1] + 1
            delete = prev[j] + 1
            sub = prev[j - 1] + (0 if ca == cb else 1)
            curr.append(min(ins, delete, sub))
        prev = curr
    return prev[-1] <= max_distance


_LATIN_SYNONYMS: tuple[tuple[str, str, str, Script], ...] = (
    ("teff_mixed", "teff", "teff", Script.ENGLISH),
    ("teff_mixed", "tef", "tef", Script.ENGLISH),
    ("teff_mixed", "taff", "taff", Script.ENGLISH),
    ("teff_mixed", "xafii", "xafii", Script.LATIN),
    ("teff_mixed", "xaafii", "xaafii", Script.LATIN),
    ("wheat", "wheat", "wheat", Script.ENGLISH),
    ("wheat", "wheet", "wheet", Script.ENGLISH),
    ("wheat", "qamadii", "qamadii", Script.LATIN),
    ("maize", "maize", "maize", Script.ENGLISH),
    ("maize", "corn", "corn", Script.ENGLISH),
    ("maize", "boqqolloo", "boqqolloo", Script.LATIN),
    ("onion", "onion", "onion", Script.ENGLISH),
    ("onion", "shinkurt", "shinkurt", Script.ENGLISH),
    ("onion", "shunkurtii", "shunkurtii", Script.LATIN),
    ("cooking_oil", "cooking oil", "cooking oil", Script.ENGLISH),
    ("cooking_oil", "oil", "oil", Script.ENGLISH),
    ("cooking_oil", "zayitii", "zayitii", Script.LATIN),
)


def _ethiopic_from_bot() -> tuple[tuple[str, str, str, Script], ...]:
    rows: list[tuple[str, str, str, Script]] = []
    for item in BOT_COMMODITIES:
        # Prefer short Amharic headword before parenthetical.
        surface = item.name_am.split("(")[0].strip()
        if surface:
            rows.append((item.code, surface, surface, Script.ETHIOPIC))
        if item.name_am.strip() and item.name_am.strip() != surface:
            full = item.name_am.strip()
            rows.append((item.code, full, full, Script.ETHIOPIC))
    return tuple(rows)


STAPLE_SYNONYMS: tuple[tuple[str, str, str, Script], ...] = (
    _LATIN_SYNONYMS + _ethiopic_from_bot()
)


def resolve_commodity_code_from_memory(text: str) -> str | None:
    script = detect_script(text)
    normalized = normalize_label(text, script=script)
    scripts_to_try = [script]
    if script == Script.ENGLISH:
        scripts_to_try.append(Script.LATIN)
    elif script == Script.LATIN:
        scripts_to_try.append(Script.ENGLISH)

    for row_code, _surface, row_norm, row_script in STAPLE_SYNONYMS:
        if row_script in scripts_to_try and row_norm == normalized:
            return row_code

    if script in {Script.ENGLISH, Script.LATIN}:
        for row_code, _surface, row_norm, row_script in STAPLE_SYNONYMS:
            if row_script in {Script.ENGLISH, Script.LATIN} and looks_like_close_latin(
                normalized, row_norm
            ):
                return row_code
    return None
