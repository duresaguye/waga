# Agent Apply Flow (Telegram + Web App)

Shared apply experience for becoming a Waga market agent.  
**Same fields and same backend API** for:

- Telegram bot (**Apply to be agent** / `/apply`)
- Frontend / web app (apply form page)

Backend endpoint (both clients):

```http
POST /api/v1/agents/applications
```

Admin review (backend / admin UI later):

```http
GET  /api/v1/admin/agent-applications?status=pending
POST /api/v1/admin/agent-applications/{id}/approve
POST /api/v1/admin/agent-applications/{id}/reject
```

Full field policy: `docs/agent-onboarding.md`

---

## High-level flow

```text
User opens Telegram bot  OR  Web app
        │
        ▼
Taps / clicks  "Apply to be agent"
        │
        ▼
Fills application form (steps below)
        │
        ▼
Submits → status = pending
        │
        ▼
Cannot submit prices yet
        │
        ▼
Admin reviews
   ┌────┴────┐
   ▼         ▼
Approve    Reject
   │         │
   ▼         ▼
is_agent   Notify (optional)
   │
   ▼
Can submit market prices → earn score → redeem birr
```

Invite code (`/agent CODE`) remains an optional shortcut if the team already onboarded someone offline.

**Do not show applicants** anti-fraud / “why we gate agents” copy (e.g. inventing prices from home).  
User-facing copy stays simple: apply → wait for approval → submit prices → earn score → redeem.

---

## Step-by-step: what they fill when they click Apply

| Step | UI prompt | Field | Required | Notes |
|---|---|---|---|---|
| 1 | Full name | `full_name` | Yes | Real name for trust / payouts |
| 2 | Phone number | `phone_number` | Yes | e.g. `0911234567` or `+251911234567` |
| 3 | City | `city` | Yes | Default / expected: **Addis Ababa** |
| 4 | Subcity / area | `subcity` | No | e.g. Addis Ketema, Yeka — or skip |
| 5 | Preferred market | `preferred_market_code` | Yes | Select from list (below) |
| 5b | If **Other** | market name text | Yes if Other | Stored in `notes` or future `market_label` |
| 6 | Visit frequency | `visit_frequency` | Yes | daily / few_times_week / weekends |
| 7 | Languages | `languages` | No | e.g. Amharic, English — or skip |
| 8 | Honest reporting consent | `consent_honest_reporting` | Yes | Must agree |
| 9 | Confirm & submit | — | Yes | Review summary, then send |

**Auto-filled (not typed by user):**

| Field | Source |
|---|---|
| `telegram_id` | Telegram user id (bot only) |
| `telegram_username` | Telegram `@username` if set (bot only) |

**Web app:** collect the same form fields. For identity, use logged-in user id / phone OTP later; until auth exists, web can still POST the form and store `telegram_id` as optional/null if you extend the schema — **v1 bot requires telegram_id**. For web v1, either:

- ask for Telegram username/id to link, or  
- create web applications with phone as primary key (follow-up schema change).

Recommended for shared v1: web form also asks **Telegram username** so admin can link the same person.

---

## Market select options (shared list)

Show these buttons / dropdown options:

1. Merkato  
2. Shola Gebeya  
3. Ehil Berenda  
4. Atikilt Tera  
5. Piazza  
6. Saris  
7. Akaki  
8. Asko  
9. Kera  
10. **Other (type name)** → free-text market name  
11. (Optional) Either / flexible — apply flow only  

Codes used in API:

| Label | `preferred_market_code` |
|---|---|
| Merkato | `merkato` |
| Shola Gebeya | `shola` |
| Ehil Berenda | `ehil_berenda` |
| Atikilt Tera | `atikilt_tera` |
| Piazza | `piazza` |
| Saris | `saris` |
| Akaki | `akaki` |
| Asko | `asko` |
| Kera | `kera` |
| Other | `other` (+ typed name) |
| Either / flexible | `either` |

---

## Request body (both Telegram and web)

```json
{
  "telegram_id": "123456789",
  "telegram_username": "optional_username",
  "full_name": "Abebe Kebede",
  "phone_number": "+251911234567",
  "city": "Addis Ababa",
  "subcity": "Yeka",
  "preferred_market_code": "merkato",
  "visit_frequency": "few_times_week",
  "languages": "Amharic, English",
  "notes": null,
  "consent_honest_reporting": true
}
```

If market is Other:

```json
{
  "preferred_market_code": "other",
  "notes": "Autobis Tera"
}
```

---

## After submit — user-facing copy

**Success (pending):**
> Application submitted. Status: pending review.  
> You cannot submit prices until the Waga team approves you.

**Already pending:**
> You already have an application waiting for review.

**Already agent:**
> You are already an approved agent. Use Submit price.

**Rejected (when you notify them):**
> Your application was not approved. Contact the Waga team if you have questions.

---

## Frontend (web app) checklist

Build one **Apply** page that:

1. Starts when user clicks **Apply to be agent**  
2. Uses the same step order / fields as the table above  
3. Market dropdown = shared list + Other text input  
4. POSTs to `/api/v1/agents/applications`  
5. Shows pending success screen  
6. Does **not** unlock price submit until admin approved  

Optional later:
- “My application status” page  
- Notify on approve (SMS / Telegram / email)

---

## Admin after apply

1. Open pending applications  
2. Check name, phone, city, market, visit frequency  
3. **Approve** → contributor `is_agent=true` (can submit + score)  
4. **Reject** → optional `review_note`

---

## Out of scope for this form (for now)

- National ID upload  
- Bank account  
- Home GPS  
- National (non-Addis) markets as primary list  

Keep Addis well-known markets + Other.
