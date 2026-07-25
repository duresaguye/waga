# Data Products Research — What Each Customer Actually Needs

**Status:** R&D input for the v1 API contract.
**Product truth:** [`docs/WHAT_WE_ARE_BUILDING.md`](WHAT_WE_ARE_BUILDING.md)
**Resulting contract:** [`docs/api-contracts-v1.md`](api-contracts-v1.md)
**Mock data for frontend:** [`contracts/`](../contracts/README.md)

This document answers three questions for three customer segments:

1. What decision are they trying to make?
2. What data and indicators do they use for that decision **today**, and in what format?
3. What does Waga ship that plugs into that existing workflow?

The rule throughout: **do not invent a new indicator where a standard one already exists.**
Waga's differentiator is speed, market-level granularity, and an audit trail — not novel maths.
Where we do add an indicator, we say plainly how it differs from the standard and when it is
not yet comparable.

---

## Segment 1 — Humanitarian NGOs (the beachhead)

### The decision

> "How much cash do we transfer per household this quarter, and is the market still functional
> enough to use cash instead of in-kind?"

Two sub-decisions, both recurring:

| Sub-decision | Owner inside the NGO | Cadence |
|---|---|---|
| Set / revise the Multi-Purpose Cash (MPC) transfer value | CVA or programme lead, endorsed by the Cash Working Group | Quarterly, or on trigger |
| Judge whether markets can absorb cash at all | Market assessment / M&E staff | Monthly, or on shock |

### What they use today

| Source | What it gives | Cadence | Format they consume |
|---|---|---|---|
| **JMMI** (REACH + Ethiopia Cash Working Group) | Cost of the MEB full basket and MEB food basket, per region and woreda; Market Functionality Score | Monthly | PDF factsheet + KoBo/Excel dataset; woreda choropleth maps |
| **ECWG MEB National Reference Guide (2025)** | The costing model itself, plus regional MPC transfer values | Annual, reviewed quarterly | PDF + an Excel "Adaptation Workbook" |
| **WFP VAM / DataBridges** | Price time series, ALPS/PEWI spike alerts, Market Functionality Index | Monthly | REST API (JSON/CSV) and DataViz dashboards |
| **HDX** | `wfp_food_prices_eth.csv`, HXL-tagged | Weekly file refresh, mostly monthly observations | CSV pulled into Excel, R, Python, Power BI |
| **FEWS NET** | Staple price and food-security outlooks | Monthly | PDF + CSV |
| **ESS CPI** | Official national/urban inflation | Monthly | PDF, aggregated |

### The three indicators that actually drive the decision

Reproduce these faithfully or NGOs will not adopt Waga.

**1. Cost of the MEB, and the MPC transfer value derived from it**

The ECWG method is subtraction, not modelling:

```
MPC transfer value = total MEB cost − average household income
```

The 2025 national reference guide models household sizes 5 and 6, and publishes the gap in both
ETB and USD at the UN preferential rate. It recommends reviewing transfer values **every three
months**, and treats **six consecutive months of price movement in one direction** as the trigger
for an actual revision.

The full MEB is 53 items across food, hygiene, energy, water and health — Waga covers 5 food
staples. So Waga does **not** output a transfer value on its own authority. It outputs the
**food-price component**, expressed so it can be dropped into the ECWG workbook: cost of the
tracked staples, percent change, and the resulting change in the food line of the MEB.

**2. Market Functionality Score (REACH / JMMI)** — five weighted dimensions:

| Dimension | Weight | Can Waga measure it from price submissions? |
|---|---|---|
| Availability | 30% | Partially — a cell going `insufficient_data` after being published is a weak availability signal |
| Accessibility | 25% | No — requires a vendor questionnaire |
| Resilience | 20% | No — requires stock-days and restock-days questions |
| Affordability | 15% | **Yes** — this is exactly what Waga computes |
| Infrastructure | 10% | No |

Honest position: Waga computes the **Affordability dimension only** and must label it as such.
Claiming a "Market Functionality Score" from price data alone is the kind of thing an
experienced CVA officer catches in the first meeting. The REACH affordability scoring compares
each item's median price against the national median in bands (below 50%, 50–75%, 75–90%,
110–125%, 125–150%, above 150%) — Waga can mirror that shape against a city median.

**3. ALPS — Alert for Price Spikes (WFP/CERDI)**

Regress the monthly price series on a trend and monthly dummies, take the residual, divide by the
standard deviation of residuals:

| Band | ALPS value |
|---|---|
| Normal | < 0.25 |
| Stress | 0.25 – 1 |
| Alert | 1 – 2 |
| Crisis | ≥ 2 |

This is the vocabulary NGOs already use in Ethiopia. **ALPS needs several years of monthly
observations** to estimate a stable trend, so Waga cannot produce a real ALPS at launch. See
"Waga Spike Score" below for the honest interim.

