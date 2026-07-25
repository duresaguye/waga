# Waga Index — Admin Dashboard

## Screen Inventory by Phase

---

## Summary Count

```
┌─────────────────────────────────────────────────────┐
│  ADMIN DASHBOARD — SCREEN INVENTORY                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Phase 1   Authentication             2 screens     │
│  Phase 2   Overview & Monitoring      3 screens     │
│  Phase 3   Commodity Management       4 screens     │
│  Phase 4   Market Management          2 screens     │
│  Phase 5   Contributor Management     3 screens     │
│  Phase 6   Data & Validation          3 screens     │
│  Phase 7   System & Settings          3 screens     │
│                                                     │
│  Total                               20 screens     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Design Language

```
┌─────────────────────────────────────────────────────┐
│  TOKENS                                             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Background      #F8F7F4   warm off-white           │
│  Surface         #FFFFFF   cards, panels            │
│  Surface Alt     #F1EFE9   sidebar, section fills   │
│  Border          #E8E4DC   all dividers             │
│  Text Primary    #1A1814   headings, values         │
│  Text Secondary  #6B6560   body, labels             │
│  Text Tertiary   #9C9590   timestamps, meta         │
│                                                     │
│  Accent Green    #1D7A4E   primary actions, live    │
│  Accent Light    #E8F5EE   green tint backgrounds   │
│  Amber           #C47D1A   warnings, insufficient   │
│  Amber Light     #FEF3E2   amber tint backgrounds   │
│  Danger          #DC2626   destructive actions      │
│  Danger Light    #FEF2F2   danger tint backgrounds  │
│                                                     │
│  Type            Inter — all UI                     │
│  Display         Clash Display — numbers, headlines │
│  Amharic         Noto Sans Ethiopic                 │
│                                                     │
│  Card radius     16px                               │
│  Button radius   10px                               │
│  Badge radius    999px pill                         │
│  Shadow          0 1px 4px rgba(0,0,0,0.06)        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Shared Layout — All Screens

```
┌─────────────────────────────────────────────────────────────────────┐
│  🌿 WAGA INDEX  Admin                          Admin User ▾  Logout │
│  ─────────────────────────────────────────────────────────────────  │
├──────────────────┬──────────────────────────────────────────────────┤
│                  │                                                  │
│  OVERVIEW        │                                                  │
│  ─────────────   │                                                  │
│  📊 Dashboard    │                                                  │
│  📡 Live Feed    │                                                  │
│  📈 Coverage     │           SCREEN CONTENT AREA                   │
│                  │                                                  │
│  CATALOGUE       │                                                  │
│  ─────────────   │                                                  │
│  🏷  Categories  │                                                  │
│  📦 Commodities  │                                                  │
│  🔤 Synonyms     │                                                  │
│  📋 Unparsed     │                                                  │
│                  │                                                  │
│  MARKETS         │                                                  │
│  ─────────────   │                                                  │
│  📍 Markets      │                                                  │
│  🗺  Coverage Map │                                                  │
│                  │                                                  │
│  CONTRIBUTORS    │                                                  │
│  ─────────────   │                                                  │
│  👥 Contributors │                                                  │
│  🎯 Agents       │                                                  │
│  🚫 Rate Limits  │                                                  │
│                  │                                                  │
│  DATA            │                                                  │
│  ─────────────   │                                                  │
│  ✅ Validation   │                                                  │
│  📤 Export       │                                                  │
│  🗄  Submissions  │                                                  │
│                  │                                                  │
│  SYSTEM          │                                                  │
│  ─────────────   │                                                  │
│  👤 Users        │                                                  │
│  ⚙  Settings     │                                                  │
│  📜 Audit Log    │                                                  │
│                  │                                                  │
└──────────────────┴──────────────────────────────────────────────────┘

SIDEBAR CONSTANTS
─────────────────
Width              240px fixed
Background         Surface Alt #F1EFE9
Groups             6 labelled groups with dividers
Active item        accent green left border 3px
                   accent light background
Icon + label       every nav item
Top bar            64px, white, border-bottom, sticky
Content area       flex-1, #F8F7F4, padding 32px
```

---

# Phase 1 — Authentication

**2 screens**

```
┌──────┬──────────────────────────────────┬───────────────────────┐
│  #   │  Screen Name                     │  Actor                │
├──────┼──────────────────────────────────┼───────────────────────┤
│  1.1 │  Login                           │  Admin + Evaluator    │
│  1.2 │  Set Password (Invite Accept)    │  Admin + Evaluator    │
└──────┴──────────────────────────────────┴───────────────────────┘
```

---

## Screen 1.1 — Login

```
PURPOSE
───────
Secure entry point. Invite-only.
No self-registration. No forgot password in MVP.

┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                       🌿 WAGA INDEX                            │
│                       Admin Dashboard                          │
│                                                                 │
│            ┌────────────────────────────────────┐              │
│            │                                    │              │
│            │  Sign in                           │              │
│            │  ─────────────────────────────     │              │
│            │                                    │              │
│            │  Email                             │              │
│            │  ┌──────────────────────────────┐  │              │
│            │  │ you@organisation.org         │  │              │
│            │  └──────────────────────────────┘  │              │
│            │                                    │              │
│            │  Password                          │              │
│            │  ┌──────────────────────────────┐  │              │
│            │  │ ••••••••••••              👁 │  │              │
│            │  └──────────────────────────────┘  │              │
│            │                                    │              │
│            │  ┌──────────────────────────────┐  │              │
│            │  │          Sign in             │  │              │
│            │  └──────────────────────────────┘  │              │
│            │  (accent green, full width)        │              │
│            │                                    │              │
│            │  No account? Contact your          │              │
│            │  Waga Index administrator.         │              │
│            │  (muted 13px)                      │              │
│            │                                    │              │
│            └────────────────────────────────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

ERROR STATE
───────────
┌──────────────────────────────────────────────┐
│  ⚠  Email or password is incorrect.         │
│     (amber banner above form)               │
└──────────────────────────────────────────────┘

ELEMENTS
────────
Card              400px max-width, centered, shadow-sm
Email             type=email
Password          show/hide toggle 👁
Button            accent green, full width
Error             single message — no field hints (security)
No-account note   muted — no registration link ever
```

