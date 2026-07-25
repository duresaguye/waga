"""Human + AI-assisted submission review."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.enums import ReviewOutcome
from app.models.verification import SubmissionVerification
from app.repositories.submissions import SubmissionRepository
from app.services.addis_chat import AddisChatClient
from app.services.agent_score import AgentScoreService
from app.services.exceptions import (
    ReviewConflictError,
    SubmissionNotFoundError,
    SubmissionValidationError,
)
from app.services.review_triage import ReviewTriageService, TriageResult, facts_as_dict


class ReviewService:
    def __init__(
        self,
        session: AsyncSession,
        submissions: SubmissionRepository,
        scores: AgentScoreService,
        settings: Settings,
        triage: ReviewTriageService | None = None,
    ) -> None:
        self._session = session
        self._submissions = submissions
        self._scores = scores
        self._settings = settings
        self._triage = triage or ReviewTriageService(AddisChatClient(settings))

    async def list_pending(self, *, limit: int = 50) -> list[dict]:
        rows = await self._submissions.list_pending_reviews(limit=limit)
        return [self._to_item(row) for row in rows]

    async def triage_submission(self, submission_id: UUID) -> dict:
        bundle = await self._submissions.get_pending_review_bundle(submission_id)
        if bundle is None:
            raise SubmissionNotFoundError("Pending submission not found")
        result = await self._run_triage(bundle)
        verification: SubmissionVerification = bundle["verification"]
        self._apply_ai(verification, result)
        await self._session.commit()
        await self._session.refresh(verification)
        item = self._to_item(bundle)
        item["comparison_facts"] = facts_as_dict(result.facts)
        return item

    async def accept(
        self,
        submission_id: UUID,
        *,
        reviewer_label: str,
        note: str | None = None,
    ) -> dict:
        return await self._finalize(
            submission_id,
            accepted=True,
            reviewer_label=reviewer_label,
            note=note,
        )

    async def flag(
        self,
        submission_id: UUID,
        *,
        reviewer_label: str,
        reason: str,
        reason_code: str | None = None,
    ) -> dict:
        cleaned = reason.strip()
        if not cleaned:
            raise SubmissionValidationError("reason is required when flagging")
        return await self._finalize(
            submission_id,
            accepted=False,
            reviewer_label=reviewer_label,
            note=cleaned,
            reason_code=reason_code,
        )

    async def triage_after_create(self, submission_id: UUID) -> None:
        """Best-effort AI assist right after a new pending submission."""
        try:
            await self.triage_submission(submission_id)
        except Exception:
            # Never block intake if triage fails.
            await self._session.rollback()

    async def _finalize(
        self,
        submission_id: UUID,
        *,
        accepted: bool,
        reviewer_label: str,
        note: str | None,
        reason_code: str | None = None,
    ) -> dict:
        label = reviewer_label.strip()
        if not label:
            raise SubmissionValidationError("reviewer_label is required")

        bundle = await self._submissions.get_pending_review_bundle(submission_id)
        if bundle is None:
            # Maybe already reviewed
            existing = await self._submissions.get_by_id(submission_id)
            if existing is None:
                raise SubmissionNotFoundError("Submission not found")
            raise ReviewConflictError("Submission is not pending review")

        verification: SubmissionVerification = bundle["verification"]
        contributor = bundle["contributor"]
        if contributor is None or not contributor.telegram_id:
            raise ReviewConflictError("Submission has no agent telegram_id")

        # Close pending row by replacing with final outcome row pattern:
        # schema allows one pending + one final via unique on (submission_id, outcome)
        # and one final overall. Update the pending row in place to final outcome.
        verification.outcome = (
            ReviewOutcome.ACCEPTED if accepted else ReviewOutcome.FLAGGED
        )
        verification.reviewer_label = label
        verification.reason = note
        verification.reason_code = reason_code
        if not accepted and not verification.reason:
            raise SubmissionValidationError("reason is required when flagging")

        await self._scores.apply_review(
            contributor.telegram_id,
            accepted=accepted,
            commit=False,
        )
        await self._session.commit()
        await self._session.refresh(verification)
        return self._to_item(bundle)

    async def _run_triage(self, bundle: dict) -> TriageResult:
        submission = bundle["submission"]
        market = bundle["market"]
        commodity = bundle["commodity"]
        contributor = bundle["contributor"]
        if submission.market_id is None or submission.commodity_id is None:
            raise ReviewConflictError("Submission missing market/commodity")
        if submission.price_canonical is None:
            raise ReviewConflictError("Submission missing price")

        market_prices = await self._submissions.list_accepted_prices(
            market_id=submission.market_id,
            commodity_id=submission.commodity_id,
            exclude_submission_id=submission.id,
            limit=20,
        )
        agent_prices: list[Decimal] = []
        agent_score = 0
        accepted_count = 0
        flagged_count = 0
        if contributor is not None:
            agent_score = int(contributor.reputation_score or 0)
            accepted_count = int(contributor.accepted_count or 0)
            flagged_count = int(contributor.flagged_count or 0)
            agent_prices = await self._submissions.list_contributor_prices(
                contributor_id=contributor.id,
                commodity_id=submission.commodity_id,
                exclude_submission_id=submission.id,
                limit=10,
            )

        facts = self._triage.build_facts(
            market_code=market.code,
            commodity_code=commodity.code,
            price=Decimal(str(submission.price_canonical)),
            unit=str(submission.unit_canonical or commodity.canonical_unit),
            agent_score=agent_score,
            agent_accepted_count=accepted_count,
            agent_flagged_count=flagged_count,
            same_market_accepted_prices=market_prices,
            same_agent_recent_prices=agent_prices,
        )
        return await self._triage.triage(facts)

    @staticmethod
    def _apply_ai(verification: SubmissionVerification, result: TriageResult) -> None:
        verification.ai_verdict = result.verdict
        verification.ai_confidence = result.confidence
        verification.ai_reason = result.reason
        verification.ai_model = result.model
        verification.ai_checked_at = datetime.now(UTC)

    def _to_item(self, bundle: dict) -> dict:
        submission = bundle["submission"]
        verification = bundle["verification"]
        market = bundle["market"]
        commodity = bundle["commodity"]
        contributor = bundle["contributor"]
        market_label = None
        if submission.raw_text and str(submission.raw_text).startswith("other_market:"):
            market_label = str(submission.raw_text).removeprefix("other_market:")

        return {
            "submission_id": submission.id,
            "client_submission_id": submission.client_submission_id,
            "received_at": submission.received_at,
            "observed_at": submission.observed_at,
            "market_code": market.code,
            "market_name_en": market.name_en,
            "market_label": market_label,
            "commodity_code": commodity.code,
            "commodity_name_en": commodity.name_en,
            "price": submission.price_canonical,
            "unit": submission.unit_canonical,
            "review_status": verification.outcome.value,
            "telegram_id": None if contributor is None else contributor.telegram_id,
            "agent_score": None if contributor is None else contributor.reputation_score,
            "ai_verdict": verification.ai_verdict,
            "ai_confidence": verification.ai_confidence,
            "ai_reason": verification.ai_reason,
            "ai_model": verification.ai_model,
            "ai_checked_at": verification.ai_checked_at,
            "comparison_facts": None,
        }
