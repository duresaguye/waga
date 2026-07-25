# Text Normalization (Amharic / Afaan Oromo / English)

Agents may mistype or use different languages. Waga keeps **button codes** as the source of truth and maps free text to those codes.

## Principle

`	ext
What they typed  ->  normalize  ->  synonym match  ->  canonical code
     (raw)              clean         dictionary      teff_mixed
`

- Store raw text for audit
- Store only **canonical** market_id / commodity_id on accepted submissions
- If unsure -> show confirm buttons (never silent wrong match)

## Phase 1 (now)

Most intake is **buttons** (no typing). Normalization matters when:

- Market = **Other** (free-text name)
- Future chat / voice -> text
- Admin / import free text

## Normalize steps

1. Trim whitespace
2. Collapse multiple spaces
3. Latin: lowercase (Teff -> 	eff)
4. Strip common punctuation
5. Look up commodity_synonyms by (normalized, script)
6. Optional fuzzy: close Latin spellings (	ef ~ 	eff)
7. If confidence low -> ask agent to tap the commodity/market button

## Scripts

| Script enum | Used for |
|---|---|
| english | English spellings / typos |
| latin | Afaan Oromo and other Latin-script forms |
| ethiopic | Amharic (Fidel) — taken from 	elegram_bot/reference.py names |

## Seeded staple synonyms (examples)

| Canonical | English / typos | Afaan Oromo (latin) | Amharic |
|---|---|---|---|
| 	eff_mixed | teff, tef, taff | xafii, xaafii | from bot 
ame_am |
| wheat | wheat, wheet | qamadii | from bot 
ame_am |
| maize | maize, corn | boqqolloo | from bot 
ame_am |
| onion | onion, shinkurt | shunkurtii | from bot 
ame_am |
| cooking_oil | oil, cooking oil | zayitii | from bot 
ame_am |

Seeded by: uv run waga-seed-phase1

## Markets

Buttons cover Merkato, Shola, etc.
**Other** accepts typed names in Amharic / Afaan Oromo / English and stores them as market_label.
See docs/addis-ai-intake.md for voice (Addis AI STT).

## AI / voice (Addis AI)

Addis AI STT (Amharic/Oromo) -> confirm -> submit.
AI helps intake; it does not invent prices. Full plan: docs/addis-ai-intake.md.

## Code

- Synonym table: commodity_synonyms
- Helpers: app/services/text_normalization.py
- Admin CRUD: /api/v1/admin/catalogue/synonyms
