# Frontend guide — Track B intelligence APIs

**Base URL (local):** `http://127.0.0.1:8000/api/v1`  
**Base URL (Render):** `https://waga-2h0w.onrender.com/api/v1`  
**Auth:** these read endpoints are **public** (no bearer token) for the NGO demo tier.  
**Frozen shapes:** also see [`api-contracts-v1.md`](api-contracts-v1.md) and [`contracts/`](../contracts/).

Every `200` response uses:

```json
{
  "meta": {
    "generated_at": "...Z",
    "method_version": "waga-index-v1",
    "city": "addis_ababa",
    "currency": "ETB",
    "window": { "start": "...", "end": "...", "hours": 72 },
    "coverage": {
      "cells_expected": 45,
      "cells_published": 12,
      "cells_insufficient": 33,
      "coverage_pct": 26.7
    },
    "licence_class": "commercial_permitted",
    "snapshot_id": "snap_..."
  },
  "data": {}
}
```

**UI rule:** `insufficient_data` is a valid state — show empty/gap, never invent `0`.

---

## How data appears

```text
Agent submits price (Telegram)
  → admin accepts
  → backend recomputes index cell (72h median, need ≥3 accepted)
  → these GET APIs read published cells
```

Until enough accepts exist, affordability/heatmap/copilot will often return `insufficient_data`. That is expected.

---

## Endpoints

### 1) Current prices — public lookup / map chips

`GET /prices/current`

| Query | Type | Default |
|---|---|---|
| `market` | repeatable string | all Phase-1 markets |
| `commodity` | repeatable string | all 5 staples |
| `include_insufficient` | bool | `true` |

**Use `data.cells[]`** for market×commodity cards.  
**Use `data.city_prices[]`** for Addis city median per commodity (basket input).

Example:

```http
GET /api/v1/prices/current?commodity=teff_mixed&commodity=onion
```

### 2) Price series — charts

`GET /prices/series`

| Query | Notes |
|---|---|
| `commodity` | repeatable; default `teff_mixed` |
| `market` | omit = **city aggregate** (`market_code: null`) |
| `from` / `to` | `YYYY-MM-DD` |
| `interval` | `day` (v1) |

Break the chart line when `status === "insufficient_data"` (`value` is `null`).

### 3) Affordability — NGO headline

`GET /affordability`

| Query | Default |
|---|---|
| `basket` | `phase1_staple5` |
| `household_size` | `5` |
| `compare_days` | `30` |

Basket quantities (household size 5): teff 25kg, wheat 10kg, maize 10kg, onion 6kg, oil 3L.

If any staple city price is missing → `data.status = "insufficient_data"`, `cost_now = null`, see `missing_commodities`.

Show: `cost_now`, `change_pct`, `band`, and top `contribution_to_change_pct` item.

### 4) Heat map

`GET /heatmap`

| Query | Default |
|---|---|
| `metric` | `pct_change_7d` or `pct_change_30d` |
| `commodity` | optional filter |

Bands: `cool` | `stable` | `warm` | `hot` | `critical`  
Color by `markets[].heat` / `markets[].band`.  
`latitude` / `longitude` may be `null` until seeded — fall back to list/cards.

### 5) Copilot

`POST /copilot/ask`

```json
{
  "question": "How should we adjust cash assistance for Addis this month?",
  "household_count": 50000,
  "language": "en"
}
```

Always render `citations` (never hide). Show `mode` (`rule_based`).  
Use `recommendation.band_low_pct` / `band_high_pct` for the transfer suggestion.  
Use `impact` for the “cost of doing nothing” callout.

### 6) Impact only

`POST /impact`

```json
{ "household_count": 50000, "compare_days": 30 }
```

---

## Frozen codes

**Markets:** `merkato`, `shola`, `ehil_berenda`, `atikilt_tera`, `piazza`, `saris`, `akaki`, `asko`, `kera`  
**Commodities:** `teff_mixed`, `wheat`, `maize`, `onion`, `cooking_oil`  
**City:** `addis_ababa`

(`other` is intake-only; not in city aggregates.)

---

## Suggested screens

| Screen | Calls |
|---|---|
| Public price lookup | `GET /prices/current` |
| Charts | `GET /prices/series` |
| NGO home / score | `GET /affordability` |
| Map / market pressure | `GET /heatmap` |
| Decision assistant | `POST /copilot/ask` |

---

## Admin (separate — Track A)

Not Track B. Frontend admin teammate uses JWT +:

- `POST /auth/login`
- `GET/POST /admin/agent-applications/*`
- `GET/POST /admin/reviews/*`
- `POST /admin/agent-invites`

---

## Local demo tip

1. Seed: `uv run waga-seed-phase1`  
2. Activate agent + submit ≥3 accepted prices for the same market+commodity  
3. Then `GET /prices/current` should show `published` for that cell  

Mocks (UI before live data): `contracts/mock/*.json`
