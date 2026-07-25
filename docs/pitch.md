# Waga Intelligence — Investor Pitch

**AI-assisted food affordability monitoring for humanitarian and commercial decisions in Ethiopia.**

Supporting docs: [`business-model-early.md`](business-model-early.md) ·
[`data-products-research.md`](data-products-research.md) ·
[`business-segment.md`](business-segment.md) ·
[`WHAT_WE_ARE_BUILDING.md`](WHAT_WE_ARE_BUILDING.md)

> **How to read this.** Every externally sourced figure is cited in §19. Every projected figure is
> labelled as a model with its assumptions stated. Sections 1 and 2 are the only ones I could not
> write for you — they need your real team facts, and inventing them would be the fastest way to
> lose a room. They are marked `FILL IN` with guidance.

---

## 1. Who are you to address this problem

`FILL IN — do not skip, this is usually the first thing an investor decides on.`

The question behind the question is *"why won't a bigger team just do this?"* Answer it with
proximity, not credentials. The strongest version of this answer for Waga is some combination of:

- **You are from here.** You buy teff. You know what Ehil Berenda is and why it is different from
  Piazza. A team in Nairobi or Geneva does not.
- **You speak the languages the data is collected in.** Amharic and Afaan Oromo are not a
  localisation task for you, they are the default.
- **You can physically recruit and hold a market agent network.** This is the actual moat and it is
  a relationship business, not a software one.

Write two or three sentences. Name the people. Say what each one has done that is relevant.

## 2. What makes us qualified enough

`FILL IN.`

Cover four things, one line each:

| | What to state |
|---|---|
| **Technical** | What you have already shipped. Be specific — you have a working FastAPI backend, a Telegram intake bot with Amharic and Afaan Oromo speech-to-text wired in, an agent reputation system, and a reviewed-submission pipeline. That is not a slide deck, it is running code. |
| **Domain** | Any exposure to humanitarian work, cash programming, market monitoring, or the Cash Working Group. If you have none, say so and name the advisor you will get. |
| **Local** | Language, city knowledge, ability to onboard agents in person. |
| **Team completeness** | Who covers backend, frontend, data, and business development — and which seat is currently empty. Naming the gap builds more credibility than pretending there isn't one. |

If domain expertise is your weak spot, the honest and effective move is: *"we are not humanitarian
professionals, which is why the first thing we built was an audit trail and a rule that the system
never estimates a price it does not have."*

---

## 3. The problem — with a story

### The story

An NGO programme officer in Addis has to decide next quarter's cash transfer value for 50,000
households. The method the Ethiopia Cash Working Group prescribes is a subtraction: the cost of the
Minimum Expenditure Basket, minus average household income. Straightforward, except for one input.

The basket cost comes from the Joint Market Monitoring Initiative, which publishes **monthly**.
Enumerators visit markets, upload to KoBo, prices are cleaned and medians computed, and a factsheet
comes out weeks later. By the time she reads it, the number describes a market that no longer
exists. She knows this. So she calls two colleagues, checks a WhatsApp group, adds a margin she
cannot fully justify, and signs.

**In our Addis data, the five-staple basket moved from 4,142 to 4,924 birr in thirty days — 18.9%.**
If her transfer value was set against last month's basket and she is out by 781 birr per household,
across 50,000 households that is **39 million birr in one month**. Either families cannot buy what
the transfer was designed to buy, or scarce donor money is overspent. Both are failures, and
neither shows up until the post-distribution monitoring arrives, months later.

### Why we are part of the problem, not observers of it

We are the households in this story. When the birr was devalued in July 2024 and edible oil jumped
15–20%, we felt it in our own kitchens before any institution published a number about it. The
data that describes our cost of living is collected about us, published in English, aggregated to
the national level, and arrives too late to act on. We are building the tool we wanted to exist.

### The problem in one line

> **Ethiopia's food prices move weekly. The data that describes them moves monthly.**

---

## 4. The idea is not the moat

"A price index for Ethiopia" is not a novel idea. WFP, REACH, FEWS NET and the Ethiopian Statistics
Service all publish food prices. Anyone can say the words. So be honest about it and move the
conversation to where the difficulty actually is.

**The hard part is not the software. It is holding a network of people who reliably report honest
prices from named markets, week after week, without gaming it.** That requires local recruitment,
a reputation system with real consequences, human review, and a reason for agents to keep showing
up. We have built all four:

