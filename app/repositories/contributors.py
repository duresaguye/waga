from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contributors import (
    AgentInviteCode,
    AgentScoreEvent,
    Contributor,
    ContributorConsent,
)


class ContributorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, contributor: Contributor) -> None:
        self._session.add(contributor)

    def add_score_event(self, event: AgentScoreEvent) -> None:
        self._session.add(event)

    def add_consent(self, consent: ContributorConsent) -> None:
        self._session.add(consent)

    async def get_consent(
        self, contributor_id: UUID, consent_version: str
    ) -> ContributorConsent | None:
        statement = select(ContributorConsent).where(
            ContributorConsent.contributor_id == contributor_id,
            ContributorConsent.consent_version == consent_version,
        )
        return cast(ContributorConsent | None, await self._session.scalar(statement))

    async def get_by_user_id(self, user_id: UUID) -> Contributor | None:
        statement = select(Contributor).where(Contributor.user_id == user_id)
        return cast(Contributor | None, await self._session.scalar(statement))

    async def get_by_id(self, contributor_id: UUID) -> Contributor | None:
        statement = select(Contributor).where(Contributor.id == contributor_id)
        return cast(Contributor | None, await self._session.scalar(statement))

    async def get_by_telegram_id(self, telegram_id: str) -> Contributor | None:
        statement = select(Contributor).where(Contributor.telegram_id == telegram_id)
        return cast(Contributor | None, await self._session.scalar(statement))

    async def get_invite_by_code(self, code: str) -> AgentInviteCode | None:
        normalized = code.strip().lower()
        statement = select(AgentInviteCode).where(
            func.lower(AgentInviteCode.code) == normalized
        )
        return cast(AgentInviteCode | None, await self._session.scalar(statement))

    async def get_invite_by_id(self, invite_id: UUID) -> AgentInviteCode | None:
        return cast(
            AgentInviteCode | None, await self._session.get(AgentInviteCode, invite_id)
        )

    async def list_invites(self, *, limit: int = 50) -> list[AgentInviteCode]:
        statement = (
            select(AgentInviteCode)
            .order_by(AgentInviteCode.created_at.desc())
            .limit(limit)
        )
        return list(await self._session.scalars(statement))

    def add_invite(self, invite: AgentInviteCode) -> None:
        self._session.add(invite)
