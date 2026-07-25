# Waga Telegram Bot (Phase 1)

Approved **market agent** intake for the Addis Ababa pilot.  
Guests apply (or use an invite code); only approved agents submit prices.

Flow: apply / invite → admin approve → submit market prices → score → redeem.

## What is in this package

| Piece | Role |
|---|---|
| `telegram_bot/` | Separate process from the FastAPI API |
| Button flow | Consent → market → commodity → price → confirm |
| Phase 1 markets | Merkato, Shola, Ehil Berenda, Atikilt Tera, Piazza, Saris, Akaki, Asko, Kera, **Other (type name)** |
| Phase 1 commodities | Teff (mixed), wheat, maize, onion, cooking oil |
| Dry-run mode | Logs payload until `/submissions` API exists |

## Not in Phase 1

- Addis AI speech-to-text
- Photos
- Free-text / LLM parsing
- Real mobile-money payouts (v1 = **score + ban** only; money later)
- Mobile app

## Reputation & redeem

Full flow: **`docs/agent-score.md`**

- Agents earn score from market reports (+1 pending → +10 if accepted; −15 if flagged)
- `/score` or **My score** shows balance
- `/redeem` or **Redeem score** at 50+ points (reward request)
- Guests: join via invite only
- Banned after 3 flagged reports (no submit / redeem)

## Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy the token.
2. Add to `.env`:

```env
WAGA_TELEGRAM_BOT_TOKEN=123456:ABC...
WAGA_TELEGRAM_DRY_RUN=true
WAGA_API_BASE_URL=http://127.0.0.1:8000/api/v1
WAGA_TELEGRAM_REQUIRE_AGENT=true
WAGA_TELEGRAM_AGENT_IDS=
WAGA_TELEGRAM_AGENT_INVITE_CODES=WAGA-ADDIS-01
```

3. Onboard a person offline, then either:
   - add their Telegram numeric user ID to `WAGA_TELEGRAM_AGENT_IDS`, or
   - give them an invite code → they send `/agent WAGA-ADDIS-01`

4. Install deps and run (re-sync after `pyproject.toml` changes so scripts install):

```bash
uv sync
uv run waga-telegram-bot
```

Or:

```bash
uv run python -m telegram_bot
```

If you see `Failed to spawn: waga-telegram-bot` / `program not found`, run `uv sync` again so the project package (and console scripts) are installed into `.venv`.

## Flow

1. Guest menu: **Enter invite code** · **Help**
2. `/agent CODE` activates agent
3. Agent menu: **Submit price** · **My score** · **Redeem score** · **Help**
4. Submit flow: consent → market → commodity → price → confirm
5. Commands: `/start` `/submit` `/agent` `/score` `/redeem` `/help` `/cancel`

### Reputation (bot-side dry-run)

| Event | Points (local until API owns it) |
|---|---|
| Submit (pending) | +1 |
| Accepted (when review API wires in) | +10 path |
| Flagged | −15 |
| Score collapse / 3+ flags | Ban — bot blocks submit |

## Next wiring steps

1. Add `input_mode=telegram` to backend enums + migration
2. Implement `POST /api/v1/submissions`
3. Set `WAGA_TELEGRAM_DRY_RUN=false`
4. Later: optional Addis AI STT for voice notes with confirm step
