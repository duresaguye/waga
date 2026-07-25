# Deploy on Render (from GitHub)

Deploys two services from this repo:

| Service | Type | Role |
|---|---|---|
| `waga-api` | Web | FastAPI (`$PORT`, migrate on release) |
| `waga-telegram-bot` | Background Worker | Telegram polling bot |

Blueprint: [`render.yaml`](../render.yaml)

## 1. Push to GitHub

```bash
git push origin feat/agent-intake-submissions
```

(Or merge to `main` and point Render at that branch.)

## 2. Create Blueprint

1. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**
2. Connect `duresaguye/waga`
3. Select branch and apply `render.yaml`

## 3. Set secrets (both services)

**API (`waga-api`)**

| Key | Value |
|---|---|
| `WAGA_DATABASE_URL` | Supabase Postgres URL (`postgresql://…` or `postgresql+asyncpg://…`) |
| `WAGA_JWT_SECRET_KEY` | ≥32 random bytes |
| `WAGA_ADDIS_AI_API_KEY` | Addis AI key (review assist) |

**Bot (`waga-telegram-bot`)**

| Key | Value |
|---|---|
| `WAGA_TELEGRAM_BOT_TOKEN` | BotFather token |
| `WAGA_ADDIS_AI_API_KEY` | Same Addis key (voice) |
| `WAGA_TELEGRAM_AGENT_IDS` | Optional pre-approved Telegram user IDs |

`WAGA_API_BASE_URL` is built automatically from the API’s `RENDER_EXTERNAL_URL` + `/api/v1` via `scripts/start-bot.sh`. Override with `WAGA_API_BASE_URL` if needed.

## 4. After first deploy

1. Open `https://<waga-api>.onrender.com/api/v1/health`
2. Create admin (one-time), from a machine that can reach the DB:

   ```bash
   uv run waga-create-admin --email you@example.com
   ```

3. Seed Phase 1 markets/commodities if not already:

   ```bash
   uv run waga-seed-phase1
   ```

4. In Telegram: `/agent WAGA-ADDIS-01` then `/submit`

## Notes

- Free web services **sleep**; keep API on a paid instance for a reliable demo, or expect cold starts.
- Bot worker must stay running (not a web service).
- Migrations run automatically: `preDeployCommand` → `scripts/migrate.sh`
- Do not commit `.env`
