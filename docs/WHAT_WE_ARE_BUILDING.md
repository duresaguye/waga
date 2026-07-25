# What We Are Building — Final Product Scope (for Agents)

**Read this before adding features.**  
Do not make Waga bigger. Make it smarter.

---

## Positioning (final)

> **Waga Intelligence** is Ethiopia's AI-assisted food affordability monitoring platform that helps humanitarian organizations understand real market conditions and make smarter cash assistance decisions.

Waga is **B2B food-price intelligence for NGOs**, not a consumer price website.

**Hackathon / MVP formula:**

> **Waga = Verified Ethiopian Market Data + Food Affordability Score + Market Heat Map + AI Humanitarian Copilot**

---

## Primary customer

**First and only beachhead for v1:**  
Addis Ababa humanitarian organizations running cash / food assistance.

Free public lookup is allowed for trust.  
Farmers, banks, insurance, national coverage, and heavy forecasting are **out**.

Business detail: `docs/business-model-early.md`  
Customer research: `docs/customer-and-market-brief.md`  
Agent apply fields: `docs/agent-onboarding.md`

---

## Product pillars (build these)

| Pillar | What it is | Why judges care | Difficulty | v1 rule |
|---|---|---|---|---|
| **1. Verified Price Network** | Scored contributors submit via Telegram → review → accepted into index; bad data → penalty/ban | Trust + local moat | Medium | **Must ship** |
| **2. Food Affordability Score** | Simple score / basket cost for a fixed staple set in a place (e.g. Addis) | Instant “smart product” feel | Easy | **Must ship** |
| **3. Market Heat Map** | Map or market cards showing where prices / affordability are hot (up) or cool | Visual, memorable demo | Medium | **Must ship** (Addis markets first) |
| **4. AI Humanitarian Copilot** | Assistant that answers: “How should we adjust cash assistance?” using our data | Decision product, not raw charts | Medium | **Must ship** (rule-based + LLM optional) |
| **5. Impact Measurement** | Show “if you ignore +18%, cost to X families is Y birr” | Makes value obvious | Easy | **Should ship** for demo |
| Price prediction | Forecast future prices | Weak with little data | Hard | **Roadmap only** |

---

## Phase 1 geographic + basket scope

**City:** Addis Ababa only  

**Markets (well-known Addis + Other):**
1. Merkato  
2. Shola Gebeya  
3. Ehil Berenda  
4. Atikilt Tera  
5. Piazza  
6. Saris  
7. Akaki  
8. Asko  
9. Kera  
10. **Other** — agent types the market name if not listed  

*(Stay in Addis Ababa for v1; do not expand nationally yet.)*

**Commodities (5):**
1. Teff (mixed)  
2. Wheat  
3. Maize  
4. Onion  
5. Cooking oil  

**Units:** kg (foods), liter (oil)  
**Index window:** rolling 72 hours  
**Publish rule:** ≥3 accepted submissions per market–commodity cell  

---

## System to build (realistic stack)

```text
Contributors (Telegram bot)
        │
        ▼
FastAPI backend  ←→  PostgreSQL (Supabase)
        │
        ├── Review / verify submissions
        ├── Market prices + index snapshots
        ├── Food Affordability Score
        ├── Market heat map API
        └── Humanitarian Copilot API
        │
        ▼
NGO Dashboard (React / Next.js)
  - basket cost over time
  - affordability score
  - heat map
  - copilot recommendation
  - impact example
```

| Layer | Choice | Notes |
|---|---|---|
| Backend | FastAPI (this repo) | Users, prices, review, scores, exports |
| DB | PostgreSQL | Commodities, markets, submissions, index history |
| Intake | `telegram_bot/` | Structured buttons first; Addis AI STT later |
| Frontend | React / Next.js | NGO dashboard — separate app or `frontend/` later |
| AI | Assist, don’t invent prices | Rules + optional LLM over **our** verified data |

---

## Feature specs (what “done” means)

### 1) Verified Price Network
- Telegram: consent → market → commodity → price → confirm  
- Backend stores pending submission with provenance  
- Operator accepts / flags  
- Only accepted prices enter affordability score + heat map  
- Dry-run bot is OK until `POST /submissions` exists  
- **Not pure voluntary** — see Contributor Reputation below  

### 1b) Approved Market Agents

**Rule:** Only **approved market agents** submit for score/rewards.

| Path | How someone becomes an agent |
|---|---|
| **Apply** | Telegram / web apply form → admin approve |
| **Invite code** | Team gives `/agent CODE` after offline onboarding |
| **Allowlist** | Team adds Telegram ID directly |

- Guests can apply; they cannot submit scored prices until approved  
- Agents report real market prices  
- Score/money only applies to approved agents  
- Bad data still → penalty / ban  

