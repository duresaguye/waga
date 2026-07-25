# Backend Work Split — Avoid Double Building

**Product truth:** `docs/WHAT_WE_ARE_BUILDING.md`  
**Coding rules:** `AGENT.md`

Two backend tracks. **Do not touch the other track’s owned files** unless agreed in chat.
If you need a shared contract change, update **Shared contracts** below first, then both sides adapt.

---

## Assign names (fill in)

| Track | Owner | Focus |
|---|---|---|
| **A — Intake & Trust** | _you or coworker_ | Submissions, review, Telegram → API |
| **B — Intelligence** | _other person_ | Index, Affordability Score, Heat Map, Copilot |

---

## Already done (do not rebuild)

| Area | Status | Owners of record |
|---|---|---|
| Auth (JWT, login, roles, admin create) | Done | shared / leave alone |
| Models: users, contributors, submissions, verification, index_values, reference | Schema exists | extend carefully |
| Admin reference-data routes | Partial | Track A may extend seed only |
| Health | Done | leave |
| Telegram bot scaffold (dry-run) | Done in `telegram_bot/` | Track A owns next wiring |

---

## Track A — Intake & Trust (data in)

**Goal:** Verified prices can enter the system.

### Own these deliverables
1. `POST /api/v1/submissions` — structured create (REST + Telegram payload)
2. Contributor resolve + consent recording
3. Review APIs: list pending, accept, flag
4. **Approved agents only:** allowlist + invite codes; block public submit-for-score
5. **Agent score backend (done for v1):** see **`docs/agent-score.md`** for full how-it-works  
   - migrate `0004`, `/api/v1/agents/*`, bot dry-run + live API  
   - next: review service should call `apply_review` on accept/flag
6. Add `input_mode=telegram` (enum + migration if needed)
7. Seed Phase 1 markets + commodities (Ehil Berenda, Atikilt Tera, 5 staples)
8. Wire `telegram_bot` → real API (`WAGA_TELEGRAM_DRY_RUN=false`)
9. Tests for submit + review + reputation rules  
   *(Real money payouts = later; not Track A v1)*

### Own these paths (prefer)
```text
app/api/routes/submissions.py          (new)
app/api/routes/reviews.py              (new)
app/services/submissions.py            (new)
app/repositories/submissions.py        (new)
app/repositories/verification.py       (new)
app/schemas/submissions.py             (new)
telegram_bot/**                        (existing — A continues)
seed_data/** or commands/seed_*        (new)
migrations/*input_mode* / seed         (A-owned migrations)
```

### Do not build (Track B)
- Affordability score formula / routes
- Heat map routes
- Copilot routes
- Index rebuild / weighted median logic (except: **call** B’s recompute hook on accept — see contract)

### Done when
- Telegram (or curl) can create a **pending** submission
- Operator can **accept/flag**
- Accept triggers index recompute for that market–commodity cell (via shared service interface from B)

---

## Track B — Intelligence (value out)

**Goal:** NGO-facing numbers from accepted data.

### Own these deliverables
1. Index calculation for a market–commodity cell (72h, ≥3 accepted → publish / else insufficient)
2. `GET` current price / series (minimal read APIs)
3. **Food Affordability Score** API (Addis 5-item basket)
4. **Market Heat Map** API (per-market pressure / % change)
5. **AI Humanitarian Copilot** API (rule-based first: % change → suggested +15–18% style band)
6. Impact helper (families × gap → birr) — can be part of copilot response
7. Tests for score / heat / copilot math

### Own these paths (prefer)
```text
app/services/index_calculation.py      (new)
app/services/affordability.py          (new)
app/services/heatmap.py                (new)
app/services/copilot.py                (new)
app/repositories/index_values.py       (new)
app/repositories/reporting.py          (new)
app/api/routes/prices.py               (new)
app/api/routes/affordability.py        (new)
app/api/routes/heatmap.py              (new)
app/api/routes/copilot.py              (new)
app/schemas/prices.py / affordability / heatmap / copilot
migrations only if B needs new tables   (coordinate first)
```

### Do not build (Track A)
- Submission create / review mutations
- Telegram bot handlers
- Consent / contributor create flows

### Done when
- With seeded + accepted sample data, APIs return:
  - basket then/now + %  
  - affordability label  
  - heat map cells for 2 markets  
  - copilot recommendation citing those numbers  

---

## Shared contracts (agree once, both use)

### Phase 1 codes (frozen)
| Type | Codes |
|---|---|
| Markets | `ehil_berenda`, `atikilt_tera` |
| Commodities | `teff_mixed`, `wheat`, `maize`, `onion`, `cooking_oil` |
| Units | `kg` (foods), `liter` (oil) |

Same as `telegram_bot/reference.py` — Track A owns seed alignment.

### Submission create body (Track A publishes; B reads DB)
```json
{
  "client_submission_id": "uuid",
  "market_code": "ehil_berenda",
  "commodity_code": "teff_mixed",
  "price": 95.5,
  "unit": "kg",
  "external_contributor_id": "telegram:123",
  "consent_version": "contributor-v1",
  "input_mode": "telegram",
  "source": "user"
}
```

### On accept (A → B hook)
Track A’s review service must call:

```text
IndexCalculationService.recompute(market_id, commodity_id)
```

Track B implements that method first as a stub that writes/updates `index_values`, then fills real math.

### Affordability basket (Track B)
Fixed order: teff_mixed, wheat, maize, onion, cooking_oil  
City aggregate = combine both markets (document method: e.g. average of available published cell prices).

### API prefix
All under `/api/v1/...`  
Register routers in `app/api/router.py` — **add only your routes**; don’t rewrite the other’s includes.

---

## Parallel week plan

| Day focus | Track A | Track B |
|---|---|---|
| 1 | Submission schema + POST create | `recompute()` stub + index read shape |
| 2 | Review accept/flag + pending list | Real 72h / threshold index math |
| 3 | Seed + Telegram live wire | Affordability Score API |
| 4 | Fix edge cases + tests | Heat map API |
| 5 | Integration with B on accept→recompute | Copilot + impact; joint demo data |

Daily sync (15 min): contracts only — schema changes, migration order, demo data.

---

## Merge / conflict rules

1. **One track owns a file** — other opens a PR comment, doesn’t rewrite.  
2. Shared files (`router.py`, `enums.py`, `dependencies.py`, `models/*`): smallest possible diff; announce in chat before edit.  
3. Migrations: **timestamp order** — A and B don’t invent conflicting revisions; rebase if needed.  
4. No new product pillars without updating `WHAT_WE_ARE_BUILDING.md`.

---

## Frontend note

Dashboard (React/Next) is **not** in this backend split. Either a third person or later.  
Backend ships JSON that the demo story needs; mock UI is OK until frontend starts.

---

## Quick claim checklist

Copy into chat and fill:

```text
I take Track __ (A or B).
Owner name: ________
Starting today with: ________
```