---

## Screen 1.2 — Set Password

```
PURPOSE
───────
Invite link acceptance. One-time password setup.
Admin creates all accounts — no self-serve.

┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                       🌿 WAGA INDEX                            │
│                       Admin Dashboard                          │
│                                                                 │
│            ┌────────────────────────────────────┐              │
│            │                                    │              │
│            │  Set your password                 │              │
│            │  ─────────────────────────────     │              │
│            │                                    │              │
│            │  ┌──────────────────────────────┐  │              │
│            │  │ Evaluator                    │  │              │
│            │  └──────────────────────────────┘  │              │
│            │  (role pill — muted bg, read only) │              │
│            │                                    │              │
│            │  Account                           │              │
│            │  ┌──────────────────────────────┐  │              │
│            │  │ tigist@wfp.org  (read only)  │  │              │
│            │  └──────────────────────────────┘  │              │
│            │                                    │              │
│            │  New password                      │              │
│            │  ┌──────────────────────────────┐  │              │
│            │  │                           👁 │  │              │
│            │  └──────────────────────────────┘  │              │
│            │                                    │              │
│            │  Confirm password                  │              │
│            │  ┌──────────────────────────────┐  │              │
│            │  │                           👁 │  │              │
│            │  └──────────────────────────────┘  │              │
│            │                                    │              │
│            │  ☐  I acknowledge that submitted   │              │
│            │     data may be published and      │              │
│            │     used commercially.             │              │
│            │                                    │              │
│            │  ┌──────────────────────────────┐  │              │
│            │  │      Activate account        │  │              │
│            │  └──────────────────────────────┘  │              │
│            │  (disabled until checkbox ticked)  │              │
│            │                                    │              │
│            └────────────────────────────────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

EXPIRED STATE
─────────────
┌──────────────────────────────────────┐
│  🌿 WAGA INDEX                       │
│                                      │
│  This invite link has expired.       │
│  Links are valid for 24 hours.       │
│  Contact your administrator.         │
└──────────────────────────────────────┘
```

---

# Phase 2 — Overview & Monitoring

**3 screens**

```
┌──────┬──────────────────────────────────┬───────────────────────┐
│  #   │  Screen Name                     │  Actor                │
├──────┼──────────────────────────────────┼───────────────────────┤
│  2.1 │  Dashboard                       │  Admin + Evaluator    │
│  2.2 │  Live Feed                       │  Admin + Evaluator    │
│  2.3 │  Coverage Panel                  │  Admin + Evaluator    │
└──────┴──────────────────────────────────┴───────────────────────┘
```

---

## Screen 2.1 — Dashboard

```
PURPOSE
───────
First screen after login.
System health at a glance.
Key numbers, recent activity, cells at threshold.

┌──────────────────┬──────────────────────────────────────────────────┐
│  📊 Dashboard ←  │  Dashboard                    ● Live             │
│                  │                                                  │
│                  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│                  │  │  6 / 10  │ │    34    │ │   81%    │        │
│                  │  │  Cells   │ │  Active  │ │  Pass    │        │
│                  │  │  Live    │ │  Contrib │ │  Rate    │        │
│                  │  └──────────┘ └──────────┘ └──────────┘        │
│                  │                                                  │
│                  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│                  │  │   89     │ │  $0.004  │ │   6      │        │
│                  │  │  Submiss │ │  Cost /  │ │  Flagged │        │
│                  │  │  72h     │ │  Valid   │ │  Today   │        │
│                  │  └──────────┘ └──────────┘ └──────────┘        │
│                  │  (6 stat cards, 3-col grid)                     │
│                  │                                                  │
│                  │  Cell Status Grid                                │
│                  │  ────────────────────────────────────────────   │
│                  │  ┌──────────────────┬──────────┬──────────┐    │
│                  │  │                  │ Merkato  │ Shola    │    │
│                  │  ├──────────────────┼──────────┼──────────┤    │
│                  │  │ Tomato / ቲማቲም    │ ✅  n=12 │ ⚠   n=1 │    │
│                  │  │ Onion  / ሽንኩርት   │ ✅  n=8  │ ✅  n=4 │    │
│                  │  │ Potato / ድንች     │ ✅  n=6  │ ⚠   n=2 │    │
│                  │  │ Teff   / ጤፍ      │ ✅  n=5  │ ⚠   n=0 │    │
│                  │  │ Oil    / ዘይት     │ ✅  n=7  │ ⚠   n=1 │    │
│                  │  └──────────────────┴──────────┴──────────┘    │
│                  │  ✅ Published  ·  ⚠ Insufficient               │
│                  │                                                  │
│                  │  Source Mix                                      │
│                  │  ────────────────────────────────────────────   │
│                  │  ████████████████░░░░░░  71% Contributors       │
│                  │  ████████░░░░░░░░░░░░░░  29% Field Agents       │
│                  │                                                  │
│                  │  Recent Activity                                 │
│                  │  ────────────────────────────────────────────   │
│                  │  14:32  Tomato · Merkato · 86/kg  ✅  user      │
│                  │  14:28  Tomato · Merkato · 200/kg ⚠  flagged   │
│                  │  14:21  Onion  · Shola   · 45/kg  ✅  agent     │
│                  │                           View all →            │
└──────────────────┴──────────────────────────────────────────────────┘

STAT CARDS
──────────
Row 1   Cells at threshold / Activated contributors /
        Validation pass rate
Row 2   Submissions (72h) / Cost per validated obs /
        Flagged today

All 6 cards      white, shadow-sm, 16px radius
Number           Clash Display 32px
Label            Inter 13px muted below
Subtext          context label 11px tertiary

Cell grid        commodity rows × market columns
                 ✅ green / ⚠ amber + n count

Activity feed    3 most recent — link to Live Feed
```

---

## Screen 2.2 — Live Feed

