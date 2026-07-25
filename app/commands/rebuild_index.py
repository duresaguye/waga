"""Rebuild index snapshots from accepted submissions."""

from __future__ import annotations

import asyncio

from app.config import get_settings
from app.database import session_factory
from app.repositories.index_values import IndexValueRepository
from app.repositories.reference_data import ReferenceDataRepository
from app.repositories.submissions import SubmissionRepository
from app.services.index_calculation import IndexCalculationService


async def rebuild() -> None:
    settings = get_settings()
    async with session_factory() as session:
        service = IndexCalculationService(
            session,
            SubmissionRepository(session),
            IndexValueRepository(session),
            ReferenceDataRepository(session),
            settings,
        )
        count = await service.rebuild_all()
        print(f"Rebuilt {count} index snapshots.")


def main() -> None:
    asyncio.run(rebuild())


if __name__ == "__main__":
    main()
