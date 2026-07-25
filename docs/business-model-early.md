# Waga — Early Business Model (Clear Version)

**Aligned with final product scope:** `docs/WHAT_WE_ARE_BUILDING.md`

**One-line positioning**

> **Waga Intelligence** is Ethiopia's AI-assisted food affordability monitoring platform that helps humanitarian organizations understand real market conditions and make smarter cash assistance decisions.

Waga is a **B2B data intelligence company**, not a consumer app.

**MVP formula**

> Waga = Verified Ethiopian Market Data + Food Affordability Score + Market Heat Map + AI Humanitarian Copilot

---

## 1. The painful problem

Humanitarian organizations must answer:

> “How much money should we give families so they can still buy enough food?”

Today they often rely on:
- delayed government CPI reports
- expensive / slow manual surveys
- outdated market studies

**Wrong numbers are expensive.**

Example:
- 50,000 families
- wrong by 500 birr each
- = **25,000,000 birr** impact

Paying for better local price data is cheaper than a bad cash decision.

---

## 2. Who can use Waga?

### A. Paying customers (main focus)

#### 1) Humanitarian NGOs ⭐ first customers
Examples: food assistance, emergency response, cash & voucher programs.

**How they use Waga**
- Location: Addis Ababa
- Basket: teff, wheat, maize, onion, cooking oil
- See **Food Affordability Score** + basket cost over time
- See **Market Heat Map** (which markets are rising fastest)
- Ask **AI Humanitarian Copilot** how to adjust cash assistance
- See **impact** if they ignore the change

**Why they pay**
Budget decisions depend on it. Continuous price movement means they need ongoing access.

#### 2) Research institutions / universities
Need historical local prices for papers, food-security analysis, policy work.

**They buy:** monthly reports, research datasets, API access.

#### 3) Government agencies (future)
Faster signals for inflation monitoring, emergency planning, food policy.  
Not the first sales target.

#### 4) Food companies / distributors (future)
Market intelligence for stocking and pricing. Later expansion.

### B. Free users (not the business)

**Public / normal people**
- Basic price lookup
- Simple market comparison
- Purpose: trust + visibility  
- **Not expected to pay**

### C. Not first customers
- ❌ Normal consumers (won’t pay monthly)
- ❌ Farmers (different problem: access, transport, production)
- ❌ Banks / insurance (distract from v1)

---

## 3. How customers buy (revenue)

### Model 1 — Subscription (main)

| Plan | Who | Price (guide) | Includes |
|---|---|---|---|
| **Starter** | Small NGOs | ~$100/month | Basic dashboard, affordability score, monthly reports |
| **Professional** | Medium orgs | ~$500/month | Real-time dashboard, heat map, AI copilot, export |
| **Enterprise** | Large orgs | Custom | API, custom reports, dedicated support |

*(For local NGOs, also offer ETB / grant-budget packaging.)*

### Model 2 — Data API
Orgs with their own systems pay for machine-readable price/index feeds.

### Model 3 — Custom reports
Example: “Monthly food price report for Oromia.”

**Do not rely on ads.** Ads kill credibility for this product.

---

## 4. Why they keep paying

| Reason | Why it matters |
|---|---|
| Prices change often | Last month’s PDF goes stale |
| Decisions are recurring | Cash programs need ongoing updates |
| Switching costs | Their reports/workflows start depending on Waga |
| Local network moat | Verified Addis contributors + reviewed data get harder to copy |

---

## 5. Early go-to-market (realistic)

**Phase 1 — Addis Ababa only**
- Markets: Ehil Berenda, Atikilt Tera
- 5 staples (teff, wheat, maize, onion, cooking oil)
- Telegram **scored contributors** + human review (**Verified Price Network**)
  - Correct accepts → reputation points (later: micro-rewards)
  - Bad data → score penalty → ban
- NGO dashboard: Affordability Score + Heat Map + Copilot + Impact

**Phase 2 — Expand region by region**
- More cities / hubs
- More commodities
- Stronger API + custom reports

**Say this to judges:**  
“Starting with Addis Ababa, expanding region by region.”

**Do not lead with:** price prediction, OCR, national coverage.

---

## 6. What AI does (honest)

AI is a helper, not the source of truth.

- **Humanitarian Copilot:** suggests cash adjustment from our verified basket data
- Flags unusual prices for review
- Later: Amharic/Oromo speech-to-text (Addis AI) in Telegram

Humans + verified contributors collect; reviewers accept/flag; index is auditable.

---

## 7. Competitive advantage (short answer)

“Why can’t someone copy this?”

1. **Local data network** — verified market contributors  
2. **Ethiopian language capability** — Amharic, Afaan Oromo, English  
3. **Market-level detail** — not only “Ethiopia inflation = X”, but market heat (e.g. Ehil Berenda teff +8% vs Atikilt Tera onion +12%)

The asset is the **Ethiopian market dataset + trust process**, not the UI.

---

## 8. Demo story (start here in pitches)

Meet an NGO in Addis Ababa.  
They ask: “How much cash assistance next month?”

They open Waga → Addis Ababa → 5 essential foods.

| Month | Basket cost |
|---|---|
| June | 4,100 birr |
| July | 4,850 birr |
| Change | **+18%** |

- Affordability Score: Tightening  
- Heat map: hottest markets highlighted  
- Copilot: increase assistance about **15–18%**  
- Impact: wrong transfer × N families = large birr loss  
- Then show verified path: Telegram → review → published  

---

## 9. Final pitch block

**WAGA Intelligence**  
AI-assisted food affordability monitoring for humanitarian decisions

| | |
|---|---|
| **Problem** | Humanitarian orgs lack fast, local, reliable food price data |
| **Solution** | Verified prices + affordability score + heat map + AI copilot for cash decisions |
| **Initial market** | Addis Ababa humanitarian organizations |
| **Revenue** | Subscription + API + custom reports |
| **Impact** | Right support to families at the right time |

---

## 10. Market agents + incentive (why data is real and keeps coming)

Do **not** let the open public farm score/money from home.

| Layer | What |
|---|---|
| **Agents only** | People we meet/onboard (or invite after talking) become market agents |
| **Score (v1)** | +points for accepted prices; −points / ban for abuse |
| **Money (later)** | Trusted high-score **agents** eligible for small payouts, funded from NGO subscriptions |
| **Quality** | Only accepted agent prices count; fake data → ban |

Pitch line: *“We recruit market agents, reward accurate reporting, and block anonymous gaming.”*

## 11. Early rule for the team

Build and sell to **NGOs first**.  
Public price lookup is free trust.  
Do not make Waga bigger — make it smarter.  
Everything else (government, retailers, forecasting, OCR) is later.

Product truth for agents: `docs/WHAT_WE_ARE_BUILDING.md`
