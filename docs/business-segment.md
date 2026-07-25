# Business Segment — Sourcing & Input Cost Intelligence

**Decision made:** Waga's enterprise product is **sourcing and input-cost intelligence for
businesses that buy food in Addis Ababa.** Not site selection. Not "where should I open a shop".

**Research behind it:** [`docs/data-products-research.md`](data-products-research.md)
**Endpoints:** `/business/*` in [`docs/api-contracts-v1.md`](api-contracts-v1.md)
**Mock data:** `contracts/mock/business-*.json`

This is the **second** segment. NGOs remain the beachhead per
[`docs/WHAT_WE_ARE_BUILDING.md`](WHAT_WE_ARE_BUILDING.md). Nothing here should delay the NGO demo.

---

## 1. Why sourcing and not site selection

The instinct is "help people decide where to open a business". We should not build that, and the
reason is simple: we have none of the data it needs.

| Site selection needs | Do we have it? |
|---|---|
| Catchment population and income | No |
| Footfall and traffic counts | No |
| Rent and lease benchmarks | No |
| Competitor locations and density | No |
| Points of interest, transport, road network | No |
| Consumer segmentation | No |

Site selection is gravity models and geospatial catchment analysis over demographic and
points-of-interest data. Buying that data and building that model is a different company. A
"decision layer" that recommends where to open a shop using only staple food prices would be
guessing with a confident voice, which is the one thing this product must never do.

Now the other column:

| Sourcing and input cost needs | Do we have it? |
|---|---|
| Current price per commodity per named market | **Yes** — this is the index |
| Price spread across markets | **Yes** — derived from the same cells |
| Historical series for trend and volatility | **Yes** — accumulating daily |
| Supporting counts, so buyers know what to trust | **Yes** — provenance is on every cell |
| A benchmark to check a supplier quote against | **Yes** — the city median |

Everything the sourcing product needs is already the thing we are building for NGOs. It is the
same index, presented as cost rather than as a household basket. **Zero new collection.**

---

## 2. Who actually buys this

Three buyer types, all of whom already spend real money on food inputs every month.

| Buyer | Examples | Monthly staple spend | What they want |
|---|---|---|---|
| **Food-buying operators** | Restaurants, hotels, cafés, bakeries, caterers, school feeding, hospitals, university canteens | Tens of thousands to millions of birr | Budget certainty and a cheaper supplier |
| **Wholesalers and distributors** | Grain traders, FMCG distributors, cooperative unions | Large | Where the spread is; when to move stock |
| **Processors** | Injera producers, flour mills, edible-oil packers | Large | Input cost trend; when to hedge or pre-buy |

The sharpest wedge is the mid-size operator: a restaurant or caterer buying a few hundred kilos of
teff a month. Large enough that a 15% price difference is real money, small enough that they have
no procurement analyst.

### The pain, stated plainly

A caterer signs a fixed-price catering contract. Their teff supplier quotes 130 birr a kilo. They
have no way to know whether that is fair. They call two other brokers, get two other numbers, and
pick one. Three weeks later teff has moved 18% and the contract is underwater.

They are not short of effort. They are short of a **benchmark**.

---

## 3. What they use today

| Source | What it gives | Why it fails them |
|---|---|---|
| Phone calls to two or three brokers | Today's quote from people who profit from the quote | No history, no independence, no negotiating leverage |
| ESS CPI and NBE inflation releases | National food inflation, monthly | Nowhere near granular enough for "what will onions cost me next week" |
| Ethiopian Commodity Exchange | Exchange-traded lot prices | Only exchange commodities and lot sizes; not local retail or small wholesale |
| Consultant feasibility study | A thorough one-off report | Thousands of dollars, and stale within a quarter |
| Their own purchase ledger | Their real costs over time | The best data they own — but no external benchmark to compare against |

The last row is the opportunity. These businesses already have half the picture. They know what
*they* paid. They have no idea what *the market* paid. Waga supplies the missing half.

---

## 4. What Waga ships

Six outputs. Every one is derived from published index cells — nothing modelled, nothing invented.

### 4.1 Input Cost Index — `GET /business/cost-index`

The customer supplies their own commodity mix and quantities, so the index tracks *their* actual
basket, not a generic one.

```
index_t = 100 × Σ(qty_i × price_i,t) / Σ(qty_i × price_i,base)
```

Returns the index, the monthly cost in birr, the 30-day change, the volatility, and a planning
band. From the current fixtures, for a restaurant buying 400kg teff, 120kg wheat and 60L oil:

| | |
|---|---|
| Index today | **130.3** (base 100 on 2026-04-27) |
| Monthly cost now | 65,998 ETB |
| Change, 30 days | +19.0% |
| Volatility, 30 days | 5.0% |
| Planning band, 80% | 56,065 – 63,696 ETB |

The planning band is median ± 1.28σ. **Label it a band, never a forecast.** It answers "what
should I put in the budget", which is a different and more honest question than "what will the
price be".

### 4.2 Sourcing spread — `GET /business/sourcing`

Per commodity: the city median, the cheapest and dearest published market, the spread, and the
per-unit saving against the median. Current fixtures:

| Commodity | City median | Cheapest | Dearest | Spread | Saving vs median |
|---|---|---|---|---|---|
| Teff | 113.63 /kg | Ehil Berenda 100.74 | Shola 122.04 | **21.1%** | 12.89 /kg |
| Wheat | 69.21 /kg | Merkato 62.42 | Piazza 73.58 | 17.9% | 6.79 /kg |
| Maize | 43.97 /kg | Merkato 40.83 | Kera 49.62 | **26.0%** | 3.14 /kg |
| Onion | 56.51 /kg | Ehil Berenda 53.58 | Shola 61.00 | 13.8% | 2.93 /kg |
| Cooking oil | 204.01 /L | Atikilt Tera 184.62 | Piazza 214.43 | 16.1% | 19.39 /L |