| | Status |
|---|---|
| Approved-agent onboarding with invite codes and an application flow | Shipped |
| Reputation scoring: points for accepted prices, penalties and bans for bad data | Shipped |
| Human review before any price enters the index | Shipped |
| Redemption path so agents earn something real | Shipped, payouts manual |
| Amharic and Afaan Oromo intake, including voice | Shipped |

A well-funded competitor can copy the dashboard in a fortnight. Copying a trusted agent network in
Merkato takes a year and someone who lives here.

---

## 5. Why now

Four things became true at once, and only recently.

**1. Prices are volatile again, after a false calm.** Ethiopia moved to a market-determined
exchange rate in July 2024; the birr fell 30% on day one and kept going, from 57 to roughly 125 per
dollar within seven months. Inflation then fell to a single digit — 9.7% in December 2025 — and
policymakers declared progress. It did not hold. Headline inflation ran 11.7% in April 2026, 13.4%
in May, and **13.9% in June 2026, with food inflation at 15.1%**, the highest since January 2025.
The National Bank raised its policy rate to 16% in July 2026 and expects double digits to persist
for another six months. Volatility is the condition that makes stale data dangerous.

**2. Humanitarian budgets collapsed.** Global humanitarian funding fell by more than 30% between
2024 and 2025, with US humanitarian support dropping from roughly $14bn to $3.7bn. The 2025 Global
Humanitarian Appeal was **35.1% funded** as of May 2026. WFP eliminated 6,000 positions; more than
a quarter of a million posts were cut across former USAID partners. Every organisation still
operating has to defend every birr, with fewer analysts to do it. *Less money and fewer staff is
precisely the condition that creates demand for cheaper, faster decision support.*

**3. Coordination itself is thinner.** No Humanitarian Needs and Response Plan is expected to be
published for Ethiopia in 2026. Partners are working from unofficial figures. When the central
coordination product weakens, the value of an independent, fast, auditable signal goes up.

**4. The enabling technology is finally local.** Amharic and Afaan Oromo speech-to-text is now
available as an API through Addis AI, and we have it wired into our Telegram bot today. Telegram is
already how people in Addis communicate. Two years ago, collecting structured prices by voice in
Amharic meant building an ASR team. Now it is an integration.

---

## 6. Value proposition — what each customer actually receives

| Customer | What they get | What it replaces |
|---|---|---|
| **Humanitarian NGO** | Basket cost and 30-day change, an affordability score, a market heat map, a spike alert feed, and a copilot that recommends a transfer adjustment band and cites every figure | An analyst rebuilding last month's JMMI factsheet in Excel, plus a margin of guesswork |
| **Food-buying business** | Their own input-cost index, cross-market sourcing table, a quote benchmark, and volatility so they know whether to lock a contract | Three phone calls to brokers who profit from the answer |
| **Researcher** | A tidy long panel with WFP-compatible columns, HXL tags, immutable snapshot IDs, a citation string, a codebook, and **no imputed values** | Monthly aggregated data with imputation they cannot distinguish from observation |

The through-line: **we do not sell prices, we sell a decision that is defensible in writing.**

---

## 7. Why it is unique

Five things, in descending order of how hard they are to copy.

1. **The agent network.** Local, recruited in person, scored, and penalised for bad data. Hardest
   to copy, and the reason the rest works.
2. **72-hour cadence at market-cell granularity.** Not "Addis cereals, monthly" but "Ehil Berenda
   teff, this morning". Our own data shows staple prices differing **13.8% to 26.0%** between Addis
   markets on the same day — a citywide average hides the entire decision.
3. **We never impute.** REACH's own JMMI guidance permits imputing up to 15% of MEB items. Our
   architecture forbids it outright: below the publication threshold, a cell returns
   `insufficient_data` with a null value, and that row stays in every export. For a researcher this
   is strictly better; for an auditor it is the difference between a defensible number and a
   plausible one.
4. **A complete audit chain.** Submission → contributor → reviewer decision → index snapshot →
   method version. Every published figure is reproducible from source.
5. **Trilingual by default.** Amharic, Afaan Oromo, English — in intake and in output.

**What we are careful not to claim.** We are Addis-only against JMMI's national coverage. We price
5 staples against the MEB's 53 items. We have no household income data, so we produce the
food-price input to a transfer value, not the transfer value itself. Saying this out loud is what
makes the rest believable to anyone who knows the sector.