```
PURPOSE
───────
Real-time stream of all submissions.
Flagged entries visible with rule and reason.
Primary monitoring tool during demonstration.

┌──────────────────┬──────────────────────────────────────────────────┐
│  📡 Live Feed ←  │  Live Feed                        ● updating     │
│                  │                                                  │
│                  │  Filter  [ All ▾ ]  Source [ All ▾ ]            │
│                  │  Market  [ All ▾ ]  Commodity [ All ▾ ]         │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │                                          │   │
│                  │  │  14:32  Tomato  Merkato  86/kg           │   │
│                  │  │         user · ✅ Accepted               │   │
│                  │  │                                          │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │                                          │   │
│                  │  │  14:28  Tomato  Merkato  200/kg          │   │
│                  │  │         user · ⚠ Flagged                 │   │
│                  │  │         ▼ expanded                       │   │
│                  │  │                                          │   │
│                  │  │  Rule      R2_IQR_OUTLIER                │   │
│                  │  │  Reason    Outside 2.5× IQR of           │   │
│                  │  │            trailing 7-day window         │   │
│                  │  │  Ref range 75 – 95 birr/kg               │   │
│                  │  │  Action    Contributor confirmed.        │   │
│                  │  │            Excluded from index.          │   │
│                  │  │                                          │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  14:21  Onion   Shola   45/kg            │   │
│                  │  │         agent · ✅ Accepted              │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  14:15  Teff    Merkato  580/kg          │   │
│                  │  │         user · ✅ Accepted               │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  14:02  Potato  Merkato  unparsed        │   │
│                  │  │         user · 🔵 Pending               │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │                                                  │
│                  │  Showing 50 most recent.                        │
│                  │  Flagged entries visible — never hidden.        │
└──────────────────┴──────────────────────────────────────────────────┘

ROW STATES
──────────
Accepted          white row, ✅ green badge
Flagged           amber left border 4px, ⚠ amber badge
                  click to expand — shows rule + reason
Pending           blue badge 🔵 — unparsed, awaiting synonym
Rejected          red badge — rate limit hit

FILTER BAR
──────────
Status            All / Accepted / Flagged / Pending / Rejected
Source            All / User / Agent / Seed / Scraped
Market            All / individual markets
Commodity         All / individual commodities

Each row          time / commodity / market / price+unit /
                  source badge / status badge
Read only         no edit, no delete, no approve
```

---

## Screen 2.3 — Coverage Panel

```
PURPOSE
───────
System-wide coverage health.
Which cells are at threshold, which are not.
The demonstration centrepiece.

┌──────────────────┬──────────────────────────────────────────────────┐
│  📈 Coverage ←   │  Coverage                     ● Live             │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  Rolling window   72 hours               │   │
│                  │  │  Threshold        3 validated submissions │   │
│                  │  │  Last updated     2 minutes ago          │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │                                                  │
│                  │  Market selector                                 │
│                  │  [ All Markets ▾ ]                              │
│                  │                                                  │
│                  │  Commodity       Merkato      Shola             │
│                  │  ─────────────────────────────────────────────  │
│                  │  Tomato / ቲማቲም   ✅ 12 rpts   ⚠  1 rpt        │
│                  │  Onion  / ሽንኩርት  ✅  8 rpts   ✅ 4 rpts        │
│                  │  Potato / ድንች    ✅  6 rpts   ⚠  2 rpts        │
│                  │  Teff   / ጤፍ     ✅  5 rpts   ⚠  0 rpts        │
│                  │  Oil    / ዘይት    ✅  7 rpts   ⚠  1 rpt         │
│                  │                                                  │
│                  │  ✅ At threshold (3+)  ⚠ Insufficient (<3)      │
│                  │                                                  │
│                  │  Summary                                         │
│                  │  ──────────────────────────────────────────     │
│                  │  At threshold    6 of 10 cells                  │
│                  │  Insufficient    4 cells                        │
│                  │  Contributors    34 activated                   │
│                  │  Pass rate       81%                            │
│                  │  Source mix                                      │
│                  │  ████████████░░░░  71% Contributors             │
│                  │  ████░░░░░░░░░░░░  29% Field Agents             │
└──────────────────┴──────────────────────────────────────────────────┘
```

---

# Phase 3 — Commodity Management

**4 screens**

```
┌──────┬──────────────────────────────────┬───────────────────────┐
│  #   │  Screen Name                     │  Actor                │
├──────┼──────────────────────────────────┼───────────────────────┤
│  3.1 │  Category List                   │  Admin                │
│  3.2 │  Commodity List                  │  Admin                │
│  3.3 │  Synonym Table                   │  Admin                │
│  3.4 │  Unparsed Queue                  │  Admin                │
└──────┴──────────────────────────────────┴───────────────────────┘
```

---

## Screen 3.1 — Category List

```
PURPOSE
───────
Manage commodity categories.
Activate or deactivate categories.
See live status and commodity count per category.

┌──────────────────┬──────────────────────────────────────────────────┐
│  🏷 Categories ← │  Categories                                      │
│                  │                                              [+ Add]│
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  Icon  Name             Code      Status  │   │
│                  │  │  ────────────────────────────────────── │   │
│                  │  │  🥬    Food & Groceries  food_gro  ● Live│   │
│                  │  │        ምግብና ግሮሰሪ         12 items       │   │
│                  │  │                                    [Edit] │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  📱    Electronics       electronics  ○   │   │
│                  │  │        ኤሌክትሮኒክስ          8 items         │   │
│                  │  │                          Coming soon      │   │
│                  │  │                                    [Edit] │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  👗    Clothing          clothing    ○    │   │
│                  │  │        ልብስና ጨርቃጨርቅ       10 items        │   │
│                  │  │                          Coming soon      │   │
│                  │  │                                    [Edit] │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  🏠    Household          household   ○   │   │
│                  │  │        የቤት እቃዎች           10 items        │   │
│                  │  │                          Coming soon      │   │
│                  │  │                                    [Edit] │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  💊    Health             health      ○   │   │
│                  │  │        ጤናና ፋርማሲ           10 items        │   │
│                  │  │                          Coming soon      │   │
│                  │  │                                    [Edit] │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  🚌    Transport          transport   ○   │   │
│                  │  │        ትራንስፖርት             5 items         │   │
│                  │  │                          Coming soon      │   │
│                  │  │                                    [Edit] │   │
│                  │  └──────────────────────────────────────────┘   │
└──────────────────┴──────────────────────────────────────────────────┘

ADD / EDIT MODAL
────────────────
┌──────────────────────────────────────┐
│  Edit Category                       │
│  ─────────────                      │
│                                      │
│  Icon (emoji)     ┌──────┐           │
│                   │  🥬  │           │
│                   └──────┘           │
│                                      │
│  Name (English)   ┌──────────────┐   │
│                   │              │   │
│                   └──────────────┘   │
│                                      │
│  Name (Amharic)   ┌──────────────┐   │
│                   │              │   │
│                   └──────────────┘   │
│                                      │
│  Status           ◉ Live  ○ Coming   │
│                                      │
│  [ Save ]  [ Cancel ]                │
└──────────────────────────────────────┘
```

