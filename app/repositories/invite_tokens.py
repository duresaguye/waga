from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import InviteToken


class InviteTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, invite_token: InviteToken) -> None:
        self._session.add(invite_token)

    async def get_by_hash(
        self,
        token_hash: str,
        *,
        for_update: bool = False,
    ) -> InviteToken | None:
        statement = select(InviteToken).where(InviteToken.token_hash == token_hash)
        if for_update:
            statement = statement.with_for_update()
        return cast(InviteToken | None, await self._session.scalar(statement))

    async def get_by_user_id(self, user_id: UUID) -> InviteToken | None:
        statement = (
            select(InviteToken)
            .where(InviteToken.user_id == user_id, InviteToken.accepted_at.is_(None))
            .order_by(InviteToken.created_at.desc())
        )
        return cast(InviteToken | None, await self._session.scalar(statement))
