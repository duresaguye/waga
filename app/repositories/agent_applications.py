from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_applications import AgentApplication, AgentApplicationStatus


class AgentApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, application: AgentApplication) -> None:
        self._session.add(application)

    async def get_by_id(self, application_id: UUID) -> AgentApplication | None:
        statement = select(AgentApplication).where(AgentApplication.id == application_id)
        return cast(AgentApplication | None, await self._session.scalar(statement))

    async def get_pending_by_telegram_id(self, telegram_id: str) -> AgentApplication | None:
        statement = select(AgentApplication).where(
            AgentApplication.telegram_id == telegram_id,
            AgentApplication.status == AgentApplicationStatus.PENDING,
        )
        return cast(AgentApplication | None, await self._session.scalar(statement))

    async def get_latest_by_telegram_id(self, telegram_id: str) -> AgentApplication | None:
        statement = (
            select(AgentApplication)
            .where(AgentApplication.telegram_id == telegram_id)
            .order_by(AgentApplication.created_at.desc())
            .limit(1)
        )
        return cast(AgentApplication | None, await self._session.scalar(statement))

    async def list_by_status(
        self,
        status: AgentApplicationStatus | None = None,
        *,
        limit: int = 100,
    ) -> list[AgentApplication]:
        statement = select(AgentApplication).order_by(AgentApplication.created_at.desc())
        if status is not None:
            statement = statement.where(AgentApplication.status == status)
        statement = statement.limit(limit)
        result = await self._session.scalars(statement)
        return list(result)
