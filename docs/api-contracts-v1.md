# API Contracts v1 — Read Surface

**Why this file exists:** the frontend starts before Track B finishes. This is the frozen
contract both sides build against. Frontend codes to these shapes using the fixtures in
[`contracts/`](../contracts/README.md); Track B implements them for real. Neither waits for the other.

**Research behind these shapes:** [`docs/data-products-research.md`](data-products-research.md)
**Ownership:** all of this is Track B (`docs/WORK_SPLIT.md`). Track A owns writes; this file is reads only.

Rules for changing this file:

1. Additive changes are fine. Removing or retyping a field is a breaking change — announce it.
2. Every response uses the standard envelope.
3. `insufficient_data` is a state, not an error. Never a 404, never a zero.
4. No endpoint returns a number that cannot be traced to a published index cell.

---

## Conventions

| Thing | Rule |
|---|---|
| Base path | `/api/v1` |
| Timestamps | ISO 8601, UTC, `Z` suffix |
| Dates | `YYYY-MM-DD` |
| Money | JSON number, 2 decimal places, `currency` always stated |
| Codes | `snake_case`, frozen in `telegram_bot/reference.py` |
| Missing value | `null` plus a `status` field explaining why. Never `0`, never omitted |
| Unknown query param | Ignored, not an error |
| Auth | Public tier unauthenticated; `full` and `research` tiers need a bearer token |

### Frozen codes

Markets: `merkato`, `shola`, `ehil_berenda`, `atikilt_tera`, `piazza`, `saris`, `akaki`, `asko`, `kera`, `other`
Commodities: `teff_mixed`, `wheat`, `maize`, `onion`, `cooking_oil`
Units: `kg` for foods, `liter` for cooking oil
City: `addis_ababa`

---

## Standard envelope

Every `200` response, without exception:

```json
{
  "meta": {
    "generated_at": "2026-07-25T06:00:00Z",
    "method_version": "waga-index-v1",
    "city": "addis_ababa",
    "currency": "ETB",
    "window": { "start": "2026-07-22T06:00:00Z", "end": "2026-07-25T06:00:00Z", "hours": 72 },
    "coverage": {
      "cells_expected": 45,
      "cells_published": 38,
      "cells_insufficient": 7,
      "coverage_pct": 84.4
    },
    "licence_class": "commercial_permitted",
    "snapshot_id": "snap_2026-07-25T06_v1"
  },
  "data": {}
}
```

`coverage` is the honesty signal the whole product rests on. Show it in the UI — a persistent
"38 of 45 market–commodity cells published in the last 72h" line builds more trust than any chart.

### The price cell

The atom everything else is built from. Same shape everywhere it appears.

```json
{
  "market_code": "ehil_berenda",
  "market_name_en": "Ehil Berenda",
  "market_name_am": "እህል በረንዳ",
  "commodity_code": "teff_mixed",
  "commodity_name_en": "Teff (mixed)",
  "commodity_name_am": "ጤፍ (ድብልቅ)",
  "unit": "kg",
  "currency": "ETB",
  "status": "published",
  "value": 110.5,
  "n_submissions": 7,
  "n_contributors": 4,
  "source_mix": { "agent": 6, "user": 1 },
  "window_start": "2026-07-22T06:00:00Z",
  "window_end": "2026-07-25T06:00:00Z",
  "computed_at": "2026-07-25T06:00:00Z",
  "method_version": "waga-index-v1",
  "insufficient_reason": null
}
```

When `status` is `"insufficient_data"`: `value` is `null`, `n_submissions` is the count that *did*
arrive (may be 0, 1 or 2), and `insufficient_reason` is one of `below_threshold`, `no_submissions`,
`all_flagged`.

### Errors

```json
{ "error": { "code": "unknown_market", "message": "No market with code 'bole'", "field": "market" } }
```

Codes: `unknown_market`, `unknown_commodity`, `unknown_basket`, `invalid_range`,
`range_too_large`, `unauthorized`, `tier_required`.

---

## Reference data

### `GET /reference`

Everything needed to build dropdowns and labels. Cache aggressively; changes rarely.

