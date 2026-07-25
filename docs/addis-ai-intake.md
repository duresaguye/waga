# Other market + Addis AI intake

## Typing Other in Amharic (works now)

When the agent picks **Other**:
- Type the market name in Amharic (Fidel), Afaan Oromo, or English
- Or send a **voice note**

Stored as `market_label` / `raw_text` (`other_market:...`) with `market_code=other`.

## Voice flow (wired in Telegram bot)

```text
Other market
  -> type name  OR  voice note
  -> Addis AI STT (am / om)
  -> confirm: Use this / Record again / Type instead
  -> continue submit or apply
```

### Env

```env
WAGA_ADDIS_AI_API_KEY=sk_...
WAGA_ADDIS_AI_STT_URL=https://api.addisassistant.com/api/v2/stt
WAGA_ADDIS_AI_DEFAULT_LANG=am
```

Optional: install `ffmpeg` so Telegram `.ogg` voice notes convert to WAV (recommended).

### API

`POST https://api.addisassistant.com/api/v2/stt`  
Docs: https://docs.addisassistant.com/docs/capabilities/speech-to-text

### Code

- `telegram_bot/services/addis_stt.py`
- `telegram_bot/services/voice_intake.py`
- Submit / Apply handlers: Other market voice + confirm

## Safety

STT output is a **draft**. Agent must tap **Use this name** before it is saved.
AI does not invent prices.