### What Waga ships to this segment

| Waga output | Maps to | Status at launch |
|---|---|---|
| Basket cost now / prior / % change, per item | JMMI MEB food basket line | Real |
| Food Affordability Score + band | JMMI MFS *Affordability dimension* | Real, scoped honestly |
| Market heat map, per market–commodity cell | Nothing equivalent exists at this granularity | Real, and the differentiator |
| Waga Spike Score (`waga-spike-v1`) | ALPS placeholder | Real, labelled as not-yet-ALPS |
| MEB food-line delta, exportable to the ECWG workbook | MPC transfer value input | Real |
| Impact calculation: households × gap × months | The pitch line, not a standard | Real |
| Humanitarian Copilot answer with cited figures | Replaces manual rebuilding of the above in Excel | Real, rule-based first |

### Where Waga genuinely beats what they have

1. **72 hours instead of a month.** JMMI is monthly and coverage varies by partner availability.
2. **Named markets.** "Ehil Berenda teff" not "Addis Ababa cereals".
3. **No imputation, ever.** JMMI guidance permits imputing up to 15% of MEB items. Waga's
   `AGENT.md` forbids imputation outright and returns `insufficient_data` instead. For a
   researcher or an auditor this is strictly better, and it is a claim we can defend.
4. **Audit chain.** Every published number traces to submissions, reviewers, and a method version.

### Where we must not overclaim

- Waga is Addis-only; JMMI is national across ~1,142 woredas. We are a supplement, not a replacement.
- 5 staples versus the 53-item MEB.
- No income data, so no standalone transfer value.
- No vendor questionnaire, so four of five MFS dimensions are out of reach.

---

## Segment 2 — Enterprises and new market entrants

### The decision

> "Should I open or expand here, what will my input costs be, and where do I buy?"

This segment is not one buyer. Three distinct ones, in descending order of how well Waga serves them:

| Buyer | Decision | How well 5 staples × 9 Addis markets serves them |
|---|---|---|
| **Food-buying operators** — restaurants, hotels, caterers, school feeding, hospitals, bakeries | Where to source, what to budget, when to lock a contract | **Strong.** This is literally their cost of goods. |
| **Wholesalers / distributors** | Where the price spread is, which market to arbitrage | **Strong.** Cross-market spread is the whole product. |
| **Site selection / new store** | Where to open | **Weak.** Needs footfall, rent, demographics, competitor density — Waga has none of it. |

**Decided: lead with cost and sourcing, not site selection.** Retail site selection needs
catchment modelling, points-of-interest data, traffic counts, and rent benchmarks. Waga has none
of these and buying them is a different company. The agreed framing is *"input-cost and sourcing
intelligence for businesses that buy food in Addis"*, which we can deliver on day one with zero
new collection.

Full write-up of this segment: [`docs/business-segment.md`](business-segment.md).

### What they use today

Almost nothing systematic, which is the opportunity:

| Source | Limitation |
|---|---|
| Phone calls to two or three brokers | No history, no comparison, negotiating position is guesswork |
| ESS CPI / NBE inflation releases | National and monthly — useless for "what will onions cost me next week" |
| Ethiopian Commodity Exchange | Only exchange-traded lots, not retail or local wholesale |
| Consultant feasibility studies | Thousands of dollars, one-off, stale in three months |
| Their own purchase records | The best data they have, but no external benchmark to compare against |

The gap is stark: a caterer with a fixed-price contract has no way to know whether their supplier's
quote is 5% or 40% above the market, and no way to see a price rise coming.

### What Waga ships to this segment

| Output | Definition | Why it matters |
|---|---|---|
| **Input Cost Index** | Weighted cost of a user-defined commodity mix, indexed to 100 at a base date | Drop-in replacement for "gut feel" in a budget model |
| **Sourcing spread** | `(max_market_price − min_market_price) / min_market_price` per commodity | Direct, actionable: buy teff at Ehil Berenda, not Piazza |
| **Best sourcing market** | Lowest published cell for each commodity, with the supporting count | The single most useful line on the page |
| **Volatility (30d)** | Coefficient of variation of the city daily series | Distinguishes "expensive" from "unpredictable" — different responses |
| **Planning band** | Median ± 1.28σ, an 80% band for next-period cost | Turns a price feed into a budget number |
| **Benchmark check** | User enters their supplier quote → percentile against the market | Converts data into leverage in a negotiation |
| **Decision layer** | Verdict, confidence, and the drivers behind it | The "AI layer" — see below |

### What the AI decision layer should and should not do

Same discipline as the humanitarian copilot: **the model narrates and recommends, it never
produces a number.** Every figure in the answer is a lookup against a published index cell, and
the response carries the citations. A model that invents an onion price destroys the product.