---

## Screen 3.2 — Commodity List

```
PURPOSE
───────
All commodities across all categories.
Add, edit, activate, deactivate.
Filter by category.

┌──────────────────┬──────────────────────────────────────────────────┐
│  📦 Commodities← │  Commodities                              [+ Add] │
│                  │                                                  │
│                  │  [ All Categories ▾ ]  [ Search... 🔍 ]         │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  Name          Category  Unit   Conv  St  │   │
│                  │  │  ────────────────────────────────────── │   │
│                  │  │  Tomato        🥬 Food    kg     ✅   ●  │   │
│                  │  │  ቲማቲም                                    │   │
│                  │  │                              [Edit][Off]  │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  Onion         🥬 Food    kg     ✅   ●  │   │
│                  │  │  ሽንኩርት                                   │   │
│                  │  │                              [Edit][Off]  │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  Potato        🥬 Food    kg     ✅   ●  │   │
│                  │  │  ድንች                                     │   │
│                  │  │                              [Edit][Off]  │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  Teff          🥬 Food    kg     ✅   ●  │   │
│                  │  │  ጤፍ                                      │   │
│                  │  │                              [Edit][Off]  │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  Phone charger 📱 Elec    piece  ✗    ○  │   │
│                  │  │  ሞባይል ቻርጀር                               │   │
│                  │  │                              [Edit][On]   │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │                                                  │
│                  │  Conv = allow_conversion                         │
│                  │  ✅ converts to canonical unit                   │
│                  │  ✗  unit recorded as observed                   │
│                  │  St = Status ● Live  ○ Inactive                 │
└──────────────────┴──────────────────────────────────────────────────┘

ADD / EDIT MODAL
────────────────
┌──────────────────────────────────────┐
│  Add Commodity                       │
│  ─────────────                      │
│                                      │
│  Category         [ Food ▾ ]         │
│                                      │
│  Name (English)   ┌──────────────┐   │
│                   │              │   │
│                   └──────────────┘   │
│                                      │
│  Name (Amharic)   ┌──────────────┐   │
│                   │              │   │
│                   └──────────────┘   │
│                                      │
│  Code             ┌──────────────┐   │
│                   │ snake_case   │   │
│                   └──────────────┘   │
│                                      │
│  Canonical unit   [ kg ▾ ]           │
│                                      │
│  Allow conversion ◉ Yes  ○ No        │
│                                      │
│  Price hint low   ┌──────┐  birr     │
│                   │      │           │
│                   └──────┘           │
│  Price hint high  ┌──────┐  birr     │
│                   │      │           │
│                   └──────┘           │
│                                      │
│  [ Save ]  [ Cancel ]                │
└──────────────────────────────────────┘
```

---

## Screen 3.3 — Synonym Table

```
PURPOSE
───────
Manage commodity synonym mappings.
The highest-leverage table in the system.
Directly determines parse rate.

┌──────────────────┬──────────────────────────────────────────────────┐
│  🔤 Synonyms ←   │  Synonym Table                            [+ Add] │
│                  │                                                  │
│                  │  [ All Commodities ▾ ]  [ All Scripts ▾ ]       │
│                  │                                                  │
│                  │  Unparsed queue  ● 6 pending   [ View → ]       │
│                  │  (amber banner — prominent link)                 │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  Surface typed   Commodity   Script   Act│   │
│                  │  │  ──────────────────────────────────────  │   │
│                  │  │  ቲማቲም            Tomato     Ethiopic  ✕  │   │
│                  │  │  timatim          Tomato     Latin     ✕  │   │
│                  │  │  timatem          Tomato     Latin     ✕  │   │
│                  │  │  tmatm            Tomato     Latin     ✕  │   │
│                  │  │  ሽንኩርት           Onion      Ethiopic  ✕  │   │
│                  │  │  shinkurt         Onion      Latin     ✕  │   │
│                  │  │  ድንች             Potato     Ethiopic  ✕  │   │
│                  │  │  dinch            Potato     Latin     ✕  │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │                                                  │
│                  │  Parse rate (last 24h)                          │
│                  │  ████████████████░░░░  82% resolved             │
│                  │  Target ≥ 90%                                   │
│                  │                                                  │
│                  │  Additions take effect on next submission.      │
│                  │  Existing unresolved submissions are not        │
│                  │  retroactively re-parsed.                       │
└──────────────────┴──────────────────────────────────────────────────┘

ADD SYNONYM MODAL
─────────────────
┌──────────────────────────────────────┐
│  Add Synonym                         │
│  ────────────                       │
│                                      │
│  Commodity        [ Tomato ▾ ]       │
│                                      │
│  Surface typed    ┌──────────────┐   │
│  (as contributor  │              │   │
│   wrote it)       └──────────────┘   │
│                                      │
│  Script           ◉ Ethiopic         │
│                   ○ Latin            │
│                   ○ English          │
│                                      │
│  [ Add ]  [ Cancel ]                 │
└──────────────────────────────────────┘

PARSE RATE BAR
──────────────
Progress bar        full width
Filled segment      % of submissions resolved
                    without LLM in last 24h
Target line         at 90% — vertical marker
Label               percentage + "resolved"
Below threshold     bar turns amber if < 90%
```

