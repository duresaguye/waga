from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_applications import AgentApplication, AgentApplicationStatus
from app.models.contributors import Contributor
from app.models.enums import ContributorKind
from app.repositories.agent_applications import AgentApplicationRepository
from app.repositories.contributors import ContributorRepository
from app.services.exceptions import (
    AgentApplicationConflictError,
    AgentApplicationNotFoundError,
    AgentScoreError,
)


class AgentApplicationService:
    def __init__(
        self,
        session: AsyncSession,
        applications: AgentApplicationRepository,
        contributors: ContributorRepository,
    ) -> None:
        self._session = session
        self._applications = applications
        self._contributors = contributors

    async def submit_application(
        self,
        *,
        telegram_id: str,
        telegram_username: str | None,
        full_name: str,
        phone_number: str,
        city: str,
        subcity: str | None,
        preferred_market_code: str,
        visit_frequency: str,
        languages: str | None,
        notes: str | None,
        consent_honest_reporting: bool,
    ) -> AgentApplication:
        telegram_id = telegram_id.strip()
        if not consent_honest_reporting:
            raise AgentScoreError("Honest reporting consent is required")

        existing_agent = await self._contributors.get_by_telegram_id(telegram_id)
        if existing_agent is not None and existing_agent.is_agent and not existing_agent.banned:
            raise AgentApplicationConflictError("Already an approved agent")

        pending = await self._applications.get_pending_by_telegram_id(telegram_id)
        if pending is not None:
            raise AgentApplicationConflictError("Application already pending review")

        application = AgentApplication(
            id=uuid4(),
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            full_name=full_name.strip(),
            phone_number=phone_number.strip(),
            city=city.strip() or "Addis Ababa",
            subcity=subcity.strip() if subcity else None,
            preferred_market_code=preferred_market_code.strip(),
            visit_frequency=visit_frequency.strip(),
            languages=languages.strip() if languages else None,
            notes=notes.strip() if notes else None,
            consent_honest_reporting=True,
            status=AgentApplicationStatus.PENDING,
        )
        self._applications.add(application)
        await self._session.commit()
        await self._session.refresh(application)
        return application

    async def list_applications(
        self, status: AgentApplicationStatus | None = None
    ) -> list[AgentApplication]:
        return await self._applications.list_by_status(status)

    async def approve(
        self,
        application_id: UUID,
        *,
        reviewer_user_id: UUID | None,
        review_note: str | None = None,
    ) -> AgentApplication:
        application = await self._applications.get_by_id(application_id)
        if application is None:
            raise AgentApplicationNotFoundError("Application not found")
        if application.status != AgentApplicationStatus.PENDING:
            raise AgentApplicationConflictError("Application is not pending")

        contributor = await self._contributors.get_by_telegram_id(application.telegram_id)
        if contributor is None:
            contributor = Contributor(
                id=uuid4(),
                user_id=None,
                external_id=uuid4(),
                kind=ContributorKind.AGENT,
                telegram_id=application.telegram_id,
                full_name=application.full_name,
                phone_number=application.phone_number,
                city=application.city,
                is_agent=True,
                reputation_score=0,
                pending_count=0,
                accepted_count=0,
                flagged_count=0,
                redeemed_total=0,
                banned=False,
            )
            self._contributors.add(contributor)
            # Flush before linking application.contributor_id (FK to contributors).
            await self._session.flush()
        else:
            contributor.is_agent = True
            contributor.kind = ContributorKind.AGENT
            contributor.full_name = application.full_name
            contributor.phone_number = application.phone_number
            contributor.city = application.city
            contributor.banned = False
            contributor.ban_reason = None

        application.status = AgentApplicationStatus.APPROVED
        application.review_note = review_note
        application.reviewed_by_user_id = reviewer_user_id
        application.reviewed_at = datetime.now(UTC)
        application.contributor_id = contributor.id

        await self._session.commit()
        await self._session.refresh(application)
        return application

    async def reject(
        self,
        application_id: UUID,
        *,
        reviewer_user_id: UUID | None,
        review_note: str | None = None,
    ) -> AgentApplication:
        application = await self._applications.get_by_id(application_id)
        if application is None:
            raise AgentApplicationNotFoundError("Application not found")
        if application.status != AgentApplicationStatus.PENDING:
            raise AgentApplicationConflictError("Application is not pending")

        application.status = AgentApplicationStatus.REJECTED
        application.review_note = review_note
        application.reviewed_by_user_id = reviewer_user_id
        application.reviewed_at = datetime.now(UTC)
        await self._session.commit()
        await self._session.refresh(application)
        return application
