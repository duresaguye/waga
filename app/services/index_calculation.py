"""Deterministic index computation for market-commodity cells."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.enums import IndexStatus, SubmissionSource
from app.models.index_values import IndexValue
from app.models.submissions import Submission
from app.repositories.index_values import IndexValueRepository
from app.repositories.reference_data import ReferenceDataRepository
from app.repositories.submissions import SubmissionRepository

SOURCE_WEIGHTS: dict[SubmissionSource, float] = {
    SubmissionSource.AGENT: 2.0,
    SubmissionSource.USER: 1.0,
    SubmissionSource.SCRAPED: 0.5,
    SubmissionSource.SEED: 0.5,
}


def recency_weight(
    received_at: datetime,
    *,
    window_start: datetime,
    window_end: datetime,
) -> float:
    span = (window_end - window_start).total_seconds()
    if span <= 0:
        return 1.0
    elapsed = (received_at - window_start).total_seconds()
    ratio = max(0.0, min(1.0, elapsed / span))
    return 0.5 + 0.5 * ratio


def weighted_median(values_weights: list[tuple[Decimal, float]]) -> Decimal:
    if not values_weights:
        raise ValueError("weighted_median requires at least one value")
    sorted_vw = sorted(values_weights, key=lambda item: item[0])
    total = sum(weight for _, weight in sorted_vw)
    half = total / 2
    cumulative = 0.0
    for value, weight in sorted_vw:
        cumulative += weight
        if cumulative >= half:
            return value
    return sorted_vw[-1][0]


class IndexCalculationService:
    def __init__(
        self,
        session: AsyncSession,
        submissions: SubmissionRepository,
        index_values: IndexValueRepository,
        reference_data: ReferenceDataRepository,
        settings: Settings,
    ) -> None:
        self._session = session
        self._submissions = submissions
        self._index_values = index_values
        self._reference_data = reference_data
        self._settings = settings

    async def recompute_cell(
        self,
        *,
        market_id: int,
        commodity_id: int,
        trigger_verification_id: UUID,
        window_end: datetime | None = None,
    ) -> IndexValue:
        end = window_end or datetime.now(UTC)
        window_start = end - timedelta(hours=self._settings.index_window_hours)
        existing = await self._index_values.get_by_trigger_verification(
            trigger_verification_id,
            method_version=self._settings.method_version,
        )
        if existing is not None:
            return existing

        commodity = await self._reference_data.get_commodity(commodity_id)
        if commodity is None:
            raise ValueError(f"Unknown commodity id {commodity_id}")

        accepted_rows = await self._submissions.list_accepted_in_window(
            market_id=market_id,
            commodity_id=commodity_id,
            window_start=window_start,
            window_end=end,
        )
        n_submissions = len(accepted_rows)
        contributor_ids = {
            row["contributor"].id
            for row in accepted_rows
            if row["contributor"] is not None
        }
        source_mix = _build_source_mix(accepted_rows)

        if n_submissions < self._settings.publication_threshold:
            status = IndexStatus.INSUFFICIENT_DATA
            value: Decimal | None = None
        else:
            status = IndexStatus.PUBLISHED
            weighted_values = _build_weighted_values(
                accepted_rows,
                window_start=window_start,
                window_end=end,
            )
            value = weighted_median(weighted_values)

        snapshot = IndexValue(
            market_id=market_id,
            commodity_id=commodity_id,
            trigger_verification_id=trigger_verification_id,
            method_version=self._settings.method_version,
            window_start=window_start,
            window_end=end,
            value=value,
            unit=commodity.canonical_unit,
            n_submissions=n_submissions,
            n_contributors=len(contributor_ids),
            source_mix=source_mix,
            status=status,
        )
        self._index_values.add(snapshot)
        await self._session.flush()
        return snapshot

    async def rebuild_all(self) -> int:
        accepted_rows = await self._submissions.list_all_accepted_cells()
        count = 0
        for row in accepted_rows:
            submission = row["submission"]
            verification = row["verification"]
            if submission.market_id is None or submission.commodity_id is None:
                continue
            await self.recompute_cell(
                market_id=submission.market_id,
                commodity_id=submission.commodity_id,
                trigger_verification_id=verification.id,
                window_end=submission.received_at,
            )
            count += 1
        await self._session.commit()
        return count


def _build_source_mix(rows: list[dict]) -> dict[str, int]:
    mix: dict[str, int] = {}
    for row in rows:
        submission: Submission = row["submission"]
        key = submission.source.value
        mix[key] = mix.get(key, 0) + 1
    return mix


def _build_weighted_values(
    rows: list[dict],
    *,
    window_start: datetime,
    window_end: datetime,
) -> list[tuple[Decimal, float]]:
    weighted: list[tuple[Decimal, float]] = []
    for row in rows:
        submission: Submission = row["submission"]
        if submission.price_canonical is None:
            continue
        source_weight = SOURCE_WEIGHTS.get(submission.source, 1.0)
        recency = recency_weight(
            submission.received_at,
            window_start=window_start,
            window_end=window_end,
        )
        weighted.append((Decimal(str(submission.price_canonical)), source_weight * recency))
    return weighted