**Do not show applicants** why we gate agents (no “people could fake prices from home” copy in bot or web). Keep user copy positive: apply → approval → submit → score → redeem.

### 1c) Contributor Reputation, Rewards & Penalties

Open voluntary intake is too weak and too easy to game. Waga uses **approved agents + score now + money later**.

| Event | Effect (v1) | Later |
|---|---|---|
| Submission accepted | **+score** (reputation points) | Counts toward payout tier |
| Streak of correct accepts | Bonus score | Higher reward rate |
| Submission flagged / rejected | **−score** | Warning |
| Repeated bad data | Soft ban (cooldown) → hard ban | Permanent exclude + forfeit |
| High reputation threshold | “Trusted agent” badge in bot | Eligible for **monetary reward** |

**v1 (implemented — see `docs/agent-score.md`):**
- Invite activate → agent
- Score on pending / accept / flag
- Redeem at 50+ (reward *request*; payout offline)
- Ban after 3 flags
- Telegram: score card + redeem buttons
- API under `/api/v1/agents/...`

**v1.5 / post-hackathon:**
- Real airtime / mobile money payouts for trusted agents
- Funded by NGO subscription revenue (data quality budget)
- Admin tools for invites + payouts

**Do not** promise large payments without a funding rule.  
Say: *“Approved market agents earn reputation for correct prices and can unlock micro-rewards. Abuse is penalized or banned.”*

**How it works (read this):** [`docs/agent-score.md`](agent-score.md)

### 2) Food Affordability Score
- Input: location (Addis) + fixed 5-item basket  
- Output examples:
  - current basket cost (ETB)
  - change vs prior period (%)
  - score label: e.g. Stable / Tightening / Severe  
- Keep formula simple and documented (no black box)

### 3) Market Heat Map
- Show Addis markets as map points or clear market cards  
- Color by recent % change or affordability pressure  
- Example story: “Ehil Berenda teff +8%, Atikilt Tera onion +12%”  
- v1 can be **market cards + simple map**; perfect GIS is not required  

### 4) AI Humanitarian Copilot
- Answers NGO questions using Waga data only, e.g.:
  - “How much did the Addis basket rise this month?”
  - “Should we adjust cash assistance?”  
- Response shape:
  - basket then / now  
  - % change  
  - suggested adjustment band (e.g. +15–18%)  
  - short plain-language reason  
- Must cite underlying Waga figures (no hallucinated prices)

### 5) Impact Measurement (demo)
- Convert % miss into birr: families × gap = impact  
- Shown on dashboard / pitch demo, not a separate product  

---

## Explicitly out of scope (do not build now)

- Price prediction as a main feature  
- OCR / receipt scanning / Google Vision  
- National Ethiopia coverage  
- Farmers, banks, insurance products  
- Consumer-paid app  
- Ads  
- Full mobile-money payout rails (v1 = score + ban only; money is next)  
- Background ML training pipelines  
- Perfect multi-city heat maps before Addis works  

---

## Demo story (product acceptance test)

1. NGO opens Waga → Addis Ababa → 5 essential foods  
2. Sees basket: June **4,100** → July **4,850** (**+18%**)  
3. Heat map shows which markets are hottest  
4. Copilot recommends raising assistance **~15–18%**  
5. Impact line: wrong transfer × N families = large birr loss  
6. Optional: show one verified submission path (Telegram → review → published)

If this story works end-to-end, the MVP is successful.

---

## Agent build order

1. Submissions API + review (wire Telegram dry-run → real)  
2. Contributor reputation (+/− score, ban) on accept/flag — Track A  
3. Index / basket cost + **Food Affordability Score**  
4. Heat map API + simple dashboard view  
5. Humanitarian Copilot endpoint + UI panel  
6. Impact numbers on the same dashboard  
7. Later: micro-rewards for trusted scores, Addis AI STT, more markets, API billing  

---

## Docs map

| Doc | Purpose |
|---|---|
| **`docs/WHAT_WE_ARE_BUILDING.md`** | **This file — product truth for agents** |
| **`docs/WORK_SPLIT.md`** | **Backend ownership — Track A vs Track B (avoid double work)** |
| `docs/agent-score.md` | Agent reputation rules + API |
| `docs/business-model-early.md` | Who pays, pricing, why they stay |
| `docs/customer-and-market-brief.md` | NGO landscape & competitors |
| `docs/telegram-bot.md` | Telegram intake details |
| `AGENT.md` | Backend architecture & coding rules |
| `plan.md` | Implementation plan / iterations |

When product and code conflict, **prefer this file for product scope**, then `AGENT.md` for how to implement in the backend.
