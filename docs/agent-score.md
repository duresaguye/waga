# Agent Score — How It Works

Backend-owned reputation for **approved market agents**.  
This is Track A. Full product context: `docs/WHAT_WE_ARE_BUILDING.md`.

---

## Big picture

```text
Person talks to Waga team
        │
        ▼
Gets invite code  (e.g. WAGA-ADDIS-01)
        │
        ▼
Telegram: /agent CODE
        │
        ▼
Becomes agent (is_agent = true)
        │
        ▼
Visits market → /submit price
        │
        ▼
Score +1 (pending) ──► reviewer accepts → score path to +10
                    └──► reviewer flags   → score −15
        │
        ▼
At 50+ points → /redeem
        │
        ▼
Admin rate converts score → birr
(example default: 1 point = 2 ETB → 50 pts = 100 birr)
        │
        ▼
Admin pays pending redeem request (airtime / mobile money)
        │
        ▼
3+ flagged reports → banned (no submit / no redeem)
```

Only approved agents can submit prices and earn score/rewards.

---

## Admin sets birr rate (important)

Score alone is not money. **Admin configures conversion in the backend:**

| Setting | Meaning | Default seed |
|---|---|---|
| `birr_per_point` | How many ETB one score point is worth | **2** |
| `redeem_min_points` | Minimum score before redeem | **50** |
| `currency_code` | Currency | **ETB** |

**Example:**  
`50 points × 2 birr = 100 ETB`

### Admin APIs (login as admin/operator)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/admin/agent-rewards/settings` | See current rate + example |
| PUT | `/api/v1/admin/agent-rewards/settings` | Set `birr_per_point` / min points |
| GET | `/api/v1/admin/agent-rewards/redeem-requests?status=pending` | Payout queue |
| POST | `/api/v1/admin/agent-rewards/redeem-requests/{id}/resolve` | Mark `paid` or `rejected` |

Example PUT body:

```json
{
  "birr_per_point": 2,
  "redeem_min_points": 50,
  "currency_code": "ETB"
}
```

When an agent redeems, a row is created in `agent_redeem_requests` with:
- points redeemed  
- birr rate used at that moment  
- **birr_amount** to pay  
- status `pending` until admin marks `paid`

---

## Score rules (single source)

File: `app/services/agent_score_rules.py`  
Bot dry-run uses the **same** numbers.

| Event | Points | Notes |
|---|---|---|
| Submit (pending review) | **+1** | Immediate credit for sending a report |
| Review **accepted** | net **+10** from start | Applies `+9` after the pending `+1` |
| Review **flagged** | **−15** | Bad / fake data |
| **Redeem** | spend all current score | Needs **≥ 50** points |
| **Ban** | — | After **3 flagged** reports |

Status labels:
- `Active` — score &lt; 20  
- `Rising` — 20–49  
- `Trusted` — ≥ 50  
- `Banned` — cannot submit or redeem  

---

## End-to-end flows

### 1) Become an agent

1. Team meets/trains the person and assigns a market.  
2. Team gives invite code (DB table `agent_invite_codes`, seed: `waga-addis-01`).  
3. Person sends in Telegram: `/agent WAGA-ADDIS-01`  
4. Backend: `POST /api/v1/agents/activate`  
   - Creates/updates `contributors` with `kind=agent`, `is_agent=true`, `telegram_id=...`  
   - Writes `agent_score_events` row type `activate`  

**Dry-run bot:** activates only in local memory (no DB).  
**Live bot** (`WAGA_TELEGRAM_DRY_RUN=false`): calls the API (backend must be up).

### 2) Submit a price (earn pending score)

1. Agent: **Submit price** → market → commodity → price → confirm.  
2. Backend score: `POST /api/v1/agents/{telegram_id}/pending` → **+1**, `pending_count++`.  
3. Later: submissions API stores the price as `pending` review (when that route exists).  

Bot shows: current score + “waiting for review”.

### 3) Review changes the score

| Reviewer action | API (temporary hooks) | Effect |
|---|---|---|
| Accept | `POST .../review/accept` | accepted_count++, score toward +10 path |
| Flag | `POST .../review/flag` | flagged_count++, score −15; ban if flags ≥ 3 |

**Next build step:** real review service should call `AgentScoreService.apply_review()` so these hooks are not used by hand.

### 4) Redeem score → birr payout request

1. Admin has set rate (e.g. 2 birr/point, min 50).  
2. Agent has score ≥ min.  
3. Taps **Redeem score** or `/redeem`.  
4. `POST /api/v1/agents/{telegram_id}/redeem`  
   - Creates `agent_redeem_requests` with **birr_amount**  
   - Zeros agent score; logs event  
5. Admin sees pending request → pays ETB → marks `paid`  
6. No automatic bank/mobile-money transfer in v1 (manual payout).

---

## Where data lives

| Store | What |
|---|---|
| `contributors` | `is_agent`, `reputation_score`, pending/accepted/flagged counts, `redeemed_total`, `banned`, `ban_reason`, `telegram_id` |
| `agent_invite_codes` | codes, active flag, use limits |
| `agent_score_events` | audit log of every +/− (activate, pending, accept, flag, redeem, ban) |
| `agent_reward_settings` | admin `birr_per_point`, `redeem_min_points` |
| `agent_redeem_requests` | payout queue (points → birr_amount, pending/paid) |

Migrations:
- `20260725_0004_agent_score.py`
- `20260725_0005_agent_reward_settings.py`

```bash
uv run alembic upgrade head
```

---

## API cheat sheet

Base: `/api/v1`

| Method | Path | Who uses it |
|---|---|---|
| POST | `/agents/activate` | Bot `/agent` |
| GET | `/agents/{telegram_id}/score` | Bot `/score` |
| POST | `/agents/{telegram_id}/redeem` | Bot `/redeem` |
| POST | `/agents/{telegram_id}/pending` | Bot after confirm submit |
| POST | `/agents/{telegram_id}/review/accept` | Reviewer / tests (temporary) |
| POST | `/agents/{telegram_id}/review/flag` | Reviewer / tests (temporary) |

Code:
- Service: `app/services/agent_score.py`  
- Routes: `app/api/routes/agents.py`  
- Schemas: `app/schemas/agents.py`  

---

## Bot modes

| Mode | Env | Score behavior |
|---|---|---|
| Dry-run | `WAGA_TELEGRAM_DRY_RUN=true` | In-memory (`telegram_bot/services/reputation.py`), same rules, no DB |
| Live | `WAGA_TELEGRAM_DRY_RUN=false` | Calls backend APIs; needs `uvicorn` + migrated DB |

Commands / buttons:
- Guest: **Enter invite code**, `/agent CODE`  
- Agent: **Submit price**, **My score**, **Redeem score**  
- `/score`, `/redeem`, `/submit`, `/help`  

---

## Example numbers

Start: **0**

1. Submit teff price → **1** (pending)  
2. Accepted → **10**  
3. Submit again → **11**  
4. Accepted → **20** (Rising)  
5. … continue until **50+** (Trusted)  
6. Redeem → score **0**, redeemed_total **50** (reward request logged)  
7. Three flagged reports over time → **Banned**

---

## What is not built yet

- Automatic mobile-money payout  
- Review UI calling accept/flag automatically  
- Admin screen to create invite codes / pay redemptions  
- Linking score events to `submission_id` (nice follow-up)

---

## For your coworker

- **Track A** owns this file + agent score APIs + Telegram wiring.  
- **Track B** should not rebuild score; they only need accepted prices for affordability / heat map / copilot.  
- When review accept lands, call `AgentScoreService.apply_review(telegram_id, accepted=True)`.