---

## Screen 3.4 — Unparsed Queue

```
PURPOSE
───────
Review submissions that could not be parsed.
Add synonyms directly from this screen.
The feedback loop that improves the synonym table.

┌──────────────────┬──────────────────────────────────────────────────┐
│  📋 Unparsed ←   │  Unparsed Queue                    6 pending     │
│                  │                                                  │
│                  │  These submissions could not be parsed.          │
│                  │  They are stored. Add synonyms to resolve        │
│                  │  future matches. Nothing is discarded.           │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  Time   Raw text        Suggestion       │   │
│                  │  │  ────────────────────────────────────── │   │
│                  │  │                                          │   │
│                  │  │  14:32  "tmatem 85"     Tomato          │   │
│                  │  │         fuzzy match · 87% confidence    │   │
│                  │  │         [Add as synonym]  [Unresolvable] │   │
│                  │  │                                          │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  13:55  "ye ቲማቲም kilo"  Tomato          │   │
│                  │  │         partial match                    │   │
│                  │  │         [Add as synonym]  [Unresolvable] │   │
│                  │  │                                          │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  13:20  "berbere 120"    No match        │   │
│                  │  │         Outside commodity basket         │   │
│                  │  │                          [Unresolvable]  │   │
│                  │  │                                          │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  12:44  "ዘይት ሊትር 95"    Oil             │   │
│                  │  │         fuzzy match · 91% confidence    │   │
│                  │  │         [Add as synonym]  [Unresolvable] │   │
│                  │  │                                          │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │                                                  │
│                  │  "Add as synonym" opens the synonym modal        │
│                  │  pre-populated with the surface and suggestion.  │
│                  │  "Unresolvable" removes from queue — retained   │
│                  │  in database with reason.                        │
└──────────────────┴──────────────────────────────────────────────────┘

ROW ELEMENTS
────────────
Time              when submission was received
Raw text          exactly as submitted, quoted
Suggestion        fuzzy match result + confidence %
                  "No match" if nothing found
Add as synonym    opens synonym modal pre-populated
                  available when suggestion exists
Unresolvable      requires confirmation click
                  logs reason to database
                  removes from this queue only
Nav badge         count shown on sidebar nav item
                  clears as queue empties
```

---

# Phase 4 — Market Management

**2 screens**

```
┌──────┬──────────────────────────────────┬───────────────────────┐
│  #   │  Screen Name                     │  Actor                │
├──────┼──────────────────────────────────┼───────────────────────┤
│  4.1 │  Market List                     │  Admin                │
│  4.2 │  Coverage Map                    │  Admin + Evaluator    │
└──────┴──────────────────────────────────┴───────────────────────┘
```

---

## Screen 4.1 — Market List

```
PURPOSE
───────
Add and manage markets.
Activate or deactivate.
Deactivation does not delete — submissions retain reference.

┌──────────────────┬──────────────────────────────────────────────────┐
│  📍 Markets ←    │  Markets                                  [+ Add] │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  Code      Name          Status  Actions  │   │
│                  │  │  ──────────────────────────────────────  │   │
│                  │  │  merkato   Merkato       ● Live  [Edit]   │   │
│                  │  │            መርካቶ                  [Off]    │   │
│                  │  │            Lat 9.0054                     │   │
│                  │  │            Lon 38.7378                    │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  shola     Shola         ● Live  [Edit]   │   │
│                  │  │            ሾላ                    [Off]    │   │
│                  │  │            Lat 9.0167                     │   │
│                  │  │            Lon 38.7500                    │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │                                                  │
│                  │  Deactivating a market does not delete it.      │
│                  │  Existing submissions retain their market       │
│                  │  reference. All changes logged to audit trail.  │
└──────────────────┴──────────────────────────────────────────────────┘

ADD / EDIT MODAL
────────────────
┌──────────────────────────────────────┐
│  Add Market                          │
│  ──────────                         │
│                                      │
│  Code           ┌──────────────┐     │
│  (snake_case)   │              │     │
│                 └──────────────┘     │
│                                      │
│  Name (English) ┌──────────────┐     │
│                 │              │     │
│                 └──────────────┘     │
│                                      │
│  Name (Amharic) ┌──────────────┐     │
│                 │              │     │
│                 └──────────────┘     │
│                                      │
│  Latitude       ┌──────────────┐     │
│                 │              │     │
│                 └──────────────┘     │
│                                      │
│  Longitude      ┌──────────────┐     │
│                 │              │     │
│                 └──────────────┘     │
│                                      │
│  Status         ◉ Live  ○ Inactive   │
│                                      │
│  [ Save ]  [ Cancel ]                │
└──────────────────────────────────────┘
```

---

## Screen 4.2 — Coverage Map

```
PURPOSE
───────
Visual overview of market locations and cell status.
Which markets have data, which do not.

┌──────────────────┬──────────────────────────────────────────────────┐
│  🗺 Coverage ←   │  Coverage Map                                    │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │                                          │   │
│                  │  │     [  MAP OF ADDIS ABABA  ]             │   │
│                  │  │                                          │   │
│                  │  │    ● Merkato                             │   │
│                  │  │      6 cells live                        │   │
│                  │  │                                          │   │
│                  │  │    ◐ Shola                               │   │
│                  │  │      2 cells live · 3 insufficient       │   │
│                  │  │                                          │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │  (Leaflet or Mapbox map, MVP static is fine)    │
│                  │                                                  │
│                  │  ● All cells live                               │
│                  │  ◐ Partial coverage                             │
│                  │  ○ No coverage                                  │
│                  │                                                  │
│                  │  Market          Live cells   Total cells       │
│                  │  ─────────────────────────────────────────     │
│                  │  Merkato         6            5                 │
│                  │  Shola           2            5                 │
└──────────────────┴──────────────────────────────────────────────────┘

NOTE
────
MVP map can be a static image with pins.
Interactive map is a v2 enhancement.
The table below the map is the functional element.
```

---

# Phase 5 — Contributor Management

**3 screens**