**Note what this table shows: no single market is cheapest for everything.** Ehil Berenda wins
grains and onion, Merkato wins wheat and maize, Atikilt Tera wins oil. That is precisely why the
product has value — if one market were always cheapest, everyone would already know and nobody
would pay. Spreads of 14% to 26% on staples are the entire commercial case in one table.

### 4.3 Quote benchmark — `POST /business/benchmark`

The customer types in what their supplier quoted. We tell them where it sits.

> Quote: 130.00 ETB/kg teff.
> *This quote is 14.4% above the Addis median and higher than 100% of prices recorded in the last
> 30 days. Ehil Berenda published 100.74 ETB/kg today.*

Verdicts: `below_market`, `at_market`, `above_market`, `far_above_market`.

This is the single highest-value feature in the segment, because it converts data into
**leverage**. A buyer who can say "I know the Addis median is 113" negotiates differently from one
who cannot. It is also the cheapest feature to build — it is one median and one subtraction.

### 4.4 Volatility

Coefficient of variation of the city daily series over 30 days. It separates two situations that
look identical on a price tag and demand opposite responses:

- **Expensive but stable** (maize, 2.9%) → safe to lock a longer contract
- **Volatile** (onion, 10.0%) → buy short, keep flexibility, do not commit

### 4.5 Alerts

The same `waga-spike-v1` detector the NGO product uses, read commercially. An NGO sees "onion is
spiking at Atikilt Tera, families are under pressure". A distributor sees the same cell and reads
an arbitrage window. One computation, two audiences.

### 4.6 The decision layer — `POST /business/ask`

This is the "AI layer". Its job is to **narrate and recommend**. It never produces a number.

Every figure in an answer is a lookup against a published index cell and appears in `citations`.
A response with an empty `citations` array is a bug, not a degraded answer. A model that invents an
onion price ends this product.

**Question types it must handle:**

| Question | Draws on |
|---|---|
| "I need 400kg of teff a month. What should I budget and where do I buy?" | cost-index, sourcing |
| "My supplier quoted 130 for teff. Is that fair?" | benchmark |
| "Should I sign a six-month fixed price on cooking oil?" | volatility, trend, alerts |
| "What is driving my costs up this month?" | cost-index item shares |
| "Which of my inputs is riskiest right now?" | volatility, alerts |

**Worked example from the current fixtures:**

> Budget 40,296–47,725 ETB a month for 400kg of teff at current prices. Buy at Ehil Berenda, where
> teff published at 100.74 ETB/kg today against a city median of 113.63 — about 5,156 ETB a month
> cheaper. Teff has risen 18.0% in 30 days and 30-day volatility is 4.9%, so this is not a good
> week to lock a six-month fixed price.

Four numbers, four citations, one clear action. That is the product.

**Confidence must move with coverage.** When the underlying cells are thin, the answer says so and
lowers its confidence rather than guessing. Cooking oil publishes in only 3 of 9 markets in the
current fixtures — an oil recommendation must carry that caveat visibly.

---

## 5. Honest limits — put these in the UI, not the footnotes

1. **Retail prices, not contract prices.** Useful as an independent benchmark and a trend. It is
   not a quote and not a wholesale contract rate.
2. **Five commodities.** A restaurant buys a hundred things. We cover the staples that usually
   dominate the bill, and nothing else.
3. **Addis Ababa only.**
4. **72-hour window.** Fast by the standards of this market, but not a live tick feed.
5. **Coverage varies.** Some cells are `insufficient_data`. Show it; never fill it in.
6. **No site selection, no demand estimation, no competitor data.** If a customer asks, say no
   clearly. Saying no to the wrong question is how we stay credible on the right one.

---

## 6. How they would pay

Not a plan, just the shape. The NGO tiers in `docs/business-model-early.md` do not transfer
directly — a restaurant will not pay $500 a month, and a distributor might pay more.

| Tier | Who | Rough shape | Includes |
|---|---|---|---|
| **Free** | Anyone | 0 | Public price lookup, city medians |
| **Buyer** | Single-site operators | Low monthly, ETB-priced | Cost index for their basket, sourcing table, quote benchmark, alerts |
| **Trade** | Distributors, processors, multi-site | Higher monthly | The above plus full history, CSV export, API |

Two things to note. **Price in birr**, because this segment budgets in birr and a dollar price
reads as "not for us". And the free tier matters more here than for NGOs — a buyer who checks the
teff median for free three times is most of the way to paying.

---

## 7. Build order

Nothing here starts before the NGO demo works end to end. When it does, the order is cheapest
first, and all four already have frozen contracts and mock fixtures.

| # | Endpoint | Effort | Why this order |
|---|---|---|---|
| 1 | `POST /business/benchmark` | Trivial — one median, one subtraction | Highest value per line of code; strongest standalone demo |
| 2 | `GET /business/sourcing` | Small — min, max, median over existing cells | The spread table is the commercial argument |
| 3 | `GET /business/cost-index` | Medium — needs the series and a base date | Turns a price feed into a budget number |
| 4 | `POST /business/ask` | Medium — rules first, LLM narration optional | Only worth building once 1–3 return real data |

All four read from `index_values`. **No new tables, no new collection, no new agents.** This
segment is a presentation layer over the index that already has to exist for NGOs — which is
exactly why it is worth doing, and exactly why it must not come first.