```json
{
  "meta": { "generated_at": "2026-07-25T06:00:00Z", "method_version": "waga-index-v1" },
  "data": {
    "city": { "code": "addis_ababa", "name_en": "Addis Ababa", "name_am": "አዲስ አበባ" },
    "markets": [
      {
        "code": "ehil_berenda",
        "name_en": "Ehil Berenda",
        "name_am": "እህል በረንዳ",
        "latitude": 9.0333,
        "longitude": 38.7389,
        "is_active": true
      }
    ],
    "commodities": [
      {
        "code": "teff_mixed",
        "name_en": "Teff (mixed)",
        "name_am": "ጤፍ (ድብልቅ)",
        "category": "cereals and tubers",
        "unit": "kg",
        "price_hint_low": 80,
        "price_hint_high": 160
      }
    ],
    "baskets": [
      {
        "code": "phase1_staple5",
        "name_en": "Addis staple basket (5 items)",
        "household_size": 5,
        "period_days": 30,
        "items": [
          { "commodity_code": "teff_mixed", "quantity": 25, "unit": "kg" },
          { "commodity_code": "wheat", "quantity": 10, "unit": "kg" },
          { "commodity_code": "maize", "quantity": 10, "unit": "kg" },
          { "commodity_code": "onion", "quantity": 6, "unit": "kg" },
          { "commodity_code": "cooking_oil", "quantity": 3, "unit": "liter" }
        ]
      }
    ]
  }
}
```

---

## Core price reads

### `GET /prices/current`

Query: `market` (repeatable, default all), `commodity` (repeatable, default all),
`include_insufficient` (default `true`).

```json
{
  "meta": {},
  "data": {
    "cells": [],
    "city_prices": [
      {
        "commodity_code": "teff_mixed",
        "unit": "kg",
        "status": "published",
        "value": 112.0,
        "markets_published": 8,
        "markets_expected": 9,
        "min": { "market_code": "ehil_berenda", "value": 104.5 },
        "max": { "market_code": "piazza", "value": 121.0 },
        "spread_pct": 15.8
      }
    ]
  }
}
```

`city_prices[].value` is the median of published market cells for that commodity. It is what the
public lookup page and the basket calculation both use.

### `GET /prices/series`

Query: `commodity` (repeatable), `market` (repeatable, omit for city-level), `from`, `to`,
`interval` (`day` | `week` | `month`, default `day`). Max range 366 days.

```json
{
  "meta": {},
  "data": {
    "interval": "day",
    "series": [
      {
        "commodity_code": "teff_mixed",
        "market_code": null,
        "unit": "kg",
        "points": [
          { "date": "2026-07-24", "value": 111.5, "status": "published", "n_submissions": 22 },
          { "date": "2026-07-25", "value": null, "status": "insufficient_data", "n_submissions": 1 }
        ]
      }
    ]
  }
}
```

`market_code: null` means the city aggregate. Points with `status: "insufficient_data"` are
**present in the array** — the frontend must break the line, not interpolate across them.

### `GET /coverage`

Powers the data-quality panel and tells operators where to send agents.

```json
{
  "meta": {},
  "data": {
    "matrix": [
      {
        "market_code": "ehil_berenda",
        "cells": [
          { "commodity_code": "teff_mixed", "status": "published", "n_submissions": 7, "hours_since_last": 4.2 }
        ]
      }
    ],
    "worst_covered": [
      { "market_code": "kera", "commodity_code": "cooking_oil", "hours_since_last": 96.0 }
    ]
  }
}
```

---

## NGO surface

### `GET /affordability`

Query: `basket` (default `phase1_staple5`), `household_size` (default 5),
`compare_days` (default 30).

The headline NGO number.

```json
{
  "meta": {},
  "data": {
    "basket_code": "phase1_staple5",
    "household_size": 5,
    "period_days": 30,
    "status": "published",
    "cost_now": 4850.0,
    "cost_prior": 4100.0,
    "prior_date": "2026-06-25",
    "change_abs": 750.0,
    "change_pct": 18.3,
    "score": 8.5,
    "band": "Severe",
    "method_version": "waga-affordability-v1",
    "items": [
      {
        "commodity_code": "teff_mixed",
        "quantity": 25,
        "unit": "kg",
        "unit_price_now": 112.0,
        "unit_price_prior": 95.0,
        "cost_now": 2800.0,
        "cost_prior": 2375.0,
        "change_pct": 17.9,
        "contribution_to_change_pct": 56.7,
        "status": "published"
      }
    ],
    "missing_commodities": []
  }
}
```

`contribution_to_change_pct` is what makes this actionable — it answers "teff is 57% of why the
basket moved", which is the sentence an NGO puts in its justification memo.

If any commodity lacks a published city price, the whole response returns
`status: "insufficient_data"`, `cost_now: null`, and lists the codes in `missing_commodities`.
No partial baskets.

