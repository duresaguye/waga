"""Track B constants — index, basket, heat, affordability bands."""

from __future__ import annotations

from decimal import Decimal

METHOD_VERSION_INDEX = "waga-index-v1"
METHOD_VERSION_AFFORDABILITY = "waga-affordability-v1"
METHOD_VERSION_HEAT = "waga-heat-v1"
METHOD_VERSION_COPILOT = "waga-copilot-v1"

WINDOW_HOURS = 72
MIN_SUBMISSIONS_TO_PUBLISH = 3
CITY_CODE = "addis_ababa"
CURRENCY = "ETB"

# Markets used for city aggregates / heat (exclude free-text "other").
PHASE1_MARKET_CODES: tuple[str, ...] = (
    "merkato",
    "shola",
    "ehil_berenda",
    "atikilt_tera",
    "piazza",
    "saris",
    "akaki",
    "asko",
    "kera",
)

PHASE1_COMMODITY_CODES: tuple[str, ...] = (
    "teff_mixed",
    "wheat",
    "maize",
    "onion",
    "cooking_oil",
)

# Household basket quantities for phase1_staple5 (per household_size=5 baseline).
BASKET_PHASE1: tuple[tuple[str, Decimal, str], ...] = (
    ("teff_mixed", Decimal("25"), "kg"),
    ("wheat", Decimal("10"), "kg"),
    ("maize", Decimal("10"), "kg"),
    ("onion", Decimal("6"), "kg"),
    ("cooking_oil", Decimal("3"), "liter"),
)


def heat_band(pct_change: float | None) -> str | None:
    if pct_change is None:
        return None
    if pct_change < -2:
        return "cool"
    if pct_change < 2:
        return "stable"
    if pct_change < 5:
        return "warm"
    if pct_change < 10:
        return "hot"
    return "critical"


def affordability_band(change_pct: float | None) -> tuple[float | None, str]:
    """Map basket % change → (score 0–10, band label)."""
    if change_pct is None:
        return None, "Unknown"
    score = max(0.0, min(10.0, round(abs(change_pct) / 2.0, 1)))
    if change_pct < 0:
        return score, "Easing"
    if change_pct < 5:
        return score, "Stable"
    if change_pct < 10:
        return score, "Elevated"
    if change_pct < 15:
        return score, "High"
    return score, "Severe"
