from datetime import datetime
from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contributors import Contributor
from app.models.enums import ReviewOutcome
from app.models.reference_data import Commodity, Market
from app.models.submissions import Submission
from app.models.verification import SubmissionVerification


class SubmissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, submission: Submission) -> None:
        self._session.add(submission)

    def add_verification(self, verification: SubmissionVerification) -> None:
        self._session.add(verification)

    async def get_by_id(self, submission_id: UUID) -> Submission | None:
        return cast(Submission | None, await self._session.get(Submission, submission_id))

    async def get_by_client_submission_id(
        self,
        *,
        contributor_id: UUID,
        client_submission_id: UUID,
    ) -> Submission | None:
        statement = select(Submission).where(
            Submission.contributor_id == contributor_id,
            Submission.client_submission_id == client_submission_id,
        )
        return cast(Submission | None, await self._session.scalar(statement))

    async def get_pending_verification(
        self, submission_id: UUID
    ) -> SubmissionVerification | None:
        statement = select(SubmissionVerification).where(
            SubmissionVerification.submission_id == submission_id,
            SubmissionVerification.outcome == ReviewOutcome.PENDING,
        )
        return cast(
            SubmissionVerification | None, await self._session.scalar(statement)
        )

    async def list_pending_reviews(
        self, *, limit: int = 50
    ) -> list[dict[str, Any]]:
        statement = (
            select(
                Submission,
                SubmissionVerification,
                Market,
                Commodity,
                Contributor,
            )
            .join(
                SubmissionVerification,
                SubmissionVerification.submission_id == Submission.id,
            )
            .join(Market, Market.id == Submission.market_id)
            .join(Commodity, Commodity.id == Submission.commodity_id)
            .outerjoin(Contributor, Contributor.id == Submission.contributor_id)
            .where(SubmissionVerification.outcome == ReviewOutcome.PENDING)
            .order_by(Submission.received_at.desc())
            .limit(limit)
        )
        rows = await self._session.execute(statement)
        items: list[dict[str, Any]] = []
        for submission, verification, market, commodity, contributor in rows.all():
            items.append(
                {
                    "submission": submission,
                    "verification": verification,
                    "market": market,
                    "commodity": commodity,
                    "contributor": contributor,
                }
            )
        return items

    async def get_pending_review_bundle(
        self, submission_id: UUID
    ) -> dict[str, Any] | None:
        statement = (
            select(
                Submission,
                SubmissionVerification,
                Market,
                Commodity,
                Contributor,
            )
            .join(
                SubmissionVerification,
                SubmissionVerification.submission_id == Submission.id,
            )
            .join(Market, Market.id == Submission.market_id)
            .join(Commodity, Commodity.id == Submission.commodity_id)
            .outerjoin(Contributor, Contributor.id == Submission.contributor_id)
            .where(
                Submission.id == submission_id,
                SubmissionVerification.outcome == ReviewOutcome.PENDING,
            )
        )
        row = (await self._session.execute(statement)).first()
        if row is None:
            return None
        submission, verification, market, commodity, contributor = row
        return {
            "submission": submission,
            "verification": verification,
            "market": market,
            "commodity": commodity,
            "contributor": contributor,
        }

    async def list_accepted_prices(
        self,
        *,
        market_id: int,
        commodity_id: int,
        exclude_submission_id: UUID | None = None,
        limit: int = 20,
    ) -> list[Decimal]:
        statement: Select[tuple[Decimal]] = (
            select(Submission.price_canonical)
            .join(
                SubmissionVerification,
                SubmissionVerification.submission_id == Submission.id,
            )
            .where(
                Submission.market_id == market_id,
                Submission.commodity_id == commodity_id,
                SubmissionVerification.outcome == ReviewOutcome.ACCEPTED,
                Submission.price_canonical.is_not(None),
            )
            .order_by(Submission.received_at.desc())
            .limit(limit)
        )
        if exclude_submission_id is not None:
            statement = statement.where(Submission.id != exclude_submission_id)
        values = await self._session.scalars(statement)
        return [Decimal(str(value)) for value in values.all()]

    async def list_accepted_in_window(
        self,
        *,
        market_id: int,
        commodity_id: int,
        window_start: datetime,
        window_end: datetime,
    ) -> list[dict[str, Any]]:
        statement = (
            select(
                Submission,
                Contributor,
            )
            .join(
                SubmissionVerification,
                SubmissionVerification.submission_id == Submission.id,
            )
            .outerjoin(Contributor, Contributor.id == Submission.contributor_id)
            .where(
                Submission.market_id == market_id,
                Submission.commodity_id == commodity_id,
                SubmissionVerification.outcome == ReviewOutcome.ACCEPTED,
                Submission.received_at >= window_start,
                Submission.received_at <= window_end,
                Submission.price_canonical.is_not(None),
            )
            .order_by(Submission.received_at.asc())
        )
        rows = await self._session.execute(statement)
        items: list[dict[str, Any]] = []
        for submission, contributor in rows.all():
            items.append({"submission": submission, "contributor": contributor})
        return items

        if exclude_submission_id is not None:
            statement = statement.where(Submission.id != exclude_submission_id)
        values = await self._session.scalars(statement)
        return [Decimal(str(value)) for value in values.all()]

    async def get_accepted_verification(
        self, submission_id: UUID
    ) -> SubmissionVerification | None:
        statement = select(SubmissionVerification).where(
            SubmissionVerification.submission_id == submission_id,
            SubmissionVerification.outcome == ReviewOutcome.ACCEPTED,
        )
        return cast(
            SubmissionVerification | None, await self._session.scalar(statement)
        )

    async def list_all_accepted_cells(self) -> list[dict[str, Any]]:
        statement = (
            select(
                Submission,
                SubmissionVerification,
            )
            .join(
                SubmissionVerification,
                SubmissionVerification.submission_id == Submission.id,
            )
            .where(
                SubmissionVerification.outcome == ReviewOutcome.ACCEPTED,
                Submission.market_id.is_not(None),
                Submission.commodity_id.is_not(None),
            )
            .order_by(Submission.received_at.asc())
        )
        rows = await self._session.execute(statement)
        items: list[dict[str, Any]] = []
        for submission, verification in rows.all():
            items.append({"submission": submission, "verification": verification})
        return items
