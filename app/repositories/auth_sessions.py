from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import AuthSession


class AuthSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, auth_session: AuthSession) -> None:
        self._session.add(auth_session)

    async def get_by_refresh_hash(
        self,
        refresh_token_hash: str,
        *,
        for_update: bool = False,
    ) -> AuthSession | None:
        statement = select(AuthSession).where(AuthSession.refresh_token_hash == refresh_token_hash)
        if for_update:
            statement = statement.with_for_update()
        return cast(AuthSession | None, await self._session.scalar(statement))

    async def revoke_family(self, family_id: UUID, revoked_at: datetime) -> None:
        statement = (
            update(AuthSession)
            .where(
                AuthSession.session_family_id == family_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        await self._session.execute(statement)

    async def revoke_all_for_user(self, user_id: UUID, revoked_at: datetime) -> None:
        statement = (
            update(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        await self._session.execute(statement)
