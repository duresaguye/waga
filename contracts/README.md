# Frontend Contract & Mock Data

The frontend does not wait for the backend. Build against these fixtures now; swap the fetch layer
for real HTTP when Track B ships. The shapes are identical, so nothing else changes.

| File | What it is |
|---|---|
| `types.ts` | TypeScript types for every v1 read endpoint. Copy into the frontend app. |
| `mock/index.json` | Manifest: endpoint → fixture file. Use it to build the mock client. |
| `mock/*.json` | One realistic response per endpoint. |
| `mock/panel.csv` | 4,050-row research panel, WFP HDX column layout with an HXL header row. |
| `generate_mock.py` | Regenerates everything deterministically. |

**Contract:** [`docs/api-contracts-v1.md`](../docs/api-contracts-v1.md)
**Why these shapes:** [`docs/data-products-research.md`](../docs/data-products-research.md)

## Regenerate

```bash
python contracts/generate_mock.py
```

Stdlib only, no dependencies. The seed is fixed, so output is byte-stable and diffs stay
reviewable. Change the world at the top of the file (markets, price paths, dead cells, spikes)
and re-run.

## What the fixtures contain

A synthetic but plausible 90 days of Addis Ababa prices, ending 2026-07-25, across 9 markets and
5 commodities.

| | |
|---|---|
| Basket 30 days ago | 4,142.35 ETB |
| Basket now | 4,923.64 ETB (**+18.9%**, band `Severe`) |
| Coverage today | 36 of 45 cells published, 9 `insufficient_data` |
| Panel | 4,050 rows, 3,754 published |
| Alerts | 4, spanning `stress`, `alert` and `crisis` |
| Cheapest market | Varies by commodity — Ehil Berenda, Merkato and Atikilt Tera each win items |

That basket movement is deliberately close to the 4,100 → 4,850 demo story in
`docs/WHAT_WE_ARE_BUILDING.md`, so the UI you build against mocks tells the same story on stage.

## Edge cases baked in — please build for these

The fixtures are not a happy path. They contain the states that break naive UIs.

**1. Thin coverage.** Cooking oil is published in only 3 of 9 markets today. Any per-market grid
must handle a mostly-empty column.

**2. Permanently missing cells.** `kera × cooking_oil`, `akaki × teff_mixed`, `asko × onion`,
`piazza × maize` and `merkato × cooking_oil` are `insufficient_data` today. Render an explicit
empty state. Never `0`, never `—` without explanation, never omit the row.

**3. Gaps inside time series.** Roughly 7% of historical cell-days are `insufficient_data` with
`value: null`. **Break the line, do not interpolate.** Not imputing is a product promise we sell
to researchers, and a chart that visually bridges a gap breaks it.

**4. A market that cannot be scored.** A market with fewer than two published cells returns
`status: "insufficient_data"` and `heat: null` on the heat map. It needs a distinct pin style.

**5. Long text.** Copilot answers run to several sentences and Amharic market names are in every
reference row. Do not size containers to the English strings.

## Building the mock client

Read `mock/index.json`, map endpoint → file, and keep the same call signature you will use for
real HTTP so the swap is a one-line change:

```ts
import type { AffordabilityResponse } from "./types";

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

export async function getAffordability(): Promise<AffordabilityResponse> {
  if (USE_MOCKS) {
    return (await import("./mock/affordability.json")).default as AffordabilityResponse;
  }
  const response = await fetch("/api/v1/affordability");
  if (!response.ok) throw new Error(`affordability: ${response.status}`);
  return response.json();
}
```

Fixtures are static, so query parameters are ignored. Filter client-side while mocking —
`prices-series-by-market.json` carries all 9 markets × 5 commodities so market and commodity
filters can be built and tested for real.

## Suggested build order

Mirrors the Track B order in `docs/api-contracts-v1.md`, so the frontend and backend converge on
the same endpoint at roughly the same time.

| # | Screen | Fixtures |
|---|---|---|
| 1 | Public price lookup | `reference`, `prices-current` |
| 2 | NGO dashboard header: basket, score, band | `affordability` |
| 3 | Basket trend chart | `prices-series` |
| 4 | Market heat map | `heatmap`, `reference` (coordinates) |
| 5 | Copilot panel and impact slider | `copilot-ask`, `impact` |
| 6 | Data quality panel | `coverage` |
| 7 | Alerts feed | `alerts` |
| 8 | Business cost and sourcing | `business-cost-index`, `business-sourcing`, `business-benchmark` |
| 9 | Research downloads | `research-snapshots`, `research-codebook`, `panel.csv` |

Screens 1 to 6 are the full demo story.

## Two rules that are not negotiable

**Always show provenance.** Every response carries `meta.coverage`. Put it on screen — a
persistent "36 of 45 market–commodity cells published in the last 72h" line is what separates
Waga from a chart anyone could fake. Cells also carry `n_submissions`, `n_contributors` and
`source_mix`; surface them on hover at minimum.

**Never render a number the API did not return.** No client-side gap filling, no averaging away
an `insufficient_data`, no rounding a `null` to zero. If the API says it does not know, the UI
says so too.