### `GET /heatmap`

Query: `metric` (`pct_change_7d` default, or `pct_change_30d`), `commodity` (optional filter).

```json
{
  "meta": {},
  "data": {
    "metric": "pct_change_7d",
    "method_version": "waga-heat-v1",
    "markets": [
      {
        "market_code": "ehil_berenda",
        "market_name_en": "Ehil Berenda",
        "latitude": 9.0333,
        "longitude": 38.7389,
        "status": "published",
        "heat": 8.4,
        "band": "hot",
        "cells_published": 5,
        "cells_expected": 5,
        "cells": [
          { "commodity_code": "teff_mixed", "status": "published", "value": 110.5, "pct_change": 8.1, "band": "hot" }
        ]
      }
    ],
    "hottest_cell": { "market_code": "atikilt_tera", "commodity_code": "onion", "pct_change": 12.4 }
  }
}
```

Bands: `cool` (< −2%), `stable` (−2% to 2%), `warm` (2% to 5%), `hot` (5% to 10%), `critical` (≥ 10%).

### `GET /alerts`

Query: `min_band` (default `stress`).

```json
{
  "meta": {},
  "data": {
    "method_version": "waga-spike-v1",
    "alps_comparable": false,
    "alps_comparable_note": "Detrended residual z-score over a 30-day daily window, banded jointly with the percent deviation from trend. Same structure as WFP ALPS but daily rather than monthly. Real ALPS needs 24 monthly observations per cell.",
    "window_days": 30,
    "min_deviation_pct": 2.0,
    "z_thresholds": [1.0, 2.0, 3.0],
    "deviation_thresholds_pct": [2.0, 5.0, 10.0],
    "alerts": [
      {
        "market_code": "atikilt_tera",
        "commodity_code": "onion",
        "spike": 3.55,
        "band": "crisis",
        "value": 60.91,
        "expected": 51.93,
        "median_30d": 41.91,
        "pct_above_expected": 17.3,
        "first_detected_at": "2026-07-23T06:00:00Z",
        "consecutive_days": 3
      }
    ]
  }
}
```

`expected` is the detrended trend value; `pct_above_expected` is the deviation from it.
The band is the **weaker** of the z band and the deviation band — see `waga-spike-v1` in
`docs/data-products-research.md` for why both are required. `alps_comparable` must stay `false`
until the data supports a real ALPS. Do not remove the note.

### `GET /meb/food-line`

The bridge into the ECWG workbook. Waga owns the food-price delta; the NGO owns income and the
other 48 MEB items.

```json
{
  "meta": {},
  "data": {
    "household_size": 5,
    "waga_food_line_now": 4850.0,
    "waga_food_line_prior": 4100.0,
    "change_pct": 18.3,
    "coverage_note": "Waga prices 5 of the 53 ECWG MEB items. This is the tracked-staple line only.",
    "ecwg_reference": {
      "source": "ECWG MEB National Reference Guide, June 2025",
      "national_meb_full_etb": 17700.0,
      "national_meb_food_etb": 16135.0,
      "as_of": "2025-12-01",
      "review_cadence_months": 3,
      "revision_trigger": "Six consecutive months of price movement in one direction"
    },
    "consecutive_months_rising": 4,
    "revision_trigger_met": false
  }
}
```

`ecwg_reference` values are static published figures the NGO already knows, included so the UI can
show Waga's fast-moving number next to the slow official one. Keep them in config, not hardcoded
in a service, and label the `as_of` date honestly.

### `POST /copilot/ask`

```json
{ "question": "How should we adjust cash assistance for Addis this month?", "household_count": 50000, "language": "en" }
```

```json
{
  "meta": {},
  "data": {
    "answer": "The Addis staple basket rose from 4,100 to 4,850 ETB over the last 30 days, an increase of 18.3%. Teff accounts for 57% of that increase. If your transfer value was set against the June basket, it now covers about 85% of the same goods. A adjustment of 15–18% would restore purchasing power.",
    "recommendation": {
      "action": "increase_transfer_value",
      "band_low_pct": 15.0,
      "band_high_pct": 18.0,
      "confidence": "medium",
      "confidence_reason": "38 of 45 cells published; onion coverage thin at 3 of 9 markets"
    },
    "citations": [
      { "label": "Basket cost now", "value": 4850.0, "unit": "ETB", "source": "/affordability", "cell_refs": ["addis_ababa:phase1_staple5:2026-07-25"] }
    ],
    "impact": {
      "household_count": 50000,
      "gap_per_household_etb": 750.0,
      "monthly_total_etb": 37500000.0,
      "note": "Cost of leaving the transfer value unchanged for one month."
    },
    "mode": "rule_based"
  }
}
```

