from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_submission_service
from app.schemas.submissions import (
    SubmissionCreate,
    SubmissionCreateResponse,
    SubmissionScoreSnapshot,
)
from app.services.exceptions import (
    AgentBannedError,
    SubmissionConflictError,
    SubmissionValidationError,
)
from app.services.submissions import SubmissionService

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post(
    "",
    response_model=SubmissionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_submission(
    body: SubmissionCreate,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionCreateResponse:
    """Create a pending price report (Telegram bot / structured clients)."""
    try:
        submission, score, market_label = await service.create_from_bot(
            client_submission_id=body.client_submission_id,
            external_contributor_id=body.external_contributor_id,
            market_code=body.market_code,
            commodity_code=body.commodity_code,
            price=body.price,
            unit=body.unit,
            consent_version=body.consent_version,
            input_mode=body.input_mode,
            source=body.source,
            telegram_username=body.telegram_username,
            market_label=body.market_label,
            observed_at=body.observed_at,
        )
    except AgentBannedError as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    except SubmissionValidationError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except SubmissionConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error

    ban_reason = score.get("ban_reason")
    return SubmissionCreateResponse(
        id=submission.id,
        client_submission_id=submission.client_submission_id,
        market_code=body.market_code,
        commodity_code=body.commodity_code,
        price=submission.price_canonical or body.price,
        unit=submission.unit_canonical or body.unit,
        review_status="pending",
        market_label=market_label,
        score=SubmissionScoreSnapshot(
            score=int(score["score"]),
            status=str(score["status"]),
            pending_count=int(score["pending_count"]),
            accepted_count=int(score["accepted_count"]),
            flagged_count=int(score["flagged_count"]),
            banned=bool(score["banned"]),
            ban_reason=None if ban_reason is None else str(ban_reason),
        ),
    )
