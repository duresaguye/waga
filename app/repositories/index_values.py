from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IndexStatus, ReviewOutcome
from app.models.index_values import IndexValue
from app.models.submissions import Submission
from app.models.verification import SubmissionVerification
from app.services.index_rules import METHOD_VERSION_INDEX


class IndexValueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, row: IndexValue) -> None:
        self._session.add(row)

    async def get_by_trigger(
        self, trigger_verification_id: UUID, *, method_version: str = METHOD_VERSION_INDEX
    ) -> IndexValue | None:
        statement = select(IndexValue).where(
            IndexValue.trigger_verification_id == trigger_verification_id,
            IndexValue.method_version == method_version,
        )
        return await self._session.scalar(statement)

    async def get_latest_for_cell(
        self,
        *,
        market_id: int,
        commodity_id: int,
        method_version: str = METHOD_VERSION_INDEX,
        as_of: datetime | None = None,
        published_only: bool = False,
    ) -> IndexValue | None:
        statement = (
            select(IndexValue)
            .where(
                IndexValue.market_id == market_id,
                IndexValue.commodity_id == commodity_id,
                IndexValue.method_version == method_version,
            )
            .order_by(IndexValue.computed_at.desc())
            .limit(1)
        )
        if as_of is not None:
            statement = statement.where(IndexValue.computed_at <= as_of)
        if published_only:
            statement = statement.where(IndexValue.status == IndexStatus.PUBLISHED)
        return await self._session.scalar(statement)

    async def list_latest_cells(
        self,
        *,
        method_version: str = METHOD_VERSION_INDEX,
        market_ids: list[int] | None = None,
        commodity_ids: list[int] | None = None,
    ) -> list[IndexValue]:
        statement = (
            select(IndexValue)
            .where(IndexValue.method_version == method_version)
            .order_by(IndexValue.computed_at.desc())
        )
        if market_ids is not None:
            statement = statement.where(IndexValue.market_id.in_(market_ids))
        if commodity_ids is not None:
            statement = statement.where(IndexValue.commodity_id.in_(commodity_ids))
        rows = list(await self._session.scalars(statement))
        latest: list[IndexValue] = []
        seen: set[tuple[int, int]] = set()
        for row in rows:
            key = (row.market_id, row.commodity_id)
            if key in seen:
                continue
            seen.add(key)
            latest.append(row)
        return latest

    async def list_accepted_in_window(
        self,
        *,
        market_id: int,
        commodity_id: int,
        window_start: datetime,
        window_end: datetime,
    ) -> list[dict[str, Any]]:
        statement = (
            select(Submission, SubmissionVerification)
            .join(
                SubmissionVerification,
                SubmissionVerification.submission_id == Submission.id,
            )
            .where(
                Submission.market_id == market_id,
                Submission.commodity_id == commodity_id,
                SubmissionVerification.outcome == ReviewOutcome.ACCEPTED,
                Submission.price_canonical.is_not(None),
                Submission.received_at >= window_start,
                Submission.received_at <= window_end,
            )
            .order_by(Submission.received_at.desc())
        )
        rows = await self._session.execute(statement)
        return [
            {"submission": submission, "verification": verification}
            for submission, verification in rows.all()
        ]

    async def list_in_range(
        self,
        *,
        commodity_id: int,
        market_id: int | None,
        start: datetime,
        end: datetime,
        method_version: str = METHOD_VERSION_INDEX,
    ) -> list[IndexValue]:
        filters = [
            IndexValue.commodity_id == commodity_id,
            IndexValue.method_version == method_version,
            IndexValue.computed_at >= start,
            IndexValue.computed_at <= end,
        ]
        if market_id is not None:
            filters.append(IndexValue.market_id == market_id)
        statement = (
            select(IndexValue)
            .where(and_(*filters))
            .order_by(IndexValue.computed_at.asc())
        )
        return list(await self._session.scalars(statement))