```
┌──────┬──────────────────────────────────┬───────────────────────┐
│  #   │  Screen Name                     │  Actor                │
├──────┼──────────────────────────────────┼───────────────────────┤
│  5.1 │  Contributor List                │  Admin                │
│  5.2 │  Agent Management                │  Admin                │
│  5.3 │  Rate Limit Log                  │  Admin                │
└──────┴──────────────────────────────────┴───────────────────────┘
```

---

## Screen 5.1 — Contributor List

```
PURPOSE
───────
Overview of all contributors.
Submission counts, status, kind.
Promote to agent from this screen.

┌──────────────────┬──────────────────────────────────────────────────┐
│  👥 Contributors←│  Contributors                                    │
│                  │                                                  │
│                  │  Total activated: 34  ·  Agents: 2              │
│                  │                                                  │
│                  │  [ Search by Telegram ID... ]                    │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  Telegram ID   Kind    Submissions  Since │   │
│                  │  │  ────────────────────────────────────── │   │
│                  │  │  1234567890    agent   47           Jun 1 │   │
│                  │  │                              [View][Edit] │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  9876543210    agent   38           Jun 2 │   │
│                  │  │                              [View][Edit] │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  5554443330    user    14           Jun 5 │   │
│                  │  │                        [Promote to agent] │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  3332221110    user    8            Jun 7 │   │
│                  │  │                        [Promote to agent] │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │                                                  │
│                  │  Showing 34 of 34 activated contributors.       │
│                  │  Activated = at least one accepted submission.  │
└──────────────────┴──────────────────────────────────────────────────┘
```

---

## Screen 5.2 — Agent Management

```
PURPOSE
───────
Manage field agents specifically.
Add by Telegram ID. Assign to market. Remove.
Agents are weighted 2× in index computation.

┌──────────────────┬──────────────────────────────────────────────────┐
│  🎯 Agents ←     │  Agent Management                         [+ Add] │
│                  │                                                  │
│                  │  Agents submit through the standard Telegram     │
│                  │  bot. This panel marks a contributor as          │
│                  │  kind = agent. Agent submissions are weighted    │
│                  │  2× in the index computation.                    │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  Telegram ID   Name      Market   Status  │   │
│                  │  │  ────────────────────────────────────── │   │
│                  │  │  1234567890    Almaz T.  Merkato  ● Active│   │
│                  │  │                          [Edit]  [Remove]  │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  9876543210    Dawit K.  Shola    ● Active│   │
│                  │  │                          [Edit]  [Remove]  │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │                                                  │
│                  │  The contributor must have sent /start before   │
│                  │  they can be added as an agent.                 │
└──────────────────┴──────────────────────────────────────────────────┘

ADD AGENT MODAL
───────────────
┌──────────────────────────────────────┐
│  Add Agent                           │
│  ──────────                         │
│                                      │
│  Telegram user ID  ┌─────────────┐   │
│                    │             │   │
│                    └─────────────┘   │
│                                      │
│  Internal name     ┌─────────────┐   │
│  (not public)      │             │   │
│                    └─────────────┘   │
│                                      │
│  Assigned market   [ Merkato ▾ ]     │
│                                      │
│  [ Add ]  [ Cancel ]                 │
└──────────────────────────────────────┘
```

---

## Screen 5.3 — Rate Limit Log

```
PURPOSE
───────
View all rate limit rejections.
Evidence of abuse control for demonstration.
The rejection count is the abuse-control claim.

┌──────────────────┬──────────────────────────────────────────────────┐
│  🚫 Rate Limits← │  Rate Limit Log                                  │
│                  │                                                  │
│                  │  Rejections today: 4                             │
│                  │  Rejections this week: 11                        │
│                  │                                                  │
│                  │  [ Date range ▾ ]  [ Market ▾ ]                 │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  Time   Contributor  Market  Commodity    │   │
│                  │  │  Rule                                     │   │
│                  │  │  ────────────────────────────────────── │   │
│                  │  │  14:12  5554443330   Merkato  Tomato      │   │
│                  │  │         R4: max submissions/day exceeded  │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  13:40  3332221110   Shola    Onion       │   │
│                  │  │         R5: duplicate within 6 hours      │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  11:20  5554443330   Merkato  Potato      │   │
│                  │  │         R4: max submissions/day exceeded  │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │                                                  │
│                  │  Read only. Logged on every rejection.          │
│                  │  Rejection count is queryable for demonstration.│
└──────────────────┴──────────────────────────────────────────────────┘
```

---

# Phase 6 — Data & Validation

**3 screens**

```
┌──────┬──────────────────────────────────┬───────────────────────┐
│  #   │  Screen Name                     │  Actor                │
├──────┼──────────────────────────────────┼───────────────────────┤
│  6.1 │  Validation Parameters           │  Admin                │
│  6.2 │  Data Export                     │  Admin + Evaluator    │
│  6.3 │  Submissions Archive             │  Admin + Evaluator    │
└──────┴──────────────────────────────────┴───────────────────────┘
```

---

## Screen 6.1 — Validation Parameters

