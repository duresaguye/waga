# AI-assisted submission review

Waga uses **rules + Addis AI** to triage every pending price report. Humans still accept or flag; AI recommends and explains.

## Pitch line

> We use Addis AI to triage every price report against other agents at the same market, that agent’s history, and recent medians — then accept, hold, or flag with a reason. AI never invents prices.

## Flow

```text
POST /submissions (pending)
        │
        ▼
Rules compare:
  - sanity band for commodity
  - same market accepted prices
  - same agent recent prices
        │
        ▼
Addis LLM (optional) → verdict + reason
        │
        ▼
Admin queue:
  GET  /admin/reviews/pending
  POST /admin/reviews/{id}/triage
  POST /admin/reviews/{id}/accept
  POST /admin/reviews/{id}/flag
```

## Env

Same key as voice STT:

```env
WAGA_ADDIS_AI_API_KEY=sk_...
WAGA_ADDIS_AI_CHAT_URL=https://api.addisassistant.com/api/v1/chat_generate
WAGA_ADDIS_AI_DEFAULT_LANG=am
WAGA_REVIEW_AI_ENABLED=true
```

If the key is missing, triage still runs with **rules-v1** only.

## API (admin / operator JWT)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/admin/reviews/pending` | Queue with AI fields |
| POST | `/api/v1/admin/reviews/{submission_id}/triage` | Re-run AI assist |
| POST | `/api/v1/admin/reviews/{submission_id}/accept` | Accept + score |
| POST | `/api/v1/admin/reviews/{submission_id}/flag` | Flag + score (`{"reason":"..."}`) |

## Stored fields

On `submission_verifications` (pending row):

- `ai_verdict` — `accept` \| `hold` \| `flag`
- `ai_confidence` — `high` \| `medium` \| `low`
- `ai_reason` — short English sentence
- `ai_model` — e.g. Addis model name or `rules-v1`
- `ai_checked_at`

## Migration

`20260725_0008_review_ai_assist`
