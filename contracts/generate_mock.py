"""Generate deterministic mock fixtures for the Waga v1 read API.

The frontend builds against these files while Track B implements the real endpoints.
Shapes match `docs/api-contracts-v1.md` and `contracts/types.ts` exactly.

    python contracts/generate_mock.py

Output goes to `contracts/mock/`. The seed is fixed, so re-running produces identical
files and diffs stay reviewable.

Stdlib only, on purpose: this must run without touching the backend's dependency set.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import statistics
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------------------
# Fixed world
# --------------------------------------------------------------------------------------

SEED = 20260725
DAYS = 90
END_DATE = date(2026, 7, 25)
GENERATED_AT = datetime(2026, 7, 25, 6, 0, 0, tzinfo=timezone.utc)
WINDOW_HOURS = 72
PUBLISH_THRESHOLD = 3
ETB_PER_USD = 140.0
SNAPSHOT_ID = "snap_2026-07-25T06_v1"
INDEX_METHOD = "waga-index-v1"

OUT_DIR = Path(__file__).parent / "mock"

MARKETS: list[dict[str, Any]] = [
    {"code": "merkato", "name_en": "Merkato", "name_am": "መርካቶ", "lat": 9.0341, "lon": 38.7395, "mult": 0.96},
    {"code": "ehil_berenda", "name_en": "Ehil Berenda", "name_am": "እህል በረንዳ", "lat": 9.0333, "lon": 38.7389, "mult": 0.97},
    {"code": "atikilt_tera", "name_en": "Atikilt Tera", "name_am": "አትክልት ተራ", "lat": 9.0300, "lon": 38.7450, "mult": 0.98},
    {"code": "asko", "name_en": "Asko", "name_am": "አስኮ", "lat": 9.0489, "lon": 38.6889, "mult": 0.99},
    {"code": "saris", "name_en": "Saris", "name_am": "ሳሪስ", "lat": 8.9797, "lon": 38.7622, "mult": 1.00},
    {"code": "akaki", "name_en": "Akaki", "name_am": "አቃቂ", "lat": 8.8939, "lon": 38.8069, "mult": 1.01},
    {"code": "kera", "name_en": "Kera", "name_am": "ቄራ", "lat": 8.9994, "lon": 38.7481, "mult": 1.03},
    {"code": "shola", "name_en": "Shola Gebeya", "name_am": "ሾላ ገበያ", "lat": 9.0244, "lon": 38.7986, "mult": 1.06},
    {"code": "piazza", "name_en": "Piazza", "name_am": "ፒያሳ", "lat": 9.0356, "lon": 38.7522, "mult": 1.08},
]

# Base city price at day -89, -30 and 0. Piecewise linear between the three, plus noise.
# Chosen so the 5-item basket lands near the 4,100 -> 4,850 demo story.
COMMODITIES: list[dict[str, Any]] = [
    {"code": "teff_mixed", "name_en": "Teff (mixed)", "name_am": "ጤፍ (ድብልቅ)", "unit": "kg",
     "category": "cereals and tubers", "hint": (80, 160), "path": (88.0, 95.0, 112.0)},
    {"code": "wheat", "name_en": "Wheat", "name_am": "ስንዴ", "unit": "kg",
     "category": "cereals and tubers", "hint": (45, 90), "path": (56.0, 60.0, 68.0)},
    {"code": "maize", "name_en": "Maize", "name_am": "በቆሎ", "unit": "kg",
     "category": "cereals and tubers", "hint": (28, 60), "path": (37.0, 40.0, 44.0)},
    {"code": "onion", "name_en": "Onion", "name_am": "ሽንኩርት", "unit": "kg",
     "category": "vegetables and fruits", "hint": (25, 80), "path": (34.0, 40.0, 55.0)},
    {"code": "cooking_oil", "name_en": "Cooking oil", "name_am": "የምግብ ዘይት", "unit": "liter",
     "category": "oil and fats", "hint": (120, 260), "path": (150.0, 162.0, 200.0)},
]

# Market specialisation. Discounts only on markets already below the median multiplier and
# premiums only on those above, so the city median stays anchored at the base path.
# No single market is cheapest for everything. That is the whole reason the sourcing product
# exists, so the fixture must not accidentally make one market win every commodity.
SPECIALISATION: dict[tuple[str, str], float] = {
    ("ehil_berenda", "teff_mixed"): 0.93,
    ("merkato", "wheat"): 0.94,
    ("merkato", "maize"): 0.95,
    ("atikilt_tera", "onion"): 0.90,
    ("atikilt_tera", "cooking_oil"): 0.95,
    ("piazza", "teff_mixed"): 1.02,
    ("shola", "onion"): 1.04,
    ("kera", "cooking_oil"): 1.02,
}

# Cells with no usable data right now, so the UI must render empty states.
DEAD_CELLS: set[tuple[str, str]] = {
    ("kera", "cooking_oil"),
    ("akaki", "teff_mixed"),
    ("asko", "onion"),
    ("piazza", "maize"),
    ("merkato", "cooking_oil"),
}

# Deliberate spikes so the alerts fixture exercises more than one band.
SPIKES: dict[tuple[str, str], tuple[int, float]] = {
    ("atikilt_tera", "onion"): (4, 1.26),
    ("kera", "maize"): (6, 1.14),
}

BASKET = {
    "code": "phase1_staple5",
    "name_en": "Addis staple basket (5 items)",
    "household_size": 5,
    "period_days": 30,
    "items": [
        {"commodity_code": "teff_mixed", "quantity": 25, "unit": "kg"},
        {"commodity_code": "wheat", "quantity": 10, "unit": "kg"},
        {"commodity_code": "maize", "quantity": 10, "unit": "kg"},
        {"commodity_code": "onion", "quantity": 6, "unit": "kg"},
        {"commodity_code": "cooking_oil", "quantity": 3, "unit": "liter"},
    ],
}

MARKET_BY_CODE = {m["code"]: m for m in MARKETS}
COMMODITY_BY_CODE = {c["code"]: c for c in COMMODITIES}
DATES = [END_DATE - timedelta(days=DAYS - 1 - i) for i in range(DAYS)]

rng = random.Random(SEED)


# --------------------------------------------------------------------------------------
# Price surface
# --------------------------------------------------------------------------------------


def base_price(commodity_code: str, day_index: int) -> float:
    """Piecewise linear city price. day_index 0 is the oldest day, DAYS-1 is today."""
    start, mid, end = COMMODITY_BY_CODE[commodity_code]["path"]
    mid_index = DAYS - 31
    if day_index <= mid_index:
        t = day_index / mid_index
        return start + (mid - start) * t
    t = (day_index - mid_index) / (DAYS - 1 - mid_index)
    return mid + (end - mid) * t


def build_surface() -> dict[tuple[str, str], list[dict[str, Any]]]:
    """market_code, commodity_code -> one entry per day."""
    surface: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for market in MARKETS:
        for commodity in COMMODITIES:
            key = (market["code"], commodity["code"])
            multiplier = market["mult"] * SPECIALISATION.get(key, 1.0)
            drift = 0.0
            days: list[dict[str, Any]] = []

            for day_index, day in enumerate(DATES):
                drift = drift * 0.7 + rng.gauss(0, 0.008)
                value = base_price(commodity["code"], day_index) * multiplier * (1 + drift)

                if key in SPIKES:
                    spike_days, spike_factor = SPIKES[key]
                    if day_index >= DAYS - spike_days:
                        ramp = (day_index - (DAYS - spike_days) + 1) / spike_days
                        value *= 1 + (spike_factor - 1) * ramp

                is_today = day_index == DAYS - 1
                if key in DEAD_CELLS and is_today:
                    published = False
                else:
                    published = rng.random() > 0.07

                if published:
                    n_sub = rng.randint(PUBLISH_THRESHOLD, 9)
                    reason = None
                else:
                    n_sub = rng.randint(0, PUBLISH_THRESHOLD - 1)
                    reason = "no_submissions" if n_sub == 0 else "below_threshold"

                n_agent = max(1, round(n_sub * 0.75)) if n_sub else 0
                source_mix: dict[str, int] = {}
                if n_agent:
                    source_mix["agent"] = n_agent
                if n_sub - n_agent > 0:
                    source_mix["user"] = n_sub - n_agent

                days.append({
                    "date": day,
                    "value": round(value, 2) if published else None,
                    "status": "published" if published else "insufficient_data",
                    "n_submissions": n_sub,
                    "n_contributors": max(1, math.ceil(n_sub * 0.6)) if n_sub else 0,
                    "source_mix": source_mix,
                    "insufficient_reason": reason,
                })

            surface[key] = days

    return surface


SURFACE = build_surface()


def city_price(commodity_code: str, day_index: int) -> float | None:
    """Median across published market cells for a commodity on one day."""
    values = [
        SURFACE[(m["code"], commodity_code)][day_index]["value"]
        for m in MARKETS
        if SURFACE[(m["code"], commodity_code)][day_index]["value"] is not None
    ]
    return round(statistics.median(values), 2) if values else None


CITY_SERIES = {
    c["code"]: [city_price(c["code"], i) for i in range(DAYS)] for c in COMMODITIES
}
TODAY = DAYS - 1


def pct_change(now: float | None, prior: float | None) -> float | None:
    if now is None or prior in (None, 0):
        return None
    return round((now - prior) / prior * 100, 1)


def last_valid(series: list[float | None], index: int) -> float | None:
    """Nearest non-null value at or before index. Used for reference points, never to fill a gap."""
    for i in range(index, -1, -1):
        if series[i] is not None:
            return series[i]
    return None


# --------------------------------------------------------------------------------------
# Envelope
# --------------------------------------------------------------------------------------


def iso(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def coverage_counts() -> tuple[int, int, int]:
    expected = len(MARKETS) * len(COMMODITIES)
    published = sum(
        1 for m in MARKETS for c in COMMODITIES
        if SURFACE[(m["code"], c["code"])][TODAY]["status"] == "published"
    )
    return expected, published, expected - published


def meta(method_version: str = INDEX_METHOD) -> dict[str, Any]:
    expected, published, insufficient = coverage_counts()
    return {
        "generated_at": iso(GENERATED_AT),
        "method_version": method_version,
        "city": "addis_ababa",
        "currency": "ETB",
        "window": {
            "start": iso(GENERATED_AT - timedelta(hours=WINDOW_HOURS)),
            "end": iso(GENERATED_AT),
            "hours": WINDOW_HOURS,
        },
        "coverage": {
            "cells_expected": expected,
            "cells_published": published,
            "cells_insufficient": insufficient,
            "coverage_pct": round(published / expected * 100, 1),
        },
        "licence_class": "commercial_permitted",
        "snapshot_id": SNAPSHOT_ID,
    }


def envelope(data: Any, method_version: str = INDEX_METHOD) -> dict[str, Any]:
    return {"meta": meta(method_version), "data": data}


def price_cell(market_code: str, commodity_code: str, day_index: int = TODAY) -> dict[str, Any]:
    market = MARKET_BY_CODE[market_code]
    commodity = COMMODITY_BY_CODE[commodity_code]
    entry = SURFACE[(market_code, commodity_code)][day_index]
    return {
        "market_code": market_code,
        "market_name_en": market["name_en"],
        "market_name_am": market["name_am"],
        "commodity_code": commodity_code,
        "commodity_name_en": commodity["name_en"],
        "commodity_name_am": commodity["name_am"],
        "unit": commodity["unit"],
        "currency": "ETB",
        "status": entry["status"],
        "value": entry["value"],
        "n_submissions": entry["n_submissions"],
        "n_contributors": entry["n_contributors"],
        "source_mix": entry["source_mix"],
        "window_start": iso(GENERATED_AT - timedelta(hours=WINDOW_HOURS)),
        "window_end": iso(GENERATED_AT),
        "computed_at": iso(GENERATED_AT),
        "method_version": INDEX_METHOD,
        "insufficient_reason": entry["insufficient_reason"],
    }


# --------------------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------------------


def build_reference() -> dict[str, Any]:
    payload = {
        "city": {"code": "addis_ababa", "name_en": "Addis Ababa", "name_am": "አዲስ አበባ"},
        "markets": [
            {
                "code": m["code"],
                "name_en": m["name_en"],
                "name_am": m["name_am"],
                "latitude": m["lat"],
                "longitude": m["lon"],
                "is_active": True,
            }
            for m in MARKETS
        ],
        "commodities": [
            {
                "code": c["code"],
                "name_en": c["name_en"],
                "name_am": c["name_am"],
                "category": c["category"],
                "unit": c["unit"],
                "price_hint_low": c["hint"][0],
                "price_hint_high": c["hint"][1],
            }
            for c in COMMODITIES
        ],
        "baskets": [BASKET],
    }
    return envelope(payload)


def build_prices_current() -> dict[str, Any]:
    cells = [price_cell(m["code"], c["code"]) for m in MARKETS for c in COMMODITIES]

    city_prices = []
    for commodity in COMMODITIES:
        published = [
            (m["code"], SURFACE[(m["code"], commodity["code"])][TODAY]["value"])
            for m in MARKETS
            if SURFACE[(m["code"], commodity["code"])][TODAY]["value"] is not None
        ]
        if published:
            cheapest = min(published, key=lambda pair: pair[1])
            dearest = max(published, key=lambda pair: pair[1])
            city_prices.append({
                "commodity_code": commodity["code"],
                "unit": commodity["unit"],
                "status": "published",
                "value": CITY_SERIES[commodity["code"]][TODAY],
                "markets_published": len(published),
                "markets_expected": len(MARKETS),
                "min": {"market_code": cheapest[0], "value": cheapest[1]},
                "max": {"market_code": dearest[0], "value": dearest[1]},
                "spread_pct": round((dearest[1] - cheapest[1]) / cheapest[1] * 100, 1),
            })
        else:
            city_prices.append({
                "commodity_code": commodity["code"],
                "unit": commodity["unit"],
                "status": "insufficient_data",
                "value": None,
                "markets_published": 0,
                "markets_expected": len(MARKETS),
                "min": None,
                "max": None,
                "spread_pct": None,
            })

    return envelope({"cells": cells, "city_prices": city_prices})


def build_prices_series() -> dict[str, Any]:
    series = []
    for commodity in COMMODITIES:
        points = []
        for day_index, day in enumerate(DATES):
            value = CITY_SERIES[commodity["code"]][day_index]
            n_sub = sum(
                SURFACE[(m["code"], commodity["code"])][day_index]["n_submissions"]
                for m in MARKETS
            )
            points.append({
                "date": day.isoformat(),
                "value": value,
                "status": "published" if value is not None else "insufficient_data",
                "n_submissions": n_sub,
            })
        series.append({
            "commodity_code": commodity["code"],
            "market_code": None,
            "unit": commodity["unit"],
            "points": points,
        })
    return envelope({"interval": "day", "series": series})


def build_prices_series_by_market(window_days: int = 30) -> dict[str, Any]:
    start = DAYS - window_days
    series = []
    for market in MARKETS:
        for commodity in COMMODITIES:
            entries = SURFACE[(market["code"], commodity["code"])][start:]
            series.append({
                "commodity_code": commodity["code"],
                "market_code": market["code"],
                "unit": commodity["unit"],
                "points": [
                    {
                        "date": e["date"].isoformat(),
                        "value": e["value"],
                        "status": e["status"],
                        "n_submissions": e["n_submissions"],
                    }
                    for e in entries
                ],
            })
    return envelope({"interval": "day", "series": series})


def build_coverage() -> dict[str, Any]:
    matrix = []
    worst: list[dict[str, Any]] = []

    for market in MARKETS:
        cells = []
        for commodity in COMMODITIES:
            entries = SURFACE[(market["code"], commodity["code"])]
            entry = entries[TODAY]
            hours = None
            for offset in range(DAYS):
                if entries[TODAY - offset]["status"] == "published":
                    hours = round(offset * 24 + rng.uniform(0.5, 8.0), 1)
                    break
            cells.append({
                "commodity_code": commodity["code"],
                "status": entry["status"],
                "n_submissions": entry["n_submissions"],
                "hours_since_last": hours,
            })
            if entry["status"] != "published":
                worst.append({
                    "market_code": market["code"],
                    "commodity_code": commodity["code"],
                    "hours_since_last": hours,
                })
        matrix.append({"market_code": market["code"], "cells": cells})

    worst.sort(key=lambda row: -(row["hours_since_last"] or 0))
    return envelope({"matrix": matrix, "worst_covered": worst[:10]})


def affordability_band(change: float) -> str:
    if change < 3:
        return "Stable"
    if change < 8:
        return "Watch"
    if change < 15:
        return "Tightening"
    return "Severe"


def basket_cost(day_index: int) -> tuple[float | None, list[str]]:
    total = 0.0
    missing = []
    for item in BASKET["items"]:
        price = last_valid(CITY_SERIES[item["commodity_code"]], day_index)
        if price is None:
            missing.append(item["commodity_code"])
        else:
            total += price * item["quantity"]
    return (None, missing) if missing else (round(total, 2), [])


def build_affordability() -> dict[str, Any]:
    prior_index = TODAY - 30
    cost_now, missing_now = basket_cost(TODAY)
    cost_prior, missing_prior = basket_cost(prior_index)
    missing = sorted(set(missing_now) | set(missing_prior))

    items = []
    total_change = (cost_now - cost_prior) if (cost_now and cost_prior) else None

    for item in BASKET["items"]:
        code = item["commodity_code"]
        now = last_valid(CITY_SERIES[code], TODAY)
        prior = last_valid(CITY_SERIES[code], prior_index)
        cost_item_now = round(now * item["quantity"], 2) if now else None
        cost_item_prior = round(prior * item["quantity"], 2) if prior else None
        contribution = None
        if cost_item_now and cost_item_prior and total_change:
            contribution = round((cost_item_now - cost_item_prior) / total_change * 100, 1)
        items.append({
            "commodity_code": code,
            "quantity": item["quantity"],
            "unit": item["unit"],
            "unit_price_now": now,
            "unit_price_prior": prior,
            "cost_now": cost_item_now,
            "cost_prior": cost_item_prior,
            "change_pct": pct_change(now, prior),
            "contribution_to_change_pct": contribution,
            "status": "published" if now is not None else "insufficient_data",
        })

    change = pct_change(cost_now, cost_prior)
    payload = {
        "basket_code": BASKET["code"],
        "household_size": BASKET["household_size"],
        "period_days": BASKET["period_days"],
        "status": "insufficient_data" if missing else "published",
        "cost_now": cost_now,
        "cost_prior": cost_prior,
        "prior_date": DATES[prior_index].isoformat(),
        "change_abs": round(total_change, 2) if total_change else None,
        "change_pct": change,
        "score": round(max(0.0, min(100.0, 100 - 5 * change)), 1) if change is not None else None,
        "band": affordability_band(change) if change is not None else None,
        "method_version": "waga-affordability-v1",
        "items": items,
        "missing_commodities": missing,
    }
    return envelope(payload, "waga-affordability-v1")


def heat_band(change: float) -> str:
    if change < -2:
        return "cool"
    if change < 2:
        return "stable"
    if change < 5:
        return "warm"
    if change < 10:
        return "hot"
    return "critical"


def build_heatmap(lookback: int = 7) -> dict[str, Any]:
    prior_index = TODAY - lookback
    markets_out = []
    hottest = None

    for market in MARKETS:
        cells = []
        weighted_sum = 0.0
        weight_total = 0.0
        published_count = 0

        for commodity in COMMODITY_BY_CODE.values():
            entries = SURFACE[(market["code"], commodity["code"])]
            now = entries[TODAY]["value"]
            prior = last_valid([e["value"] for e in entries], prior_index)
            change = pct_change(now, prior)
            if now is not None and change is not None:
                published_count += 1
                weight = entries[TODAY]["n_submissions"]
                weighted_sum += change * weight
                weight_total += weight
                if hottest is None or change > hottest["pct_change"]:
                    hottest = {
                        "market_code": market["code"],
                        "commodity_code": commodity["code"],
                        "pct_change": change,
                    }
            cells.append({
                "commodity_code": commodity["code"],
                "status": entries[TODAY]["status"],
                "value": now,
                "pct_change": change,
                "band": heat_band(change) if change is not None else None,
            })

        enough = published_count >= 2 and weight_total > 0
        heat = round(weighted_sum / weight_total, 1) if enough else None
        markets_out.append({
            "market_code": market["code"],
            "market_name_en": market["name_en"],
            "latitude": market["lat"],
            "longitude": market["lon"],
            "status": "published" if enough else "insufficient_data",
            "heat": heat,
            "band": heat_band(heat) if heat is not None else None,
            "cells_published": published_count,
            "cells_expected": len(COMMODITIES),
            "cells": cells,
        })

    payload = {
        "metric": f"pct_change_{lookback}d",
        "method_version": "waga-heat-v1",
        "markets": markets_out,
        "hottest_cell": hottest,
    }
    return envelope(payload, "waga-heat-v1")


SPIKE_WINDOW = 30
SPIKE_MIN_OBSERVATIONS = 12
SPIKE_MIN_DEVIATION_PCT = 2.0

BANDS = ("normal", "stress", "alert", "crisis")
SPIKE_Z_THRESHOLDS = (1.0, 2.0, 3.0)
SPIKE_DEVIATION_THRESHOLDS = (2.0, 5.0, 10.0)


def _band_index(value: float, thresholds: tuple[float, ...]) -> int:
    return sum(1 for threshold in thresholds if value >= threshold)


def spike_band(z: float, deviation_pct: float) -> str:
    """Take the weaker of the statistical and the economic signal.

    A cell with a tight price history can post a large z-score on a 2% move. That is
    statistically unusual but economically trivial, and flagging it as an alert is how a
    monitoring product loses credibility. Requiring both keeps the bands meaningful.
    """
    return BANDS[
        min(
            _band_index(z, SPIKE_Z_THRESHOLDS),
            _band_index(deviation_pct, SPIKE_DEVIATION_THRESHOLDS),
        )
    ]


def fit_trend(points: list[tuple[int, float]]) -> tuple[float, float]:
    """Ordinary least squares slope and intercept over (day_index, price)."""
    n = len(points)
    mean_x = statistics.fmean(x for x, _ in points)
    mean_y = statistics.fmean(y for _, y in points)
    denominator = sum((x - mean_x) ** 2 for x, _ in points)
    slope = (
        sum((x - mean_x) * (y - mean_y) for x, y in points) / denominator
        if denominator
        else 0.0
    )
    return slope, mean_y - slope * mean_x


def spike_scores(market_code: str, commodity_code: str) -> dict[int, tuple[float, float]]:
    """day_index -> (spike score, expected price) over the trailing window.

    Detrend before scoring, the same way ALPS regresses price on a trend before taking the
    residual. Without this a steadily rising series scores every day as a spike.
    """
    entries = SURFACE[(market_code, commodity_code)]
    observed = [
        (i, entries[i]["value"])
        for i in range(max(TODAY - SPIKE_WINDOW, 0), TODAY + 1)
        if entries[i]["value"] is not None
    ]
    if len(observed) < SPIKE_MIN_OBSERVATIONS:
        return {}

    slope, intercept = fit_trend(observed)
    residuals = {i: value - (slope * i + intercept) for i, value in observed}
    sigma = statistics.pstdev(residuals.values())
    if sigma <= 0:
        return {}

    return {
        i: (residuals[i] / sigma, slope * i + intercept) for i, _ in observed
    }


def build_alerts() -> dict[str, Any]:
    alerts = []
    for market in MARKETS:
        for commodity in COMMODITIES:
            entries = SURFACE[(market["code"], commodity["code"])]
            now = entries[TODAY]["value"]
            if now is None:
                continue

            scores = spike_scores(market["code"], commodity["code"])
            if TODAY not in scores:
                continue

            spike, expected = scores[TODAY]
            deviation_pct = (now - expected) / expected * 100
            if spike < SPIKE_Z_THRESHOLDS[0] or deviation_pct < SPIKE_MIN_DEVIATION_PCT:
                continue

            consecutive = 0
            for offset in range(TODAY, max(TODAY - 14, 0), -1):
                if offset not in scores or scores[offset][0] < SPIKE_Z_THRESHOLDS[0]:
                    break
                consecutive += 1

            history = [
                e["value"]
                for e in entries[TODAY - SPIKE_WINDOW:TODAY]
                if e["value"] is not None
            ]
            alerts.append({
                "market_code": market["code"],
                "commodity_code": commodity["code"],
                "spike": round(spike, 2),
                "band": spike_band(spike, deviation_pct),
                "value": now,
                "expected": round(expected, 2),
                "median_30d": round(statistics.median(history), 2),
                "pct_above_expected": round(deviation_pct, 1),
                "first_detected_at": iso(GENERATED_AT - timedelta(days=max(consecutive - 1, 0))),
                "consecutive_days": consecutive,
            })

    alerts.sort(key=lambda row: -row["spike"])
    payload = {
        "method_version": "waga-spike-v1",
        "alps_comparable": False,
        "alps_comparable_note": (
            "Detrended residual z-score over a 30-day daily window, banded jointly with the "
            "percent deviation from trend. Same structure as WFP ALPS but daily rather than "
            "monthly. Real ALPS needs 24 monthly observations per cell."
        ),
        "window_days": SPIKE_WINDOW,
        "min_deviation_pct": SPIKE_MIN_DEVIATION_PCT,
        "z_thresholds": list(SPIKE_Z_THRESHOLDS),
        "deviation_thresholds_pct": list(SPIKE_DEVIATION_THRESHOLDS),
        "alerts": alerts,
    }
    return envelope(payload, "waga-spike-v1")


def build_meb_food_line() -> dict[str, Any]:
    cost_now, _ = basket_cost(TODAY)
    cost_prior, _ = basket_cost(TODAY - 30)
    payload = {
        "household_size": BASKET["household_size"],
        "waga_food_line_now": cost_now,
        "waga_food_line_prior": cost_prior,
        "change_pct": pct_change(cost_now, cost_prior),
        "coverage_note": (
            "Waga prices 5 of the 53 ECWG MEB items. This is the tracked-staple line only."
        ),
        "ecwg_reference": {
            "source": "ECWG MEB National Reference Guide, June 2025",
            "national_meb_full_etb": 17700.0,
            "national_meb_food_etb": 16135.0,
            "as_of": "2025-12-01",
            "review_cadence_months": 3,
            "revision_trigger": "Six consecutive months of price movement in one direction",
        },
        "consecutive_months_rising": 4,
        "revision_trigger_met": False,
    }
    return envelope(payload)


def build_copilot() -> dict[str, Any]:
    cost_now, _ = basket_cost(TODAY)
    cost_prior, _ = basket_cost(TODAY - 30)
    change = pct_change(cost_now, cost_prior)
    gap = round(cost_now - cost_prior, 2)
    households = 50000

    teff_now = last_valid(CITY_SERIES["teff_mixed"], TODAY)
    teff_prior = last_valid(CITY_SERIES["teff_mixed"], TODAY - 30)
    teff_share = round(
        (teff_now - teff_prior) * 25 / (cost_now - cost_prior) * 100, 1
    )

    low = math.floor(change - 3)
    high = math.ceil(change)
    _, published, _ = coverage_counts()
    expected = len(MARKETS) * len(COMMODITIES)

    payload = {
        "answer": (
            f"The Addis staple basket rose from {cost_prior:,.0f} to {cost_now:,.0f} ETB over the "
            f"last 30 days, an increase of {change}%. Teff accounts for {teff_share}% of that "
            f"increase. A transfer value set against last month's basket now covers roughly "
            f"{round(cost_prior / cost_now * 100)}% of the same goods. An adjustment of "
            f"{low}\u2013{high}% would restore purchasing power."
        ),
        "recommendation": {
            "action": "increase_transfer_value",
            "band_low_pct": float(low),
            "band_high_pct": float(high),
            "confidence": "medium",
            "confidence_reason": (
                f"{published} of {expected} cells published in the last 72h; "
                "cooking oil coverage is thin."
            ),
        },
        "citations": [
            {
                "label": "Basket cost now",
                "value": cost_now,
                "unit": "ETB",
                "source": "/affordability",
                "cell_refs": [f"addis_ababa:phase1_staple5:{END_DATE.isoformat()}"],
            },
            {
                "label": "Basket cost 30 days ago",
                "value": cost_prior,
                "unit": "ETB",
                "source": "/affordability",
                "cell_refs": [
                    f"addis_ababa:phase1_staple5:{DATES[TODAY - 30].isoformat()}"
                ],
            },
            {
                "label": "Teff city median",
                "value": teff_now,
                "unit": "ETB/kg",
                "source": "/prices/current",
                "cell_refs": [f"addis_ababa:teff_mixed:{END_DATE.isoformat()}"],
            },
        ],
        "impact": {
            "household_count": households,
            "gap_per_household_etb": gap,
            "monthly_total_etb": round(gap * households, 2),
            "note": "Cost of leaving the transfer value unchanged for one month.",
        },
        "mode": "rule_based",
    }
    return envelope(payload, "waga-copilot-v1")


def build_impact() -> dict[str, Any]:
    cost_now, _ = basket_cost(TODAY)
    cost_prior, _ = basket_cost(TODAY - 30)
    gap = round(cost_now - cost_prior, 2)
    households = 50000
    months = 3
    payload = {
        "household_count": households,
        "gap_per_household_etb": gap,
        "monthly_total_etb": round(gap * households, 2),
        "months": months,
        "total_etb": round(gap * households * months, 2),
        "note": f"Cost of leaving the transfer value unchanged for {months} months.",
    }
    return envelope(payload, "waga-impact-v1")


BUSINESS_ITEMS = [
    {"commodity_code": "teff_mixed", "quantity": 400, "unit": "kg"},
    {"commodity_code": "wheat", "quantity": 120, "unit": "kg"},
    {"commodity_code": "cooking_oil", "quantity": 60, "unit": "liter"},
]


def business_basket_cost(day_index: int) -> float | None:
    total = 0.0
    for item in BUSINESS_ITEMS:
        price = last_valid(CITY_SERIES[item["commodity_code"]], day_index)
        if price is None:
            return None
        total += price * item["quantity"]
    return round(total, 2)


def build_cost_index() -> dict[str, Any]:
    base_index = 0
    base_cost = business_basket_cost(base_index)
    now_cost = business_basket_cost(TODAY)
    prior_cost = business_basket_cost(TODAY - 30)

    series = []
    values_30d = []
    for day_index, day in enumerate(DATES):
        cost = business_basket_cost(day_index)
        value = round(cost / base_cost * 100, 2) if cost else None
        series.append({
            "date": day.isoformat(),
            "value": value,
            "status": "published" if value is not None else "insufficient_data",
        })
        if day_index >= TODAY - 30 and cost:
            values_30d.append(cost)

    mean_30d = statistics.fmean(values_30d)
    stdev_30d = statistics.pstdev(values_30d)
    median_30d = statistics.median(values_30d)

    items = []
    for item in BUSINESS_ITEMS:
        price = last_valid(CITY_SERIES[item["commodity_code"]], TODAY)
        cost = round(price * item["quantity"], 2) if price else None
        items.append({
            "commodity_code": item["commodity_code"],
            "quantity": item["quantity"],
            "unit": item["unit"],
            "unit_price": price,
            "cost_etb": cost,
            "share_pct": round(cost / now_cost * 100, 1) if cost and now_cost else None,
            "status": "published" if price is not None else "insufficient_data",
        })

    payload = {
        "method_version": "waga-cost-index-v1",
        "base_date": DATES[base_index].isoformat(),
        "base_value": 100.0,
        "current_value": round(now_cost / base_cost * 100, 2),
        "change_pct_30d": pct_change(now_cost, prior_cost),
        "monthly_cost_now_etb": now_cost,
        "monthly_cost_base_etb": base_cost,
        "volatility_30d_pct": round(stdev_30d / mean_30d * 100, 1),
        "planning_band": {
            "low_etb": round(median_30d - 1.28 * stdev_30d, 2),
            "high_etb": round(median_30d + 1.28 * stdev_30d, 2),
            "confidence": 0.8,
        },
        "items": items,
        "series": series,
    }
    return envelope(payload, "waga-cost-index-v1")


def commodity_volatility(commodity_code: str) -> float | None:
    values = [v for v in CITY_SERIES[commodity_code][TODAY - 30:] if v is not None]
    if len(values) < 5:
        return None
    return round(statistics.pstdev(values) / statistics.fmean(values) * 100, 1)


def build_sourcing() -> dict[str, Any]:
    out = []
    for commodity in COMMODITIES:
        median = CITY_SERIES[commodity["code"]][TODAY]
        markets_out = []
        published = []

        for market in MARKETS:
            entry = SURFACE[(market["code"], commodity["code"])][TODAY]
            markets_out.append({
                "market_code": market["code"],
                "market_name_en": market["name_en"],
                "status": entry["status"],
                "value": entry["value"],
                "diff_from_median_pct": pct_change(entry["value"], median),
                "n_submissions": entry["n_submissions"],
            })
            if entry["value"] is not None:
                published.append((market["code"], entry["value"], entry["n_submissions"]))

        if published:
            cheapest = min(published, key=lambda row: row[1])
            dearest = max(published, key=lambda row: row[1])
            out.append({
                "commodity_code": commodity["code"],
                "unit": commodity["unit"],
                "city_median": median,
                "cheapest": {
                    "market_code": cheapest[0], "value": cheapest[1], "n_submissions": cheapest[2],
                },
                "dearest": {
                    "market_code": dearest[0], "value": dearest[1], "n_submissions": dearest[2],
                },
                "spread_pct": round((dearest[1] - cheapest[1]) / cheapest[1] * 100, 1),
                "saving_per_unit_etb": round(median - cheapest[1], 2),
                "volatility_30d_pct": commodity_volatility(commodity["code"]),
                "markets": markets_out,
            })
        else:
            out.append({
                "commodity_code": commodity["code"],
                "unit": commodity["unit"],
                "city_median": None,
                "cheapest": None,
                "dearest": None,
                "spread_pct": None,
                "saving_per_unit_etb": None,
                "volatility_30d_pct": commodity_volatility(commodity["code"]),
                "markets": markets_out,
            })

    return envelope({"commodities": out})


def benchmark_verdict(diff: float) -> str:
    if diff < -5:
        return "below_market"
    if diff < 5:
        return "at_market"
    if diff < 20:
        return "above_market"
    return "far_above_market"


def build_benchmark(quoted: float = 130.0) -> dict[str, Any]:
    median = CITY_SERIES["teff_mixed"][TODAY]
    diff = round((quoted - median) / median * 100, 1)

    history = [
        e["value"]
        for m in MARKETS
        for e in SURFACE[(m["code"], "teff_mixed")][TODAY - 30:]
        if e["value"] is not None
    ]
    percentile = round(sum(1 for v in history if v < quoted) / len(history) * 100)

    published = [
        (m["code"], SURFACE[(m["code"], "teff_mixed")][TODAY]["value"])
        for m in MARKETS
        if SURFACE[(m["code"], "teff_mixed")][TODAY]["value"] is not None
    ]
    cheapest = min(published, key=lambda row: row[1])

    payload = {
        "commodity_code": "teff_mixed",
        "quoted_price": quoted,
        "city_median": median,
        "diff_pct": diff,
        "percentile": percentile,
        "verdict": benchmark_verdict(diff),
        "message": (
            f"This quote is {diff}% above the Addis median and higher than {percentile}% of "
            f"prices recorded in the last 30 days. "
            f"{MARKET_BY_CODE[cheapest[0]]['name_en']} published "
            f"{cheapest[1]:.2f} ETB/kg today."
        ),
        "cheapest_alternative": {"market_code": cheapest[0], "value": cheapest[1]},
    }
    return envelope(payload, "waga-benchmark-v1")


def build_business_ask() -> dict[str, Any]:
    median = CITY_SERIES["teff_mixed"][TODAY]
    published = [
        (m["code"], SURFACE[(m["code"], "teff_mixed")][TODAY]["value"])
        for m in MARKETS
        if SURFACE[(m["code"], "teff_mixed")][TODAY]["value"] is not None
    ]
    cheapest = min(published, key=lambda row: row[1])
    quantity = 400
    change_30d = pct_change(median, last_valid(CITY_SERIES["teff_mixed"], TODAY - 30))
    volatility = commodity_volatility("teff_mixed")
    saving = round((median - cheapest[1]) * quantity, 0)
    low = round(cheapest[1] * quantity, 0)
    high = round(median * quantity * 1.05, 0)

    payload = {
        "answer": (
            f"Budget {low:,.0f}\u2013{high:,.0f} ETB a month for {quantity}kg of teff at current "
            f"prices. Buy at {MARKET_BY_CODE[cheapest[0]]['name_en']}, where teff published at "
            f"{cheapest[1]:.2f} ETB/kg today against a city median of {median:.2f} \u2014 about "
            f"{saving:,.0f} ETB a month cheaper. Teff has risen {change_30d}% in 30 days and "
            f"30-day volatility is {volatility}%, so this is not a good week to lock a six-month "
            f"fixed price."
        ),
        "verdict": {
            "action": "source_at_alternative_market",
            "confidence": "high",
            "confidence_reason": (
                f"Teff published in {len(published)} of {len(MARKETS)} markets in the last 72h."
            ),
        },
        "drivers": [
            {"label": "Teff 30-day change", "value": change_30d, "unit": "%", "direction": "up"},
            {"label": "Teff 30-day volatility", "value": volatility, "unit": "%", "direction": "up"},
            {
                "label": "Cheapest vs city median",
                "value": round((cheapest[1] - median) / median * 100, 1),
                "unit": "%",
                "direction": "down",
            },
        ],
        "citations": [
            {
                "label": f"{MARKET_BY_CODE[cheapest[0]]['name_en']} teff",
                "value": cheapest[1],
                "unit": "ETB/kg",
                "source": "/prices/current",
                "cell_refs": [f"{cheapest[0]}:teff_mixed:{END_DATE.isoformat()}"],
            },
            {
                "label": "Addis teff median",
                "value": median,
                "unit": "ETB/kg",
                "source": "/prices/current",
                "cell_refs": [f"addis_ababa:teff_mixed:{END_DATE.isoformat()}"],
            },
        ],
        "mode": "rule_based",
    }
    return envelope(payload, "waga-business-copilot-v1")


# --------------------------------------------------------------------------------------
# Research surface
# --------------------------------------------------------------------------------------

PANEL_COLUMNS = [
    "date", "admin1", "admin2", "market", "latitude", "longitude", "category", "commodity",
    "unit", "priceflag", "pricetype", "currency", "price", "usdprice",
    "n_submissions", "n_contributors", "source_mix", "status", "method_version", "snapshot_id",
]

PANEL_HXL = [
    "#date", "#adm1+name", "#adm2+name", "#loc+market+name", "#geo+lat", "#geo+lon",
    "#item+type", "#item+name", "#item+unit", "#item+price+flag", "#item+price+type",
    "#currency", "#value", "#value+usd", "#meta+count", "#meta+contributors", "#meta+sources",
    "#status+code", "#meta+method", "#meta+snapshot",
]

WFP_UNIT = {"kg": "KG", "liter": "L"}


def build_panel_rows() -> list[list[Any]]:
    rows = []
    for day_index, day in enumerate(DATES):
        for market in MARKETS:
            for commodity in COMMODITIES:
                entry = SURFACE[(market["code"], commodity["code"])][day_index]
                value = entry["value"]
                rows.append([
                    day.isoformat(),
                    "Addis Ababa",
                    "Addis Ababa",
                    market["name_en"],
                    market["lat"],
                    market["lon"],
                    commodity["category"],
                    commodity["name_en"],
                    WFP_UNIT[commodity["unit"]],
                    "actual",
                    "Retail",
                    "ETB",
                    f"{value:.2f}" if value is not None else "",
                    f"{value / ETB_PER_USD:.4f}" if value is not None else "",
                    entry["n_submissions"],
                    entry["n_contributors"],
                    "|".join(f"{k}:{v}" for k, v in entry["source_mix"].items()),
                    entry["status"],
                    INDEX_METHOD,
                    SNAPSHOT_ID,
                ])
    return rows


def write_panel_csv(path: Path) -> tuple[int, int, str]:
    rows = build_panel_rows()
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(PANEL_COLUMNS)
        writer.writerow(PANEL_HXL)
        writer.writerows(rows)
    published = sum(1 for row in rows if row[17] == "published")
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    return len(rows), published, checksum


def build_snapshots(row_count: int, published: int, checksum: str) -> dict[str, Any]:
    payload = {
        "snapshots": [
            {
                "snapshot_id": SNAPSHOT_ID,
                "created_at": iso(GENERATED_AT),
                "method_version": INDEX_METHOD,
                "temporal_coverage": {
                    "start": DATES[0].isoformat(),
                    "end": DATES[-1].isoformat(),
                },
                "spatial_coverage": {"city": "addis_ababa", "markets": len(MARKETS)},
                "commodities": len(COMMODITIES),
                "row_count": row_count,
                "rows_published": published,
                "rows_insufficient": row_count - published,
                "licence": "CC-BY-4.0",
                "checksum_sha256": checksum,
                "citation": (
                    f"Waga Intelligence (2026). Addis Ababa Market Price Index, snapshot "
                    f"{SNAPSHOT_ID}. https://waga.et/data/{SNAPSHOT_ID}"
                ),
                "download": {
                    "csv": f"/api/v1/exports/panel.csv?snapshot={SNAPSHOT_ID}",
                    "parquet": None,
                },
                "immutable": True,
            }
        ]
    }
    return envelope(payload)


def build_methodology() -> dict[str, Any]:
    payload = {
        "method_version": INDEX_METHOD,
        "effective_from": "2026-04-01",
        "window_hours": WINDOW_HOURS,
        "publish_threshold_submissions": PUBLISH_THRESHOLD,
        "aggregation": "weighted median",
        "source_weights": {"agent": 2.0, "user": 1.0, "scraped": 0.5, "seed": 0.5},
        "recency_weight": "linear 0.5 \u2192 1.0 across the window",
        "imputation": "none",
        "below_threshold_behaviour": "insufficient_data, value null",
        "changelog": [
            {"version": INDEX_METHOD, "date": "2026-04-01", "change": "Initial release."}
        ],
    }
    return envelope(payload)


CODEBOOK_DESCRIPTIONS: dict[str, tuple[str, str, str | None, bool, list[str] | None]] = {
    "date": ("date", "Observation date of the index window end.", None, False, None),
    "admin1": ("string", "First-level administrative unit.", None, False, None),
    "admin2": ("string", "Second-level administrative unit.", None, False, None),
    "market": ("string", "Named marketplace within the city.", None, False, None),
    "latitude": ("number", "Market latitude, WGS84.", "degrees", True, None),
    "longitude": ("number", "Market longitude, WGS84.", "degrees", True, None),
    "category": ("string", "WFP commodity category.", None, False, None),
    "commodity": ("string", "Commodity name in English.", None, False, None),
    "unit": ("enum", "Unit the price refers to.", None, False, ["KG", "L"]),
    "priceflag": ("enum", "Always 'actual'. Waga never forecasts or models prices.", None, False, ["actual"]),
    "pricetype": ("enum", "Always 'Retail' in v1.", None, False, ["Retail"]),
    "currency": ("enum", "ISO 4217 currency of the price column.", None, False, ["ETB"]),
    "price": ("number", "Weighted median accepted price. Empty when status is insufficient_data.", "ETB", True, None),
    "usdprice": ("number", "Price converted at the reference rate. Empty when price is empty.", "USD", True, None),
    "n_submissions": ("number", "Accepted submissions inside the window.", "count", False, None),
    "n_contributors": ("number", "Distinct contributors behind those submissions.", "count", False, None),
    "source_mix": ("string", "Pipe-separated source:count pairs, e.g. 'agent:6|user:1'.", None, True, None),
    "status": ("enum", "Whether the cell met the publication threshold.", None, False, ["published", "insufficient_data"]),
    "method_version": ("string", "Index method that produced this row. Frozen once published.", None, False, None),
    "snapshot_id": ("string", "Immutable snapshot this row belongs to.", None, False, None),
}


def build_codebook() -> dict[str, Any]:
    columns = []
    for name, tag in zip(PANEL_COLUMNS, PANEL_HXL):
        type_, description, unit, nullable, allowed = CODEBOOK_DESCRIPTIONS[name]
        columns.append({
            "name": name,
            "type": type_,
            "unit": unit,
            "hxl_tag": tag,
            "description": description,
            "allowed_values": allowed,
            "nullable": nullable,
        })
    payload = {
        "dataset": "waga_addis_market_prices_panel",
        "method_version": INDEX_METHOD,
        "columns": columns,
    }
    return envelope(payload)


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------


def write_json(name: str, payload: Any) -> Path:
    path = OUT_DIR / name
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    row_count, published, checksum = write_panel_csv(OUT_DIR / "panel.csv")

    fixtures: dict[str, tuple[str, Any]] = {
        "GET /reference": ("reference.json", build_reference()),
        "GET /prices/current": ("prices-current.json", build_prices_current()),
        "GET /prices/series": ("prices-series.json", build_prices_series()),
        "GET /prices/series?market=*": (
            "prices-series-by-market.json", build_prices_series_by_market()
        ),
        "GET /coverage": ("coverage.json", build_coverage()),
        "GET /affordability": ("affordability.json", build_affordability()),
        "GET /heatmap": ("heatmap.json", build_heatmap()),
        "GET /alerts": ("alerts.json", build_alerts()),
        "GET /meb/food-line": ("meb-food-line.json", build_meb_food_line()),
        "POST /copilot/ask": ("copilot-ask.json", build_copilot()),
        "POST /impact": ("impact.json", build_impact()),
        "GET /business/cost-index": ("business-cost-index.json", build_cost_index()),
        "GET /business/sourcing": ("business-sourcing.json", build_sourcing()),
        "POST /business/benchmark": ("business-benchmark.json", build_benchmark()),
        "POST /business/ask": ("business-ask.json", build_business_ask()),
        "GET /research/snapshots": (
            "research-snapshots.json", build_snapshots(row_count, published, checksum)
        ),
        "GET /research/methodology": ("research-methodology.json", build_methodology()),
        "GET /research/codebook": ("research-codebook.json", build_codebook()),
    }

    manifest = {
        "generated_at": iso(GENERATED_AT),
        "seed": SEED,
        "snapshot_id": SNAPSHOT_ID,
        "contract": "docs/api-contracts-v1.md",
        "types": "contracts/types.ts",
        "endpoints": {},
    }

    for endpoint, (filename, payload) in fixtures.items():
        write_json(filename, payload)
        manifest["endpoints"][endpoint] = f"mock/{filename}"

    manifest["endpoints"]["GET /exports/panel.csv"] = "mock/panel.csv"
    write_json("index.json", manifest)

    expected, published_cells, insufficient = coverage_counts()
    cost_now, _ = basket_cost(TODAY)
    cost_prior, _ = basket_cost(TODAY - 30)

    print(f"Wrote {len(fixtures) + 2} files to {OUT_DIR}")
    print(f"  panel.csv        {row_count} rows, {published} published")
    print(f"  today coverage   {published_cells}/{expected} cells ({insufficient} insufficient)")
    print(f"  basket 30d ago   {cost_prior:,.2f} ETB")
    print(f"  basket now       {cost_now:,.2f} ETB  ({pct_change(cost_now, cost_prior)}%)")


if __name__ == "__main__":
    main()