`citations` is mandatory and must be non-empty. A response with no citations is a bug, not a
degraded answer. `mode` is `rule_based` or `llm_assisted` — the UI should show which.

### `POST /impact`

```json
{ "household_count": 50000, "gap_per_household_etb": 750.0, "months": 3 }
```

Returns the same `impact` block as above. Split out so the dashboard can offer a slider without
re-running the copilot.

---

## Business surface

### `GET /business/cost-index`

Query: `items` as `commodity_code:quantity` pairs, repeatable. `base_date` optional.

```json
{
  "meta": {},
  "data": {
    "method_version": "waga-cost-index-v1",
    "base_date": "2026-04-26",
    "base_value": 100.0,
    "current_value": 124.6,
    "change_pct_30d": 9.2,
    "monthly_cost_now_etb": 52400.0,
    "monthly_cost_base_etb": 42055.0,
    "volatility_30d_pct": 6.8,
    "planning_band": { "low_etb": 49100.0, "high_etb": 57300.0, "confidence": 0.8 },
    "items": [
      { "commodity_code": "teff_mixed", "quantity": 400, "unit": "kg", "unit_price": 112.0, "cost_etb": 44800.0, "share_pct": 85.5, "status": "published" }
    ],
    "series": [{ "date": "2026-07-25", "value": 124.6, "status": "published" }]
  }
}
```

`planning_band` is median ± 1.28σ, an 80% band. It is the number a business actually puts in a
budget, so label it clearly as a band and not a forecast.

### `GET /business/sourcing`

Query: `commodity` (repeatable).

```json
{
  "meta": {},
  "data": {
    "commodities": [
      {
        "commodity_code": "teff_mixed",
        "unit": "kg",
        "city_median": 112.0,
        "cheapest": { "market_code": "ehil_berenda", "value": 104.5, "n_submissions": 7 },
        "dearest": { "market_code": "piazza", "value": 121.0, "n_submissions": 4 },
        "spread_pct": 15.8,
        "saving_per_unit_etb": 7.5,
        "volatility_30d_pct": 5.1,
        "markets": []
      }
    ]
  }
}
```

`saving_per_unit_etb` is city median minus cheapest — the concrete "buy here instead" number.

### `POST /business/benchmark`

Give a business leverage in a negotiation.

```json
{ "commodity_code": "teff_mixed", "quoted_price": 130.0, "unit": "kg" }
```

```json
{
  "meta": {},
  "data": {
    "commodity_code": "teff_mixed",
    "quoted_price": 130.0,
    "city_median": 112.0,
    "diff_pct": 16.1,
    "percentile": 94,
    "verdict": "above_market",
    "message": "This quote is 16% above the Addis median and higher than 94% of prices recorded in the last 30 days. Ehil Berenda published 104.50 ETB/kg today.",
    "cheapest_alternative": { "market_code": "ehil_berenda", "value": 104.5 }
  }
}
```

Verdicts: `below_market` (< −5%), `at_market` (−5% to 5%), `above_market` (5% to 20%),
`far_above_market` (≥ 20%).

### `POST /business/ask`

The decision layer. Same discipline as the copilot: cited numbers only.

```json
{ "question": "I need 400kg of teff a month for a restaurant in Piazza. What should I budget and where do I buy?", "language": "en" }
```

```json
{
  "meta": {},
  "data": {
    "answer": "Budget 44,800–48,200 ETB a month for 400kg of teff at current prices. Buy at Ehil Berenda, where teff published at 104.50 ETB/kg today against a city median of 112.00 — about 3,000 ETB a month cheaper than buying in Piazza. Teff has risen 17.9% in 30 days and volatility is elevated, so do not lock a six-month fixed price this week.",
    "verdict": { "action": "source_at_alternative_market", "confidence": "high", "confidence_reason": "Teff published in 8 of 9 markets over the last 72h" },
    "drivers": [
      { "label": "Teff 30-day change", "value": 17.9, "unit": "%", "direction": "up" }
    ],
    "citations": [
      { "label": "Ehil Berenda teff", "value": 104.5, "unit": "ETB/kg", "source": "/prices/current", "cell_refs": ["ehil_berenda:teff_mixed:2026-07-25"] }
    ],
    "mode": "rule_based"
  }
}
```

