# Waga Index Backend Implementation Plan

## Status

Schema phase completed on July 25, 2026. The ORM models, initial Alembic migration, database
constraints, append-only triggers, and schema tests are implemented. Repositories, services,
APIs, seed data, and Supabase connection changes remain deferred to later iterations.

## Goal

Build a single FastAPI service backed by Supabase PostgreSQL that accepts structured market
price submissions through REST, stores them with complete provenance, supports manual
accept/flag review, computes auditable market-price index snapshots, and exposes read and CSV
export APIs.

The first release excludes Telegram, voice, automatic verification, LLM/ASR integrations,
background workers, and frontend applications.

## Build Constants

| Constant | Value |
|---|---|
| Markets | 2 |
| Commodities | 5 |
| Market-commodity cells | 10 |
| Publication threshold | 3 accepted submissions |
| Index window | Rolling 72 hours |
| Languages represented in reference data | Amharic and English |
| Index method version | `v1` |

The actual market list, commodity basket, synonyms, unit rules, baseline data, and consent copy
must be supplied before production activation.

## Target Structure

```text
waga/
|-- AGENT.md
|-- plan.md
|-- pyproject.toml
|-- alembic.ini
|-- Dockerfile
|-- docker-compose.yml
|-- .env.example
|-- app/
|   |-- main.py
|   |-- config.py
|   |-- database.py
|   |-- dependencies.py
|   |-- api/
|   |   |-- router.py
|   |   `-- routes/
|   |       |-- health.py
|   |       |-- reference_data.py
|   |       |-- submissions.py
|   |       |-- reviews.py
|   |       |-- prices.py
|   |       |-- coverage.py
|   |       `-- exports.py
|   |-- models/
|   |   |-- reference_data.py
|   |   |-- contributors.py
|   |   |-- submissions.py
|   |   |-- verification.py
|   |   `-- index_values.py
|   |-- schemas/
|   |-- repositories/
|   |   |-- reference_data.py
|   |   |-- contributors.py
|   |   |-- submissions.py
|   |   |-- verification.py
|   |   |-- index_values.py
|   |   `-- reporting.py
|   |-- services/
|   |   |-- submissions.py
|   |   |-- index_calculation.py
|   |   `-- exports.py
|   `-- commands/
|       |-- seed_reference_data.py
|       |-- load_baseline.py
|       `-- rebuild_index.py
|-- migrations/
|   `-- versions/
|-- seed_data/
`-- tests/
    |-- unit/
    |-- integration/
    `-- api/
```

## Database Model

### Reference data

- `sectors`: stable code, English and Amharic names, description, and active flag.
- `markets`: stable code, English and Amharic names, optional coordinates, active flag.
- `commodities`: required sector, stable code, English and Amharic names, one canonical unit,
  and active flag.
- `commodity_synonyms`: future normalization reference data; no LLM dependency.
- `unit_conversions`: commodity-specific conversion factors into the canonical unit.

### Contributors and consent

- `contributors`: server ID, external REST contributor identifier, kind, first-seen timestamp.
- `contributor_consents`: contributor, consent version, accepted timestamp.
- Do not collect names, phone numbers, or precise user location.

### Submissions

- Store raw submitted fields and normalized market, commodity, price, and unit fields.
- Store source and licence class independently.
- Store `received_at`, optional `observed_at`, parse status, parse method, and input mode.
- Input mode is `rest` in this phase.
- Submission rows are immutable.

### Manual review

- `submission_verifications` references one submission.
- Outcome is `accepted`, `flagged`, or `pending`.
- Store reviewer identifier, decision timestamp, reason code, and human-readable reason.
- The repository persists decisions; there is no automatic verification service.
- A submission cannot receive conflicting final outcomes.

### Derived index

- `index_values` stores append-only snapshots by market, commodity, computation timestamp, and
  method version.
- Include window boundaries, value, unit, submission count, contributor count, source
  composition, and status.
- Link each snapshot to its triggering accepted review for deterministic reconstruction.

## Repositories

| Repository | Responsibility |
|---|---|
| `ReferenceDataRepository` | Read markets, commodities, synonyms, and conversion rules |
| `ContributorRepository` | Create/read contributors and append consent records |
| `SubmissionRepository` | Append submissions and query submission history |
| `VerificationRepository` | Append and read manual review outcomes |
| `IndexValueRepository` | Append index snapshots and read current/history values |
| `ReportingRepository` | Coverage, feed, source mix, activation, and export queries |

Repositories receive an `AsyncSession`. Do not introduce a generic base repository.

## Services

### SubmissionService

- Accept a structured REST request.
- Resolve market, commodity, unit, source, and licence values.
- Validate structural invariants such as positive prices and required consent.
- Create or resolve the contributor.
- Append the submission and its initial `pending` review state in one transaction.
- Expose an operator action to accept or flag a pending submission using
  `VerificationRepository`.
