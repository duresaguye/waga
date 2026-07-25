from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ReviewOutcome
from app.models.submissions import Submission
from app.models.verification import SubmissionVerification


class SubmissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, submission: Submission) -> None:
        self._session.add(submission)

    def add_verification(self, verification: SubmissionVerification) -> None:
        self._session.add(verification)

    async def get_by_id(self, submission_id: UUID) -> Submission | None:
        return cast(Submission | None, await self._session.get(Submission, submission_id))

    async def get_by_client_submission_id(
        self,
        *,
        contributor_id: UUID,
        client_submission_id: UUID,
    ) -> Submission | None:
        statement = select(Submission).where(
            Submission.contributor_id == contributor_id,
            Submission.client_submission_id == client_submission_id,
        )
        return cast(Submission | None, await self._session.scalar(statement))

    async def get_pending_verification(
        self, submission_id: UUID
    ) -> SubmissionVerification | None:
        statement = select(SubmissionVerification).where(
            SubmissionVerification.submission_id == submission_id,
            SubmissionVerification.outcome == ReviewOutcome.PENDING,
        )
        return cast(
            SubmissionVerification | None, await self._session.scalar(statement)
        )
