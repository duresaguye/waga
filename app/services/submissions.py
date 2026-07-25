from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contributors import ContributorConsent
from app.models.enums import (
    InputMode,
    LicenceClass,
    ParseMethod,
    ParseStatus,
    ReviewOutcome,
    SubmissionSource,
)
from app.models.submissions import Submission
from app.models.verification import SubmissionVerification
from app.repositories.contributors import ContributorRepository
from app.repositories.reference_data import ReferenceDataRepository
from app.repositories.submissions import SubmissionRepository
from app.services.agent_score import AgentScoreService
from app.services.exceptions import (
    AgentBannedError,
    AgentNotFoundError,
    SubmissionConflictError,
    SubmissionValidationError,
)

OTHER_MARKET_CODE = "other"


class SubmissionService:
    def __init__(
        self,
        session: AsyncSession,
        submissions: SubmissionRepository,
        reference: ReferenceDataRepository,
        contributors: ContributorRepository,
        scores: AgentScoreService,
    ) -> None:
        self._session = session
        self._submissions = submissions
        self._reference = reference
        self._contributors = contributors
        self._scores = scores

    async def create_from_bot(
        self,
        *,
        client_submission_id: UUID,
        external_contributor_id: str,
        market_code: str,
        commodity_code: str,
        price: Decimal,
        unit: str,
        consent_version: str,
        input_mode: str = "telegram",
        source: str = "user",
        telegram_username: str | None = None,
        market_label: str | None = None,
        observed_at: datetime | None = None,
    ) -> tuple[Submission, dict[str, object], str | None]:
        telegram_id = self._parse_telegram_id(external_contributor_id)
        _ = telegram_username  # reserved for future audit trail

        try:
            contributor = await self._scores.ensure_agent(telegram_id)
        except AgentNotFoundError as error:
            raise SubmissionValidationError(
                "Only approved market agents can submit prices"
            ) from error

        if contributor.banned:
            raise AgentBannedError(contributor.ban_reason or "Agent is banned")

        existing = await self._submissions.get_by_client_submission_id(
            contributor_id=contributor.id,
            client_submission_id=client_submission_id,
        )
        if existing is not None:
            score = await self._scores.to_score_dict(contributor)
            label = self._extract_market_label(existing.raw_text)
            return existing, score, label

        market = await self._reference.get_market_by_code(market_code)
        if market is None or not market.is_active:
            raise SubmissionValidationError(f"Unknown market_code: {market_code}")

        commodity = await self._reference.get_commodity_by_code(commodity_code)
        if commodity is None or not commodity.is_active:
            raise SubmissionValidationError(
                f"Unknown commodity_code: {commodity_code}"
            )

        normalized_unit = unit.strip().lower()
        if normalized_unit != commodity.canonical_unit.lower():
            raise SubmissionValidationError(
                f"Unit must be '{commodity.canonical_unit}' for {commodity.code}"
            )

        cleaned_label: str | None = None
        if market.code == OTHER_MARKET_CODE:
            cleaned_label = (market_label or "").strip()
            if not cleaned_label:
                raise SubmissionValidationError(
                    "market_label is required when market_code is 'other'"
                )

        await self._ensure_consent(contributor.id, consent_version)

        raw_text = None
        if cleaned_label:
            raw_text = f"other_market:{cleaned_label}"

        try:
            input_mode_enum = InputMode(input_mode)
        except ValueError as error:
            raise SubmissionValidationError(
                f"Unsupported input_mode: {input_mode}"
            ) from error

        try:
            source_enum = SubmissionSource(source)
        except ValueError as error:
            raise SubmissionValidationError(f"Unsupported source: {source}") from error

        submission = Submission(
            id=uuid4(),
            client_submission_id=client_submission_id,
            contributor_id=contributor.id,
            market_id=market.id,
            commodity_id=commodity.id,
            price_raw=price,
            unit_raw=normalized_unit,
            price_canonical=price,
            unit_canonical=normalized_unit,
            raw_text=raw_text,
            observed_at=observed_at or datetime.now(UTC),
            source=source_enum,
            licence_class=LicenceClass.INTERNAL_ONLY,
            parse_status=ParseStatus.PARSED,
            parse_method=ParseMethod.STRUCTURED,
            input_mode=input_mode_enum,
        )
        self._submissions.add(submission)
        self._submissions.add_verification(
            SubmissionVerification(
                id=uuid4(),
                submission_id=submission.id,
                outcome=ReviewOutcome.PENDING,
                reviewer_label=None,
                reason_code=None,
                reason=None,
            )
        )

        try:
            contributor = await self._scores.record_pending_submit(
                telegram_id, commit=False
            )
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            existing = await self._submissions.get_by_client_submission_id(
                contributor_id=contributor.id,
                client_submission_id=client_submission_id,
            )
            if existing is not None:
                score = await self._scores.to_score_dict(contributor)
                return existing, score, cleaned_label
            raise SubmissionConflictError("Could not create submission") from error

        await self._session.refresh(submission)
        await self._session.refresh(contributor)
        score = await self._scores.to_score_dict(contributor)
        return submission, score, cleaned_label

    async def _ensure_consent(
        self, contributor_id: UUID, consent_version: str
    ) -> None:
        version = consent_version.strip()
        if not version:
            raise SubmissionValidationError("consent_version is required")
        existing = await self._contributors.get_consent(contributor_id, version)
        if existing is not None:
            return
        self._contributors.add_consent(
            ContributorConsent(
                id=uuid4(),
                contributor_id=contributor_id,
                consent_version=version,
            )
        )

    @staticmethod
    def _parse_telegram_id(external_contributor_id: str) -> str:
        value = external_contributor_id.strip()
        prefix = "telegram:"
        if value.lower().startswith(prefix):
            telegram_id = value[len(prefix) :].strip()
        else:
            telegram_id = value
        if not telegram_id.isdigit():
            raise SubmissionValidationError(
                "external_contributor_id must look like telegram:123456789"
            )
        return telegram_id

    @staticmethod
    def _extract_market_label(raw_text: str | None) -> str | None:
        if not raw_text:
            return None
        prefix = "other_market:"
        if raw_text.startswith(prefix):
            return raw_text[len(prefix) :]
        return None
