from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contributors import Contributor


class ContributorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, contributor: Contributor) -> None:
        self._session.add(contributor)

    async def get_by_user_id(self, user_id: UUID) -> Contributor | None:
        statement = select(Contributor).where(Contributor.user_id == user_id)
        return cast(Contributor | None, await self._session.scalar(statement))