---

## 8. Why it is compelling

Three sentences an investor can repeat.

- **The cost of being wrong is enormous and quantified.** One misjudged transfer value across
  50,000 households is 39 million birr a month. Good data is orders of magnitude cheaper than a bad
  decision.
- **The same data serves three buyers with no additional collection.** One index, three
  presentations — NGO basket, business input cost, research panel. Each new segment is a
  presentation layer, not a new company.
- **It compounds.** Every accepted submission lengthens the time series, which improves the spike
  detection, which improves the recommendations, which attracts more customers, which funds more
  agents. The dataset is the asset, and it cannot be bought.

---

## 9. Vision and mission

> **Mission.** Make the real cost of food in Ethiopian markets visible fast enough to act on.

> **Vision.** Become the reference price layer for East African markets — the number that NGOs,
> businesses, researchers and government all cite, because it is the fastest one anybody can audit.

---

## 10. Market growth

Three tailwinds, all pointing the same way.

- **Cash is displacing in-kind aid.** Ethiopia's 2024 response plan recommended a minimum 25% of
  humanitarian funding be delivered through cash and voucher modalities, and noted a marked growth
  in both sectoral CVA and multi-purpose cash. Every birr that shifts from food distribution to
  cash increases the value of accurate price data, because cash only works if you know what it
  buys.
- **Budget pressure raises the value of efficiency tools.** A sector operating at ~35% of appeal
  with a quarter-million fewer staff will buy things that let fewer people make better decisions.
- **Urban food commerce is growing.** Addis restaurants, hotels, caterers and distributors are
  expanding and have no procurement benchmark at all. This segment did not exist as a data buyer
  five years ago.

---

## 11. The service

**Waga = Verified Ethiopian market data + Food Affordability Score + Market Heat Map + AI Copilot.**

```
Market agents (Telegram, Amharic/Oromo/English, text or voice)
        ↓
Human review — accept or flag
        ↓
72-hour weighted-median index per market × commodity cell
   publish at ≥3 accepted submissions, else insufficient_data
        ↓
   ┌──────────────┬───────────────────┬────────────────────┐
NGO dashboard   Business sourcing   Research panel
+ AI copilot    + decision layer    + snapshots, codebook
```

Phase 1 scope: Addis Ababa, 9 named markets, 5 staples (teff, wheat, maize, onion, cooking oil).

**Already built:** database schema, authentication, Telegram intake bot, Addis AI speech-to-text,
agent applications, invite codes, reputation scoring, redemption queue, submission API, admin
catalogue. **In progress:** index computation, affordability score, heat map, copilot, exports —
all with frozen API contracts and mock data, so the frontend is being built in parallel today.

---

## 12. Service size — reachable market (SAM)

Ethiopia only, annual.

| Segment | Basis | Estimate |
|---|---|---|
| Humanitarian | 2024 response plan required $3.24bn; ECWG recommends ≥25% via CVA ⇒ ~$810M CVA. Market monitoring and assessment typically 0.5% of programme value | **~$4.0M** |
| Business | ~2,000 addressable food-buying operators in Addis at ~3,500 ETB/month | **~$1.0M** |
| Research | Universities, think tanks, monitoring organisations; data licences | **~$0.2M** |
| **Total SAM** | | **~$5.2M / year** |

*Model, not a measurement. The 0.5% monitoring share is the load-bearing assumption and the first
thing to validate in customer interviews.*

## 13. Total available market (TAM)

The product generalises to any country running a Joint Market Monitoring Initiative — roughly 30
countries.

| Layer | Basis | Estimate |
|---|---|---|
| **TAM** | 2025 Global Humanitarian Appeal $47bn × 25% CVA = ~$11.8bn × 0.5% monitoring | **~$59M / year** |
| **SAM** | Ethiopia, all three segments (§12) | **~$5.2M / year** |
| **SOM** | Addis Ababa by year 3 (§18) | **~$0.3M / year** |

This is a focused market, not a billion-dollar one, and we should say so. The case is a capital-
efficient business reaching profitability on a small base, in a market with a durable local moat
and a clear regional expansion path — not a hypergrowth story.

---

## 14. Competition

