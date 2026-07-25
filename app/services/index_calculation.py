"""Compute published / insufficient index cells from accepted submissions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from statistics import median
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IndexStatus
from app.models.index_values import IndexValue
from app.repositories.index_values import IndexValueRepository
from app.repositories.reference_data import ReferenceDataRepository
from app.services.index_rules import (
    METHOD_VERSION_INDEX,
    MIN_SUBMISSIONS_TO_PUBLISH,
    WINDOW_HOURS,
)


class IndexCalculationService:
    def __init__(
        self,
        session: AsyncSession,
        index_values: IndexValueRepository,
        reference: ReferenceDataRepository,
    ) -> None:
        self._session = session
        self._index = index_values
        self._reference = reference

    async def recompute(
        self,
        market_id: int,
        commodity_id: int,
        *,
        trigger_verification_id: UUID,
        commit: bool = True,
    ) -> IndexValue:
        """72h median of accepted prices; publish at ≥3 submissions."""
        existing = await self._index.get_by_trigger(trigger_verification_id)
        if existing is not None:
            return existing

        commodity = await self._reference.get_commodity(commodity_id)
        unit = commodity.canonical_unit if commodity is not None else "kg"

        window_end = datetime.now(UTC)
        window_start = window_end - timedelta(hours=WINDOW_HOURS)
        accepted = await self._index.list_accepted_in_window(
            market_id=market_id,
            commodity_id=commodity_id,
            window_start=window_start,
            window_end=window_end,
        )

        prices = [
            Decimal(str(item["submission"].price_canonical))
            for item in accepted
            if item["submission"].price_canonical is not None
        ]
        contributor_ids = {
            item["submission"].contributor_id
            for item in accepted
            if item["submission"].contributor_id is not None
        }
        source_mix: dict[str, int] = {}
        for item in accepted:
            source = str(item["submission"].source.value)
            source_mix[source] = source_mix.get(source, 0) + 1

        n = len(prices)
        if n >= MIN_SUBMISSIONS_TO_PUBLISH:
            status = IndexStatus.PUBLISHED
            value: Decimal | None = Decimal(str(median(prices))).quantize(Decimal("0.0001"))
            insufficient_reason = None
        else:
            status = IndexStatus.INSUFFICIENT_DATA
            value = None
            insufficient_reason = "no_submissions" if n == 0 else "below_threshold"

        row = IndexValue(
            id=uuid4(),
            market_id=market_id,
            commodity_id=commodity_id,
            trigger_verification_id=trigger_verification_id,
            method_version=METHOD_VERSION_INDEX,
            window_start=window_start,
            window_end=window_end,
            computed_at=window_end,
            value=value,
            unit=unit,
            n_submissions=n,
            n_contributors=len(contributor_ids),
            source_mix=source_mix,
            status=status,
        )
        self._index.add(row)
        if commit:
            await self._session.commit()
            await self._session.refresh(row)
        # Attach reason for API mappers (not a DB column).
        setattr(row, "insufficient_reason", insufficient_reason)
        return row
