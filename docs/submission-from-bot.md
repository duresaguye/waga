# Price Submit — What the Bot Collects

When an approved agent taps **Submit price**, the bot asks for these fields, then POSTs them to the API.

## Fields from the agent

| Step | What they provide | API field | Required |
|---|---|---|---|
| Consent | Agree to report honestly | `consent_version` (`contributor-v1`) | Yes |
| Market | Pick Merkato, Shola, … or **Other** | `market_code` | Yes |
| Other market name | Free text if Other | `market_label` | Yes if Other |
| Commodity | Teff / wheat / maize / onion / oil | `commodity_code` | Yes |
| Price | Number in ETB | `price` | Yes |
| Unit | From commodity (kg or liter) | `unit` | Yes (auto) |

## Filled automatically (not typed)

| Field | Source |
|---|---|
| `external_contributor_id` | `telegram:{telegram_user_id}` |
| `telegram_username` | Telegram `@username` if set |
| `client_submission_id` | New UUID per report |
| `input_mode` | `telegram` |
| `source` | `user` |

## API

```http
POST /api/v1/submissions
```

```json
{
  "client_submission_id": "uuid",
  "external_contributor_id": "telegram:123456789",
  "telegram_username": "optional",
  "market_code": "merkato",
  "market_label": null,
  "commodity_code": "teff_mixed",
  "price": 95.5,
  "unit": "kg",
  "consent_version": "contributor-v1",
  "input_mode": "telegram",
  "source": "user"
}
```

**Result:** submission stored as `pending` review + agent score `+1`.

Seed catalogue first: `uv run waga-seed-phase1`