| Competitor | Strength | Where we win |
|---|---|---|
| **JMMI** (REACH + Cash Working Group) | National reach, 53-item MEB, sector standard, free | Monthly vs our 72 hours; woreda medians vs named markets; permits imputation, we never do |
| **WFP VAM / DataBridges** | Long series, ALPS spike index, real API, global | Monthly and coarse; not designed for "what is teff in Ehil Berenda today" |
| **FEWS NET** | Authoritative early warning | Outlook product, not an operational price feed |
| **ESS CPI** | Official, authoritative | Monthly, national, aggregated; unusable for market-level operations |
| **HDX** | Free, tidy, HXL-tagged | Republishes others' data; same cadence limits |
| **Consultancies** | Depth and tailoring | $000s per one-off report, stale within a quarter |
| **Doing nothing / internal Excel** | Free, already there | The real incumbent, and the honest one to beat |

**The honest constraint:** most of this data is free. We are not selling the existence of prices.
We are selling **speed, market-level specificity, an audit trail, and a decision layer** — and
proving it against the actual incumbent, which is a spreadsheet.

**Why we are not simply displaced:** the sector standard is a coordination product, not a company.
It is not going to become real-time, and it depends on partner enumerators whose funding just fell
by a third. We are complementary to it, and we sell against the gap it structurally cannot close.

---

## 15. How we generate revenue

| Stream | Who | Price | Notes |
|---|---|---|---|
| **NGO Starter** | Small and local NGOs | $100/mo | Dashboard, affordability score, monthly brief |
| **NGO Professional** | Mid-size CVA programmes | $500/mo | Heat map, alerts, copilot, exports |
| **NGO Enterprise** | Large INGOs, UN agencies | $1,500/mo+ | API, custom reports, multi-user, support |
| **Business Buyer** | Restaurants, caterers, hotels | 3,500 ETB/mo (~$25) | Cost index, sourcing table, quote benchmark |
| **Business Trade** | Distributors, processors | 14,000 ETB/mo (~$100) | Full history, CSV, API |
| **Research licence** | Universities, think tanks | ~$150/mo or per-snapshot | Citable snapshots, codebook, panel |

**Free forever:** public price lookup. It is trust, distribution, and agent recruitment — not a
funnel leak. **No advertising**, ever; it would destroy the credibility the whole product rests on.

Price businesses **in birr**. A dollar price reads as "not for us" to an Addis caterer.

---

## 16. Go-to-market

**Segment priority is sequential, not parallel.** NGOs first — they have budget, a recurring
decision, and they cluster in one room.

**Phase 1 — Addis NGOs (months 0–6).** The Ethiopia Cash Working Group is the entire market in one
forum. Show up, present the 72-hour basket against the monthly one, and give free access to three
partners in exchange for feedback and a reference. Convert on the quarterly transfer-value review
cycle — that is the moment the need is acute and the budget is live.

**Phase 2 — Addis businesses (months 4–12).** Bottom-up and self-serve. Free quote benchmark as
the hook: a caterer checks one teff quote, sees it is 14% over market, and the product has paid for
itself before they have spoken to anyone. Sell through supplier associations and hotel groups.

**Phase 3 — Research and regional (months 12–24).** Universities license snapshots. Expand to a
second and third Ethiopian city, then a second JMMI country.

**Agent network runs ahead of sales.** Data quality is the product; agents must be recruited before
customers arrive, not after.

---

## 17. Break-even

Monthly operating cost, lean, year 1:

| Item | Monthly |
|---|---|
| Team — 4 founders at a minimal draw | $1,600 |
| Market agent rewards — 30 agents × ~700 ETB | $150 |
| Infrastructure — database, hosting, AI APIs | $150 |
| Operations and contingency | $100 |
| **Total** | **$2,000** (~280,000 ETB) |

**Break-even ≈ $2,000 MRR**, reachable several ways:

- **4 NGO customers** (1 Starter + 3 Professional) = $1,600, plus **16 business Buyers** = $400
- or **3 NGO Professional + 1 Enterprise** = $3,000 — break-even on four customers alone

**We break even on four humanitarian customers.** That is the single most important number in this
deck, because it means the business does not require the market to be large — only real.

---

## 18. Financial projection

Model. Year-end monthly run-rate, Addis-only through year 2.

| | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| NGO customers | 5 | 13 | 30 |
| Business customers | 20 | 90 | 300 |
| Research licences | 1 | 4 | 10 |
| **MRR** | **$2,350** | **$8,750** | **$24,800** |
| **ARR run-rate** | **~$28k** | **~$105k** | **~$298k** |
| Monthly cost | $2,000 | $5,500 | $14,000 |
| Monthly net | +$350 | +$3,250 | +$10,800 |
| Cities covered | 1 | 2 | 4 |
| Active market agents | 30 | 80 | 200 |

**Assumptions.** No churn modelled in year 1 (unrealistic — treat as an upper bound). Business tier
at ~$25/month equivalent. Costs scale with agent count and city count, not with customer count,
because the marginal cost of an additional subscriber is near zero. Year 3 assumes expansion beyond
Addis but stays inside Ethiopia.

**Read it as:** profitable in year 1 at small scale, ~$300k ARR by year 3 on ~6% of the Ethiopian
SAM, at which point regional expansion — not deeper Ethiopian penetration — is the growth story.

---

## 19. What we need from investors

**Ask: $150,000 for 18 months of runway.**

| Use | Amount | Buys |
|---|---|---|
| Agent network — Addis 30 → 150 agents across 4 cities | $45,000 | Coverage, which is the product |
| Team — 4 FTE for 18 months | $65,000 | Ship index, copilot, dashboard; run BD |
| Infrastructure and AI | $12,000 | Database, hosting, STT and LLM inference |
| Sales and pilots — CWG engagement, 3 free NGO pilots | $18,000 | The reference customers everything else depends on |
| Legal, data licensing, contingency | $10,000 | |

**Milestones this buys:**

| By month | Milestone |
|---|---|
| 3 | NGO dashboard live; 3 pilot NGOs using it for a real transfer-value decision |
| 6 | First paying NGO; 60 agents; 2 cities |
| 9 | Business tier launched; break-even in sight |
| 14 | **Cash-flow break-even** |
| 18 | 4 cities, 150 agents, 13 NGO and 90 business customers; ready for a second country |

**Beyond capital, we need:** an introduction to the Ethiopia Cash Working Group, one advisor who
has actually set a transfer value, and help with the institutional procurement process — UN and
INGO vendor onboarding is slow and we should start it before we need it.

---

## 20. Where AI is used

Relevant for the hackathon, and for the "is this an AI company or a wrapper?" question.

### The governing rule

> **AI never invents a price.** Every figure in every AI-generated output resolves to a published
> index cell, and the response carries machine-readable citations. A response with no citations is
> treated as a bug, not a degraded answer.

This is already enforced in the codebase — the speech-to-text intake doc states it plainly: STT
output is a *draft* that the agent must confirm before it is saved, and *"AI does not invent
prices."* This rule is what separates us from a chatbot pointed at a spreadsheet, and it is the
first thing we would show a technical judge.

### 20.1 Reports and analysis — the main AI surface

**Automated situation briefs.** The weekly and monthly NGO brief is generated, not written. From
the index the system composes: basket movement and drivers, which markets are hottest, which cells
are spiking, the recommended transfer adjustment band, and the birr impact of doing nothing. Today
this is a human analyst rebuilding a spreadsheet for a day. Output is bilingual, English and
Amharic.

**Contribution analysis — the "why".** A percentage on its own is not decision-ready. The system
decomposes basket movement into per-item contributions, so the brief says *"teff is 55% of the
increase"*, which is the sentence that goes into a justification memo. This is what turns a chart
into an argument.

**Spike detection.** `waga-spike-v1` fits a trend over a 30-day window, scores the residual against
its standard deviation, and bands the result jointly with the percent deviation from trend. Same
structure as WFP's ALPS indicator, run daily instead of monthly.

> **A finding worth telling judges.** The first version scored prices against a trailing *median*
> and flagged 33 of 36 market cells, including "crisis" on a 4.8% move — because on a rising market,
> trend reads as spike. Detrending dropped it to 4 genuine alerts. We then found a second failure:
> a cell with a very tight price history posts a large z-score on a 2% move, statistically unusual
> but economically trivial. So the band takes the *weaker* of the statistical and the economic
> signal. **Knowing why a model is wrong is the actual work**, and this is a concrete example of it.

**Confidence that tracks coverage.** When underlying cells are thin, the answer says so and lowers
its stated confidence rather than guessing. Cooking oil currently publishes in only 3 of 9 markets,
and any oil recommendation carries that caveat visibly.

