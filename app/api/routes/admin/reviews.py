from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_user, get_review_service, require_roles
from app.models.auth import User
from app.models.enums import UserRole
from app.schemas.reviews import (
    PendingReviewItem,
    ReviewAcceptRequest,
    ReviewFlagRequest,
)
from app.services.exceptions import (
    ReviewConflictError,
    SubmissionNotFoundError,
    SubmissionValidationError,
)
from app.services.reviews import ReviewService

router = APIRouter(
    prefix="/reviews",
    tags=["admin-reviews"],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.OPERATOR))],
)


@router.get("/pending", response_model=list[PendingReviewItem])
async def list_pending_reviews(
    service: Annotated[ReviewService, Depends(get_review_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[PendingReviewItem]:
    rows = await service.list_pending(limit=limit)
    return [PendingReviewItem.model_validate(row) for row in rows]


@router.post("/{submission_id}/triage", response_model=PendingReviewItem)
async def triage_submission(
    submission_id: UUID,
    service: Annotated[ReviewService, Depends(get_review_service)],
) -> PendingReviewItem:
    try:
        row = await service.triage_submission(submission_id)
    except SubmissionNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ReviewConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error
    return PendingReviewItem.model_validate(row)


@router.post("/{submission_id}/accept", response_model=PendingReviewItem)
async def accept_submission(
    submission_id: UUID,
    service: Annotated[ReviewService, Depends(get_review_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    body: ReviewAcceptRequest | None = None,
) -> PendingReviewItem:
    note = None if body is None else body.note
    try:
        row = await service.accept(
            submission_id,
            reviewer_label=current_user.email,
            note=note,
        )
    except SubmissionNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ReviewConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error
    except SubmissionValidationError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return PendingReviewItem.model_validate(row)


@router.post("/{submission_id}/flag", response_model=PendingReviewItem)
async def flag_submission(
    submission_id: UUID,
    body: ReviewFlagRequest,
    service: Annotated[ReviewService, Depends(get_review_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PendingReviewItem:
    try:
        row = await service.flag(
            submission_id,
            reviewer_label=current_user.email,
            reason=body.reason,
            reason_code=body.reason_code,
        )
    except SubmissionNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ReviewConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error
    except SubmissionValidationError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return PendingReviewItem.model_validate(row)