Concretely the decision layer answers questions like:

- "I need 400kg of teff a month for a restaurant. What should I budget and where do I buy?"
- "My supplier quoted 130 birr/kg for teff. Is that fair?"
- "Is now a bad time to sign a six-month fixed-price contract on cooking oil?"

And returns: a verdict, a number range traced to specific cells, the drivers, and an explicit
confidence that drops when coverage is thin.

### Honest limits

- Retail prices, not wholesale contract prices. Useful as a benchmark and a trend, not as a quote.
- 5 commodities. A restaurant buys a hundred things.
- Addis only.
- No rent, footfall, demographic, or competitor data — so no site selection.

---

## Segment 3 — Researchers and universities

### The decision

> "Can I cite this in a paper, and will a replication package built on it still work in three years?"

Researchers are the least demanding on *features* and the most demanding on *discipline*. They do
not want a dashboard. They want a stable file and a methodology document.

### What they use today

| Source | Why it is used | Why it frustrates them |
|---|---|---|
| WFP food prices on HDX | Free, long series, HXL-tagged, tidy long format | Monthly, coarse geography, gaps |
| ESS CPI | Official | Aggregated, no market detail, revisions poorly documented |
| JMMI datasets | Woreda-level | Imputed values are not always distinguishable from observed ones |
| FAO GIEWS, World Bank RTP | Cross-country comparison | Modelled, so unusable as a ground-truth series |
| Their own enumerator surveys | Exactly what they need | Expensive, small, one-off |

### What a citable dataset must have

Economics journals now enforce this — AEA, the Econometric Society, and most field journals
require a Data Availability Statement, a persistent identifier, and a formal data citation for
every dataset used, including ones the authors did not collect. That gives Waga a precise,
non-negotiable checklist:

| Requirement | What Waga must ship |
|---|---|
| Persistent identifier | An immutable, versioned snapshot ID per extract, resolvable forever |
| Data citation string | Pre-formatted, copy-pasteable, on the download page |
| Licence | Explicit and machine-readable. CC-BY-4.0 for the public tier |
| Codebook | Every column: name, type, unit, allowed values, definition |
| Methodology version | `method_version` on every row, with a changelog of what changed and when |
| Provenance per observation | Supporting count, contributor count, source composition, review status |
| Explicit missingness | `insufficient_data` rows present, never silently dropped or filled |
| Reproducibility | Re-requesting a snapshot ID returns byte-identical data |
| Access conditions | Stated cost and time to obtain — required in a Data Availability Statement |

Point 7 is where Waga has a real edge. The no-imputation rule in `AGENT.md` is not just internal
hygiene — it is a selling point to exactly this audience, because it means a researcher can
distinguish "the price was missing" from "the price was estimated" without reading a methods annex.

Point 8 is the one most likely to be quietly broken. Snapshot reproducibility means late-arriving
accepted submissions must **not** retroactively alter a published snapshot. They produce a new
snapshot. The append-only rules already in `AGENT.md` make this achievable; it needs to be an
explicit test.

### Column layout

Match WFP's HDX layout so existing scripts work with a column rename at most, then append Waga's
provenance columns:

```
date, admin1, admin2, market, latitude, longitude, category, commodity,
unit, priceflag, pricetype, currency, price, usdprice,
n_submissions, n_contributors, source_mix, status, method_version, snapshot_id
```

Row 2 carries HXL hashtags (`#date`, `#adm1+name`, `#loc+market+name`, `#item+name`, `#value`, …)
so the file drops straight into HDX tooling and Power BI without transformation.

### What Waga ships to this segment

- Tidy long panel, market × commodity × day, as CSV and Parquet
- HXL header row
- Snapshot IDs with a resolvable citation
- A machine-readable methodology endpoint, versioned
- A codebook generated from the same source as the API schema, so they cannot drift

---

## Cross-cutting design decisions

These fall out of the research and apply to every endpoint.

**1. Provenance travels with the data, always.** Every cell in every response carries
`status`, `n_submissions`, `n_contributors`, `source_mix`, `method_version`, `window`. An NGO
needs it to defend a transfer value; a researcher needs it to cite; a business needs it to know
how much to trust a sourcing recommendation. One envelope serves all three.

**2. `insufficient_data` is a first-class state, not an error.** It appears in responses with a
null value and a reason. Frontend must render it as an explicit empty state, never as zero and
never as a gap in a line chart.

**3. One index, three presentations.** The three segments are not three products. They are three
framings of the same market–commodity cells:

| | NGO | Business | Researcher |
|---|---|---|---|
| Unit of interest | Household basket | Input cost | Observation |
| Time framing | Month over month | Next quarter's budget | Full history |
| Wants | A recommendation | A verdict | A file |
| Tolerance for a model in the loop | Medium, if cited | High | Zero |

