from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reward_settings import AgentRedeemRequest, AgentRewardSettings


class RewardSettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active(self) -> AgentRewardSettings | None:
        statement = (
            select(AgentRewardSettings)
            .where(AgentRewardSettings.is_active.is_(True))
            .order_by(AgentRewardSettings.updated_at.desc())
            .limit(1)
        )
        return cast(AgentRewardSettings | None, await self._session.scalar(statement))

    def add_settings(self, settings: AgentRewardSettings) -> None:
        self._session.add(settings)

    def add_redeem_request(self, request: AgentRedeemRequest) -> None:
        self._session.add(request)

    async def list_redeem_requests(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[AgentRedeemRequest]:
        statement = select(AgentRedeemRequest).order_by(
            AgentRedeemRequest.created_at.desc()
        )
        if status is not None:
            statement = statement.where(AgentRedeemRequest.status == status)
        statement = statement.limit(limit)
        result = await self._session.scalars(statement)
        return list(result)

    async def get_redeem_request(self, request_id: UUID) -> AgentRedeemRequest | None:
        statement = select(AgentRedeemRequest).where(AgentRedeemRequest.id == request_id)
        return cast(AgentRedeemRequest | None, await self._session.scalar(statement))

    async def resolve_redeem_request(
        self,
        request: AgentRedeemRequest,
        *,
        status: str,
        admin_note: str | None,
    ) -> AgentRedeemRequest:
        request.status = status
        request.admin_note = admin_note
        request.resolved_at = datetime.now(UTC)
        await self._session.commit()
        await self._session.refresh(request)
        return request