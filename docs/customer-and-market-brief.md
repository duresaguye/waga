# Waga Index — Customer & Market Brief (Draft)

*Scope note: under 2 pages. Focus: what we build, who can pay, how NGOs get data today, and what we add.*

---

## 1. What we are building

**Waga** is a food-price index platform for Ethiopia.

It collects structured market prices (start: Addis Ababa, 2 markets, 5 staples), reviews them, and publishes auditable **72-hour market-price index** values plus CSV/API exports.

It is **not** a replacement for the official ESS Consumer Price Index.  
It is a **faster, market-level food price signal** with provenance (who submitted, when reviewed, how the index was computed).

**Phase 1 product surface**
- Public: simple “what does teff cost this week?” view (Amharic + English)
- Institutional: authenticated API + CSV exports of accepted prices and index snapshots

---

## 2. Who can actually pay

Public users will not pay. Revenue comes from institutions that already budget for market monitoring, cash assistance design, procurement, or risk.

| Priority | Customer | Why they pay | Likely product |
|---|---|---|---|
| **A — strongest near-term** | Humanitarian / Cash & Voucher Assistance (CVA) orgs: WFP partners, IRC, CARE, Save the Children, local NGOs in Ethiopia Cash Working Group | Need frequent prices to set transfer values and check if cash is still feasible | API + CSV + weekly brief |
| **A** | Research / monitoring orgs: REACH/IMPACT-style users, universities, think tanks | Need cleaner, auditable time series with methodology | Data license + exports |
| **B** | Institutional buyers: hotels, caterers, school feeding, hospitals, cooperatives, large traders | Need wholesale benchmarks for procurement / bidding | Dashboard + alerts |
| **B** | Fintech / agribusiness / insurers | Need local food inflation inputs for products and risk | API subscription |
| **C (later)** | Government / ESS-adjacent users | Already produce official CPI; may buy gap-filling or faster urban signals, not a rival CPI | Pilot / MoU, not first revenue |

**Honest constraint:** many NGO price datasets are **free** today (JMMI, FEWS NET, HDX). Waga must sell **speed, specificity, audit trail, and API reliability** — not “prices exist.”

---

## 3. What NGOs need — and how they get it now

### What they need
- Prices for a **Minimum Expenditure Basket** (food + some non-food)
- **Market functionality** (can traders restock? are markets open?)
- Coverage in **operational woredas**, not only Addis
- Enough quotes to set / adjust **cash transfer values**
- Comparable medians by woreda / region / month

### How they get it today

| Source | Who | Cadence | Limitation for Waga’s opportunity |
|---|---|---|---|
| **JMMI (REACH + Ethiopia Cash Working Group)** | Humanitarian partners collect via KoBo KIIs | ~monthly; coverage varies (often ~70–100 of 1,142 woredas) | Slow vs daily retail reality; coverage depends on partners; not a clean public consumer product |
| **FEWS NET** | Food-security early warning | Monthly staples / markets | Broad food-security use; not designed as live consumer index API |
| **WFP VAM / HDX** | WFP + open humanitarian data | Irregular / program-driven | Good for analysis; weak for “what is the price in this market today?” |
| **ESS CPI** | Ethiopian Statistics Service | Monthly official inflation | Authoritative but delayed and aggregated; not market-cell level for ops |
| **FAO GIEWS / World Bank RTP** | Global systems | Monthly / modeled | Useful macro; weak for operational city-market decisions |

**Gap Waga can fill:** near-real-time, named market + commodity cells, accepted/rejected review trail, and machine-readable export — starting where data density is highest (Addis), then expanding to hubs.

---

## 4. Public / “normal people” use (free layer)

Keep a thin public product so the brand is useful and shareable:

- Current price for teff, wheat, maize, onion, cooking oil
- “Up / down vs last week” in plain language
- Amharic + English
- No login for read-only market summary

This is **distribution and trust**, not the business model. Paying customers fund collection quality and exports.

---

## 5. What we can add (differentiation)

Do **not** compete as “another monthly PDF.” Add:

1. **Speed** — 72-hour rolling index vs monthly JMMI/CPI cycles  
2. **Auditability** — submission → review → index snapshot chain  
3. **API-first exports** — CSV/JSON for CVA tools and analysts  
4. **Named markets** — e.g. Ehil Berenda vs Atikilt Tera, not only “Addis Ababa”  
5. **Tight staple basket** — fewer items, higher refresh rate  
6. Later (not v1): alerts when a cell jumps X%, contributor apps, regional hub expansion

---

## 6. Recommended positioning (one sentence)

> **Waga is the audited, API-ready food price index for Ethiopian markets — free for the public to check staple prices, paid for NGOs and institutions that need faster, cleaner data than monthly surveys.**

---

## 7. Immediate next decisions

1. Confirm Phase 1 markets + 5 commodities (proposed: Ehil Berenda, Atikilt Tera; teff, wheat, maize, onion, cooking oil).  
2. Pick primary paying beachhead: **CVA/NGO data users** vs **procurement buyers**.  
3. Design public free view vs paid export package.  
4. Interview 3–5 Cash Working Group / NGO M&E staff on what they still manually rebuild today.