**4. The AI layer cites or it does not ship.** Rule-based first. Every number in an AI response
resolves to a published cell. If the underlying cells are `insufficient_data`, the answer says so
and lowers its confidence rather than guessing.

**5. Method versions are frozen and additive.** `waga-index-v1` never changes behaviour. A change
means `v2`, and old snapshots keep resolving against `v1`.

---

## Indicator definitions introduced by Waga

Everything below is new and therefore needs to be defined precisely and defended.

### `waga-index-v1` — market–commodity cell price

Already specified in `plan.md`: 72-hour rolling window, weighted median, publish at ≥3 accepted
submissions, otherwise `insufficient_data`. Source weights agent 2.0, user 1.0, scraped 0.5,
seed 0.5; recency weight rising linearly from 0.5 to 1.0 across the window.

### `waga-affordability-v1` — Food Affordability Score

```
change_pct = (basket_cost_now − basket_cost_prior_30d) / basket_cost_prior_30d × 100
score      = clamp(0, 100, 100 − 5 × change_pct)
```

| Band | change_pct |
|---|---|
| Stable | < 3% |
| Watch | 3% – 8% |
| Tightening | 8% – 15% |
| Severe | ≥ 15% |

Deliberately simple and fully documented, per the product rule "no black box". A 20% rise scores
0. The basket is only priced when **all five commodities** have a published city price; otherwise
the response returns `insufficient_data` with the list of missing commodities. No partial baskets,
because a partial basket that looks cheaper is worse than no number.

### `waga-spike-v1` — Spike Score (interim ALPS)

ALPS needs years of monthly data. Until then, keep ALPS's *structure* — detrend, then score the
residual — but run it on a 30-day daily window:

```
fit an OLS trend over the trailing 30 days of published prices for the cell
expected_t = trend value at t
residual_t = price_t − expected_t
sigma      = standard deviation of residuals across the window
spike      = residual_today / sigma
deviation  = (price_today − expected_today) / expected_today × 100
```

**Detrending is not optional.** The first version of this scored the residual against a trailing
*median* instead of a trend, and on a steadily rising series it flagged 33 of 36 cells, including
"crisis" on a 4.8% move. A rising market is not a spike. This is exactly why ALPS regresses on a
trend before taking the residual.

The band is the **weaker** of two signals:

| Band | spike (z) | AND deviation from trend |
|---|---|---|
| Normal | < 1.0 | < 2% |
| Stress | 1.0 – 2.0 | 2% – 5% |
| Alert | 2.0 – 3.0 | 5% – 10% |
| Crisis | ≥ 3.0 | ≥ 10% |

Requiring both matters. A cell with a very tight price history posts a large z-score on a 2% move —
statistically unusual, economically trivial. Publishing that as an "alert" is how a monitoring
product loses its audience in the first month. Taking the minimum of the two bands means an alert
needs to be both unusual and material.

Band names intentionally mirror ALPS so the output slots into existing NGO vocabulary. The API
must carry `"alps_comparable": false` until at least 24 monthly observations exist for that cell,
at which point real ALPS replaces this as `waga-spike-v2`. Never present this as ALPS.

### `waga-heat-v1` — market heat

Per cell: `pct_change_7d`. Per market: the mean of published cell changes, weighted by that cell's
supporting submission count. Markets with fewer than two published cells are reported as
`insufficient_data` rather than given a misleading heat value.

### `waga-cost-index-v1` — business input cost index

```
index_t = 100 × Σ(qty_i × price_i,t) / Σ(qty_i × price_i,base)
```

Quantities are supplied by the caller, so the index is that customer's actual basket. Base date
defaults to the earliest date with full coverage of the requested commodities.

---

## Sources

- REACH / IMPACT Initiatives, *Global Guidance Note: Joint Market Monitoring Initiative*, V1 2025 — MFS dimensions and weights, aggregation and imputation rules
- REACH Ethiopia JMMI factsheets, 2025 — MEB full and food basket costs, regional breakdown, monthly cadence
- Ethiopia Cash Working Group, *MEB National Reference Guide*, June 2025 — MPC transfer value method, review triggers, household sizes
- WFP VAM / CERDI, *Calculation and Use of the Alert for Price Spikes (ALPS) Indicator* — ALPS formula and thresholds
- WFP, *Market Functionality Index* technical and practical guidance — 9-dimension and reduced 4-dimension MFI, 0–10 scale
- WFP DataBridges API — ALPS/PEWI endpoint, `pricetype` and `priceflag` vocabularies
- HDX, WFP food prices country datasets — canonical CSV column layout and HXL tags
- AEA and Econometric Society data and code availability policies — Data Availability Statement, DOI, data citation, licensing requirements