### 20.2 The copilots

| Copilot | Question it answers |
|---|---|
| **Humanitarian** | "How should we adjust cash assistance this month?" → adjustment band, cited figures, birr impact |
| **Business** | "I need 400kg of teff a month — what do I budget and where do I buy?" → budget range, cheapest market, contract-timing advice |

Rule-based core with LLM narration on top. The rules produce the numbers; the model only turns them
into a sentence. This is deliberate: it is auditable, testable, cheap, and it degrades safely.

### 20.3 Language AI — already shipped

| Capability | Status |
|---|---|
| Amharic and Afaan Oromo speech-to-text via Addis AI, in the Telegram bot | **Live** |
| Voice note → transcript → agent confirms → submission | **Live** |
| Text normalisation across Ethiopic, Latin and English scripts | **Live** |
| Synonym matching — `xafii`, `tef`, `ጤፍ` all resolve to `teff_mixed` | **Live** |
| Low-confidence match falls back to confirm buttons, never a silent wrong match | **Live** |
| Bilingual report generation | Planned |

An agent who cannot type Amharic quickly can speak into Telegram and submit a price in seconds.
That is the difference between a network of 30 agents and a network of 300.

### 20.4 Data quality

AI triages, humans decide. Implausible submissions are surfaced for reviewer attention using price
hint bounds, deviation from the current cell, and contributor history. **No automatic
accept-or-reject.** A human reviewer makes every call, because the audit chain is the product and
an unreviewable acceptance would break it.

### 20.5 What we deliberately do not use AI for

Worth stating out loud, because restraint is a signal of judgement.

- **Price forecasting.** Not enough history, and a wrong forecast presented confidently is worse
  than no forecast.
- **Imputing missing prices.** Architecturally forbidden. Missing means missing.
- **Auto-accepting submissions.** Humans review.
- **Generating any figure not already in the database.**

---

## Sources

**Ethiopian macroeconomy**
- Ethiopian Statistics Service via Ethiopian Monitor and StockMarket.et, July 2026 — June 2026 headline inflation 13.9%, food inflation 15.1%, highest since January 2025
- National Bank of Ethiopia, July 2026 — policy rate raised to 16%; double-digit inflation expected for six months
- UNDP, *Ethiopia Quarterly Economic Profile*, April 2025 — July 2024 FX reform, 30% day-one depreciation, birr 57.3 → 125/USD, 15–20% edible oil increases
- Wikipedia, *2024 Ethiopian foreign exchange rate policy* — NBE reform, IMF/World Bank $10.7bn

**Humanitarian sector**
- OCHA, *Ethiopia Humanitarian Response Plan 2024* — 21.4M in need, 15.5M targeted, $3.24bn required; minimum 25% CVA recommendation; MPC target 1.4M
- Sida, *Ethiopia Humanitarian Crisis Analysis 2026*, March 2026 — no HNRP expected for 2026; partners on unofficial figures; $141M initial allocation
- Refugees International, *A Generational Collapse*, 2026 — >30% decline in global humanitarian funding 2024→2025; US $14bn → $3.7bn; WFP 6,000 posts cut
- DevelopmentAid, 2026 — 2025 Global Humanitarian Appeal ($47bn) 35.1% funded as of May 2026
- Chronicle of Philanthropy / The Conversation, 2026 — 83% of USAID programmes cancelled; 81 NGOs closed offices

**Market monitoring standards**
- REACH / IMPACT, *Global Guidance Note: JMMI*, V1 2025 — Market Functionality Score dimensions and weights; aggregation and imputation rules including the 15% imputation ceiling
- REACH Ethiopia JMMI factsheets, 2025 — 53-item MEB; December 2025 national full basket 17,700 ETB, food basket 16,135 ETB
- Ethiopia Cash Working Group, *MEB National Reference Guide*, June 2025 — transfer value = MEB cost − household income; quarterly review; six-month revision trigger
- WFP / CERDI, *Calculation and Use of the ALPS Indicator* — trend-residual method and thresholds

**Waga internal**
- `contracts/mock/` — basket 4,142.35 → 4,923.64 ETB (+18.9%); cross-market spreads 13.8%–26.0%; 36 of 45 cells published
- `docs/data-products-research.md`, `docs/business-segment.md`, `docs/api-contracts-v1.md`