```
PURPOSE
───────
Configure all validation rules.
Changes apply to new submissions only.
Every save logged to audit trail.

┌──────────────────┬──────────────────────────────────────────────────┐
│  ✅ Validation ← │  Validation Parameters                           │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  ⚠  Changes apply to new submissions     │   │
│                  │  │     only. Not retroactive. All changes   │   │
│                  │  │     are logged to the audit trail.       │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │  (amber notice, top)                             │
│                  │                                                  │
│                  │  General Rules                                   │
│                  │  ──────────────────────────────────────────     │
│                  │  IQR multiplier (R2)         ┌──────┐           │
│                  │                              │  2.5 │           │
│                  │                              └──────┘           │
│                  │  Baseline deviation (R3)     ┌──────┐           │
│                  │                              │  60% │           │
│                  │                              └──────┘           │
│                  │  Rate limit per contributor  ┌──────┐           │
│                  │  per cell per day            │  10  │           │
│                  │                              └──────┘           │
│                  │  Duplicate window (hours)    ┌──────┐           │
│                  │                              │   6  │           │
│                  │                              └──────┘           │
│                  │  Rolling window (hours)      ┌──────┐           │
│                  │                              │  72  │           │
│                  │                              └──────┘           │
│                  │  Publication threshold       ┌──────┐           │
│                  │                              │   3  │           │
│                  │                              └──────┘           │
│                  │                                                  │
│                  │  Commodity Absolute Bounds (birr/canonical unit) │
│                  │  ──────────────────────────────────────────     │
│                  │  Commodity   Min          Max                    │
│                  │  Tomato     ┌──────┐     ┌──────┐               │
│                  │             │  20  │     │  500 │               │
│                  │             └──────┘     └──────┘               │
│                  │  Onion      ┌──────┐     ┌──────┐               │
│                  │             │  15  │     │  400 │               │
│                  │             └──────┘     └──────┘               │
│                  │  (remaining commodities same pattern)            │
│                  │                                                  │
│                  │  ┌──────────────┐  ┌──────────────────────┐    │
│                  │  │ Save changes │  │  Revert to defaults  │    │
│                  │  └──────────────┘  └──────────────────────┘    │
└──────────────────┴──────────────────────────────────────────────────┘

SAVE CONFIRMATION
─────────────────
┌──────────────────────────────────────┐
│  Save validation parameters?         │
│                                      │
│  Changes apply to new submissions    │
│  only. This action will be logged.   │
│                                      │
│  [ Confirm ]  [ Cancel ]             │
└──────────────────────────────────────┘
```

---

## Screen 6.2 — Data Export

```
PURPOSE
───────
Generate and download curated data extracts.
Provenance attached. Insufficient-data rows present.
The artefact institutions actually use.

┌──────────────────┬──────────────────────────────────────────────────┐
│  📤 Export ←     │  Data Export                                     │
│                  │                                                  │
│                  │  Commodities                                     │
│                  │  ☑ Tomato  ☑ Onion  ☑ Potato  ☑ Teff  ☑ Oil   │
│                  │                                                  │
│                  │  Markets                                         │
│                  │  ☑ Merkato  ☑ Shola                             │
│                  │                                                  │
│                  │  Date range                                      │
│                  │  ┌───────────────┐  ┌───────────────┐           │
│                  │  │  Jun 1, 2025  │  │ Jun 14, 2025  │           │
│                  │  └───────────────┘  └───────────────┘           │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  Preview                                  │   │
│                  │  │  84 rows · 6 marked insufficient_data    │   │
│                  │  │  Commercial-permitted records only        │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  This export includes:                    │   │
│                  │  │  · Submission count per cell              │   │
│                  │  │  · Source composition per cell            │   │
│                  │  │  · Confidence indicator                   │   │
│                  │  │  · Methodology note (waga-method-v1)      │   │
│                  │  │  · Insufficient-data rows — present       │   │
│                  │  │    and marked, never omitted              │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │           Download CSV                   │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │  (accent green, full width of content area)     │
└──────────────────┴──────────────────────────────────────────────────┘
```

---

## Screen 6.3 — Submissions Archive

```
PURPOSE
───────
Full searchable history of all submissions.
Filterable by every dimension.
Different from Live Feed — this is the full record.

┌──────────────────┬──────────────────────────────────────────────────┐
│  🗄 Submissions← │  Submissions Archive                             │
│                  │                                                  │
│                  │  [ Status ▾ ]  [ Source ▾ ]  [ Market ▾ ]       │
│                  │  [ Commodity ▾ ]  [ Date range ▾ ]              │
│                  │                                                  │
│                  │  1,247 submissions total · 42 flagged            │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  Date    Commodity  Market  Price  Source │   │
│                  │  │  Status                                   │   │
│                  │  │  ────────────────────────────────────── │   │
│                  │  │  Jun 14  Tomato     Merkato  86/kg  user  │   │
│                  │  │  ✅ Accepted                              │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  Jun 14  Tomato     Merkato  200/kg user  │   │
│                  │  │  ⚠ Flagged · R2_IQR_OUTLIER              │   │
│                  │  │  Reference 75–95 · Confirmed · Excluded  │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  Jun 14  Onion      Shola    45/kg  agent │   │
│                  │  │  ✅ Accepted                              │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │                                                  │
│                  │  [ Load more ]                                   │
│                  │                                                  │
│                  │  Append-only. No edits. No deletes.             │
└──────────────────┴──────────────────────────────────────────────────┘
```

---

# Phase 7 — System & Settings

**3 screens**

```
┌──────┬──────────────────────────────────┬───────────────────────┐
│  #   │  Screen Name                     │  Actor                │
├──────┼──────────────────────────────────┼───────────────────────┤
│  7.1 │  User Management                 │  Admin                │
│  7.2 │  Settings                        │  Admin                │
│  7.3 │  Audit Log                       │  Admin                │
└──────┴──────────────────────────────────┴───────────────────────┘
```

---

## Screen 7.1 — User Management

```
PURPOSE
───────
Manage dashboard access.
Invite-only. Admin creates all accounts.
Role assignment: Admin or Evaluator.

┌──────────────────┬──────────────────────────────────────────────────┐
│  👤 Users ←      │  User Management                          [+ Invite]│
│                  │                                                  │
│                  │  Active users                                    │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  Email               Role      Last login │   │
│                  │  │  ────────────────────────────────────── │   │
│                  │  │  tigist@wfp.org      Evaluator  Jun 14   │   │
│                  │  │                      [Change role][Deact] │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  abebe@fao.org       Evaluator  Jun 13   │   │
│                  │  │                      [Change role][Deact] │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  admin@wagaindex.com  Admin      Jun 14   │   │
│                  │  │                      (own account)        │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │                                                  │
│                  │  Pending invites                                 │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  kebede@ifpri.org    Evaluator            │   │
│                  │  │  Sent Jun 13 · Expires Jun 14 (amber)    │   │
│                  │  │                      [Resend]  [Cancel]   │   │
│                  │  └──────────────────────────────────────────┘   │
└──────────────────┴──────────────────────────────────────────────────┘

INVITE MODAL
────────────
┌──────────────────────────────────────┐
│  Invite a user                       │
│  ──────────────                     │
│                                      │
│  Email          ┌──────────────────┐ │
│                 │                  │ │
│                 └──────────────────┘ │
│                                      │
│  Role           ◉ Evaluator          │
│                 ○ Admin              │
│                                      │
│  [ Send invite ]  [ Cancel ]         │
└──────────────────────────────────────┘
```