- Trigger cell recomputation after an accepted decision.

This service does not perform statistical plausibility checks or automatic verification.

### IndexCalculationService

- Read accepted submissions for the affected cell from the trailing 72 hours.
- Write `insufficient_data` when fewer than three accepted submissions exist.
- Otherwise calculate a weighted median using version-controlled source and recency weights.
- Use the triggering submission timestamp as the deterministic window end.
- Append a new snapshot; never update an existing snapshot.
- Support a full chronological rebuild from immutable source records.

Initial source weights:

| Source | Weight |
|---|---|
| Agent | `2.0` |
| User | `1.0` |
| Scraped | `0.5` |
| Seed | `0.5` |

Recency weight increases linearly from `0.5` at the start of the window to `1.0` at the end.

### ExportService

- Produce CSV for selected markets, commodities, and dates.
- Filter source observations by licence class.
- Treat missing classifications as internal-only.
- Include status, supporting count, source mix, method version, and methodology note.
- Include below-threshold rows as `insufficient_data`.

## API Contract

### Reference data

```text
GET /api/v1/sectors
GET /api/v1/markets
GET /api/v1/commodities
```

### Submissions and review

```text
POST /api/v1/submissions
GET  /api/v1/reviews/pending
POST /api/v1/reviews/{submission_id}/accept
POST /api/v1/reviews/{submission_id}/flag
```

New submissions return `202 Accepted` with the submission ID and `pending` status.

Operator review endpoints require `X-Admin-Key`, validated against
`WAGA_ADMIN_API_KEY`. The key must be compared using a timing-safe operation.

### Prices and reporting

```text
GET /api/v1/prices/current
GET /api/v1/prices/series
GET /api/v1/prices/compare
GET /api/v1/coverage
GET /api/v1/submissions/feed
GET /api/v1/exports/prices.csv
```

Every response containing a price must include:

- `status`
- `value`
- `unit`
- `n_submissions`
- `n_contributors`
- `source_mix`
- `window_start`
- `window_end`
- `computed_at`
- `method_version`

## Environment Variables

```text
WAGA_ENVIRONMENT=development
WAGA_DEBUG=false
WAGA_DATABASE_URL=
WAGA_DATABASE_MIGRATION_URL=
WAGA_TEST_DATABASE_URL=
WAGA_ADMIN_API_KEY=
WAGA_INDEX_WINDOW_HOURS=72
WAGA_PUBLICATION_THRESHOLD=3
WAGA_METHOD_VERSION=v1
```

- Runtime uses the Supabase pooled connection.
- Alembic and maintenance commands use the direct connection.
- Supabase connections require SSL.
- Local development may continue using Docker PostgreSQL.

## Implementation Order

1. **Completed:** Add sector-aware ORM models and a complete initial Alembic migration.
2. Align configuration and database connection handling with Supabase.
3. Add reference-data seeds and loading commands.
4. Add repositories and dependency wiring.
5. Implement REST submission and manual review workflows.
6. Implement deterministic index computation.
7. Implement current price, history, comparison, coverage, and feed APIs.
8. Implement licence-filtered CSV export.
9. Add rebuild and operational commands.
10. Complete PostgreSQL integration tests and production documentation.

## Test Plan

- Apply the migration chain to an empty PostgreSQL database.
- Verify submissions are append-only and initially pending.
- Reject invalid references, prices, units, sources, licence classes, and missing consent.
- Verify admin-key protection on all review mutations.
- Accept and flag pending submissions and prevent conflicting final decisions.
- Verify pending and flagged submissions never affect index values.
- Verify the three-submission threshold and explicit insufficient-data snapshots.
- Test source weights, recency weights, weighted-median ties, and 72-hour boundaries.
- Verify concurrent acceptance does not create inconsistent current values.
- Rebuild the index and compare values, counts, statuses, and source mixes with the original
  snapshots.
- Verify commercial exports exclude restricted observations and retain insufficient-data rows.
- Run Ruff, formatting checks, strict MyPy, and Pytest before completion.

## Acceptance Criteria

- Structured REST submissions are stored with provenance and pending review status.
- Operators can accept or flag submissions through protected endpoints.
- Accepted submissions recompute only their affected cell.
- Published values require three accepted observations in the rolling 72-hour window.
- Missing coverage is reported as insufficient data without estimation.
- Current, series, comparison, coverage, feed, and CSV APIs expose supporting metadata.
- Supabase credentials are environment-only and migrations use the direct connection.
- A full rebuild reproduces the same derived values.
- No Telegram, voice, ASR, LLM, or automatic verification implementation is introduced.
