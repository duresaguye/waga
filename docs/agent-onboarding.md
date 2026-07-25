# Agent Onboarding — What We Ask & How Approval Works

Agents who earn score/money must be **known people**, not anonymous Telegram users.

---

## What is already done

| Done | Not done before this doc |
|---|---|
| Invite code `/agent CODE` (fast path) | Full application form |
| Allowlist by Telegram ID | Admin approve/reject applications |
| Score + birr redeem after agent exists | Collect phone / location on signup |

**New flow (build this):** Apply in bot → pending → admin reviews → approve → can submit.

Invite codes can stay as a **shortcut** after you already met someone offline.

---

## What to ask applicants

### Required (v1)

| Field | Why |
|---|---|
| **Full name** | Know who they are; payouts / trust |
| **Phone number** | Contact + future airtime/mobile money |
| **City** | Start: Addis Ababa only |
| **Preferred market** | Ehil Berenda / Atikilt Tera (or “either”) |
| **How often they can visit** | e.g. daily / few times a week / weekends |
| **Honest-reporting consent** | They agree to report real market prices only |
| **Telegram user id** | Auto from Telegram (not typed) |
| **Telegram username** | Auto if set (`@name`) |

### Nice to have (ask if easy)

| Field | Why |
|---|---|
| **Subcity / area** | e.g. Addis Ketema, Yeka — closer to market |
| **Languages** | Amharic / Afaan Oromo / English |
| **Short note** | How they heard about Waga / availability |

### Do **not** ask in v1

| Skip | Why |
|---|---|
| National ID / passport photos | Heavy privacy & storage |
| Bank account | Ask only when paying (redeem) |
| Exact home GPS | Not needed; privacy risk |
| Age / gender | Not required for the job |
| Employer details | Not needed |

---

## Approval flow

```text
Applicant opens bot → Apply to be agent
        │
        ▼
Fills: name, phone, city, market, visit frequency, consent
        │
        ▼
Status = pending  (cannot submit prices yet)
        │
        ▼
Admin reviews in API / dashboard
        │
   ┌────┴────┐
   ▼         ▼
Approve    Reject
   │         │
   ▼         ▼
is_agent    notify reason
= true      (optional)
   │
   ▼
Can /submit → earn score → redeem birr
```

Admin should check:
- Phone looks real (Ethiopia format)
- Market coverage still needed
- Person seems able to visit (not random spam)
- Ideally you already spoke to them (call / meet)

---

## Pitch-safe wording (bot)

> To become a Waga market agent, share your name, phone, city, and which market you can cover.  
> Our team reviews your application. After approval you can submit prices, earn score, and redeem rewards.

---

## API (to implement / implemented with this work)

| Method | Path | Who |
|---|---|---|
| POST | `/api/v1/agents/applications` | Bot / applicant |
| GET | `/api/v1/admin/agent-applications?status=pending` | Admin |
| POST | `/api/v1/admin/agent-applications/{id}/approve` | Admin |
| POST | `/api/v1/admin/agent-applications/{id}/reject` | Admin |