---

## Research surface

### `GET /research/snapshots`

```json
{
  "meta": {},
  "data": {
    "snapshots": [
      {
        "snapshot_id": "snap_2026-07-25T06_v1",
        "created_at": "2026-07-25T06:00:00Z",
        "method_version": "waga-index-v1",
        "temporal_coverage": { "start": "2026-04-26", "end": "2026-07-25" },
        "spatial_coverage": { "city": "addis_ababa", "markets": 9 },
        "commodities": 5,
        "row_count": 4050,
        "rows_published": 3402,
        "rows_insufficient": 648,
        "licence": "CC-BY-4.0",
        "checksum_sha256": "…",
        "citation": "Waga Intelligence (2026). Addis Ababa Market Price Index, snapshot snap_2026-07-25T06_v1. https://waga.et/data/snap_2026-07-25T06_v1",
        "download": { "csv": "/api/v1/exports/panel.csv?snapshot=snap_2026-07-25T06_v1", "parquet": "…" },
        "immutable": true
      }
    ]
  }
}
```

**Immutability is a hard requirement.** A late-arriving accepted submission creates a new snapshot;
it never mutates an existing one. Track B needs an explicit test for this.

### `GET /research/methodology` and `GET /research/codebook`

Machine-readable versions of the index method and the column dictionary, generated from the same
source as the API schema so the two cannot drift.

```json
{
  "meta": {},
  "data": {
    "method_version": "waga-index-v1",
    "effective_from": "2026-04-01",
    "window_hours": 72,
    "publish_threshold_submissions": 3,
    "aggregation": "weighted median",
    "source_weights": { "agent": 2.0, "user": 1.0, "scraped": 0.5, "seed": 0.5 },
    "recency_weight": "linear 0.5 → 1.0 across the window",
    "imputation": "none",
    "below_threshold_behaviour": "insufficient_data, value null",
    "changelog": [{ "version": "waga-index-v1", "date": "2026-04-01", "change": "Initial release." }]
  }
}
```

### `GET /exports/panel.csv`

Tidy long panel. First 14 columns match the WFP HDX layout exactly so existing scripts work
unchanged; the rest is Waga provenance. Row 2 is HXL tags.

```csv
date,admin1,admin2,market,latitude,longitude,category,commodity,unit,priceflag,pricetype,currency,price,usdprice,n_submissions,n_contributors,source_mix,status,method_version,snapshot_id
#date,#adm1+name,#adm2+name,#loc+market+name,#geo+lat,#geo+lon,#item+type,#item+name,#item+unit,#item+price+flag,#item+price+type,#currency,#value,#value+usd,#meta+count,#meta+contributors,#meta+sources,#status+code,#meta+method,#meta+snapshot
2026-07-25,Addis Ababa,Addis Ababa,Ehil Berenda,9.0333,38.7389,cereals and tubers,Teff (mixed),KG,actual,Retail,ETB,104.50,0.7464,7,4,agent:6|user:1,published,waga-index-v1,snap_2026-07-25T06_v1
2026-07-25,Addis Ababa,Addis Ababa,Kera,9.0000,38.7500,oil and fats,Cooking oil,L,actual,Retail,ETB,,,1,1,agent:1,insufficient_data,waga-index-v1,snap_2026-07-25T06_v1
```

`insufficient_data` rows stay in the file with an empty `price`. Dropping them would silently
misrepresent coverage, which is the exact failure mode we are selling against.

---

## Implementation order for Track B

Follows the demo story in `WHAT_WE_ARE_BUILDING.md`, cheapest useful thing first.

| # | Endpoint | Unblocks |
|---|---|---|
| 1 | `GET /reference` | Every dropdown in the UI |
| 2 | `GET /prices/current` | Public lookup, and the atom for everything else |
| 3 | `GET /prices/series` | All charts |
| 4 | `GET /affordability` | The headline NGO number |
| 5 | `GET /heatmap` | The demo's visual moment |
| 6 | `POST /copilot/ask` | The decision product |
| 7 | `GET /coverage`, `POST /impact` | Trust panel and the impact slider |
| 8 | `GET /alerts` | Proactive value |
| 9 | `GET /exports/panel.csv`, `/research/*` | Researcher tier |
| 10 | `/business/*` | Second segment |

Endpoints 1 through 7 cover the full demo. Everything after is expansion.
