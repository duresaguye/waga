# Deploy Telegram bot as a normal Render Web Service (webhook)

Use this when you **don’t want a Background Worker** (card / paid instance).

The bot receives Telegram updates over HTTPS. Free web services can sleep; Telegram’s POST wakes them.

## 1. Push code that includes webhook support

Needs `telegram_bot/bot.py` webhook mode + `python-telegram-bot[webhooks]`.

## 2. Create a second Web Service (not Background Worker)

Render → **New → Web Service** → same repo `duresaguye/waga`

| Field | Value |
|---|---|
| Name | `waga-telegram-bot` |
| Runtime | Docker |
| Dockerfile path | `./Dockerfile` |
| Docker Command | `./scripts/start-bot.sh` |
| Instance | **Free** is OK for demo |
| Health check path | `/health` |

## 3. Env vars (on this bot web service)

| Key | Value |
|---|---|
| `WAGA_TELEGRAM_BOT_TOKEN` | BotFather token |
| `WAGA_TELEGRAM_DRY_RUN` | `false` |
| `WAGA_API_BASE_URL` | `https://waga-2h0w.onrender.com/api/v1` |
| `WAGA_TELEGRAM_MODE` | `webhook` |
| `WAGA_TELEGRAM_WEBHOOK_URL` | `https://<this-bot-service>.onrender.com` |
| `WAGA_TELEGRAM_REQUIRE_AGENT` | `true` |
| `WAGA_TELEGRAM_AGENT_INVITE_CODES` | `WAGA-ADDIS-01` |
| `WAGA_ADDIS_AI_API_KEY` | Addis key |
| `WAGA_ADDIS_AI_STT_URL` | `https://api.addisassistant.com/api/v2/stt` |
| `WAGA_ADDIS_AI_DEFAULT_LANG` | `am` |

`RENDER_EXTERNAL_URL` is set by Render automatically; if `WAGA_TELEGRAM_WEBHOOK_URL` is empty, the start script uses it.

## 4. Deploy

After deploy, logs should show:

`Webhook set to https://....onrender.com/telegram`

Open `https://<bot>.onrender.com/health` → should return `ok`.

## 5. Approval flow (no invite code required)

1. Guest applies in Telegram (`/apply`).
2. Admin approves in Swagger: `POST /admin/agent-applications/{id}/approve`.
3. API creates `is_agent=true` in the DB and (if configured) DMs the user in Telegram.
4. Agent opens the bot → `/start` or **Submit price** — bot syncs from API, no invite code.

For the approval DM, set the **same** BotFather token on the **API** web service:

| Key | Value |
|---|---|
| `WAGA_TELEGRAM_BOT_TOKEN` | same token as the bot service |

Invite codes (`/agent CODE`) remain an optional shortcut for people you onboard offline.

## 6. Important

- **Stop any local bot** (polling and webhook conflict).
- First message after sleep may be slow (cold start).
- Keep API (`waga-2h0w`) and bot as **two** web services.

## Local polling (dev)

```env
WAGA_TELEGRAM_MODE=polling
WAGA_TELEGRAM_DRY_RUN=false
WAGA_API_BASE_URL=https://waga-2h0w.onrender.com/api/v1
```

```bash
uv run waga-telegram-bot
```