---

## Screen 7.2 — Settings

```
PURPOSE
───────
System-level configuration.
Build constants visible but frozen in MVP.
Index weights and methodology version.

┌──────────────────┬──────────────────────────────────────────────────┐
│  ⚙ Settings ←   │  Settings                                        │
│                  │                                                  │
│                  │  Build Constants                                 │
│                  │  (frozen — changes require team agreement)       │
│                  │  ──────────────────────────────────────────     │
│                  │  Markets                    2                   │
│                  │  Commodities                5                   │
│                  │  Cells                      10                  │
│                  │  Activation target          40 contributors     │
│                  │  Rolling window             72 hours            │
│                  │  Publication threshold      3 submissions       │
│                  │  (all read only in MVP)                         │
│                  │                                                  │
│                  │  Index Weights                                   │
│                  │  ──────────────────────────────────────────     │
│                  │  Source: Agent              2.0                 │
│                  │  Source: User               1.0                 │
│                  │  Source: Scraped / Seed     0.5                 │
│                  │  Recency decay              0.5 → 1.0           │
│                  │  (stored in version control, not tuned here)    │
│                  │                                                  │
│                  │  Methodology                                     │
│                  │  ──────────────────────────────────────────     │
│                  │  Version                    waga-method-v1      │
│                  │  Computation                Weighted median     │
│                  │  Imputation                 None — never        │
│                  │  Rebuild from scratch       [ Run rebuild ]     │
│                  │                                                  │
│                  │  LLM Usage                                      │
│                  │  ──────────────────────────────────────────     │
│                  │  Calls today                6                   │
│                  │  Cost today                 $0.0024             │
│                  │  Total cost to date         $0.0187             │
└──────────────────┴──────────────────────────────────────────────────┘
```

---

## Screen 7.3 — Audit Log

```
PURPOSE
───────
Every admin action. Append-only. Exportable.
Full accountability trail.

┌──────────────────┬──────────────────────────────────────────────────┐
│  📜 Audit Log ←  │  Audit Log                                       │
│                  │                                                  │
│                  │  [ Actor ▾ ]  [ Action ▾ ]  [ Date range ▾ ]    │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  Time    Actor           Action           │   │
│                  │  │  ────────────────────────────────────── │   │
│                  │  │  15:32   admin@waga...   Added synonym    │   │
│                  │  │                          tmatem → Tomato  │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │ │  15:20   admin@waga...   Validation param │   │
│                  │  │                          IQR 2.0 → 2.5    │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  14:55   admin@waga...   Agent added      │   │
│                  │  │                          TG 9876 → Shola  │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  14:30   admin@waga...   Invited user     │   │
│                  │  │                          tigist@wfp.org   │   │
│                  │  ├──────────────────────────────────────────┤   │
│                  │  │  13:10   admin@waga...   Day-zero loaded  │   │
│                  │  │                          10 cells seeded  │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │                                                  │
│                  │  ┌──────────────────────────────────────────┐   │
│                  │  │  ↓ Export audit log CSV                  │   │
│                  │  └──────────────────────────────────────────┘   │
│                  │                                                  │
│                  │  Read only. Append-only. No deletions.          │
└──────────────────┴──────────────────────────────────────────────────┘
```

---

## Final Screen Inventory

```
┌─────────────────────────────────────────────────────────────────┐
│  ADMIN DASHBOARD — COMPLETE SCREEN INVENTORY                    │
├──────┬──────────────────────────────────────┬───────────────────┤
│  #   │  Screen Name                         │  Phase            │
├──────┼──────────────────────────────────────┼───────────────────┤
│  1.1 │  Login                               │  Authentication   │
│  1.2 │  Set Password                        │  Authentication   │
├──────┼──────────────────────────────────────┼───────────────────┤
│  2.1 │  Dashboard                           │  Overview         │
│  2.2 │  Live Feed                           │  Overview         │
│  2.3 │  Coverage Panel                      │  Overview         │
├──────┼──────────────────────────────────────┼───────────────────┤
│  3.1 │  Category List                       │  Commodity Mgmt   │
│  3.2 │  Commodity List                      │  Commodity Mgmt   │
│  3.3 │  Synonym Table                       │  Commodity Mgmt   │
│  3.4 │  Unparsed Queue                      │  Commodity Mgmt   │
├──────┼──────────────────────────────────────┼───────────────────┤
│  4.1 │  Market List                         │  Market Mgmt      │
│  4.2 │  Coverage Map                        │  Market Mgmt      │
├──────┼──────────────────────────────────────┼───────────────────┤
│  5.1 │  Contributor List                    │  Contributor Mgmt │
│  5.2 │  Agent Management                    │  Contributor Mgmt │
│  5.3 │  Rate Limit Log                      │  Contributor Mgmt │
├──────┼──────────────────────────────────────┼───────────────────┤
│  6.1 │  Validation Parameters               │  Data & Validation│
│  6.2 │  Data Export                         │  Data & Validation│
│  6.3 │  Submissions Archive                 │  Data & Validation│
├──────┼──────────────────────────────────────┼───────────────────┤
│  7.1 │  User Management                     │  System           │
│  7.2 │  Settings                            │  System           │
│  7.3 │  Audit Log                           │  System           │
└──────┴──────────────────────────────────────┴───────────────────┘

Phase 1   Authentication               2 screens
Phase 2   Overview & Monitoring        3 screens
Phase 3   Commodity Management         4 screens
Phase 4   Market Management            2 screens
Phase 5   Contributor Management       3 screens
Phase 6   Data & Validation            3 screens
Phase 7   System & Settings            3 screens
──────────────────────────────────────────────────
Total                                 20 screens
```
