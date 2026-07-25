from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_agent_application_service, get_current_user, require_roles
from app.models.auth import User
from app.models.agent_applications import AgentApplicationStatus
from app.models.enums import UserRole
from app.schemas.applications import (
    AgentApplicationRejectRequest,
    AgentApplicationResponse,
)
from app.services.agent_applications import AgentApplicationService
from app.services.exceptions import (
    AgentApplicationConflictError,
    AgentApplicationNotFoundError,
)

router = APIRouter(
    prefix="/agent-applications",
    tags=["admin-agent-applications"],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.OPERATOR))],
)


@router.get("", response_model=list[AgentApplicationResponse])
async def list_applications(
    service: Annotated[AgentApplicationService, Depends(get_agent_application_service)],
    status_filter: Annotated[str | None, Query(alias="status")] = "pending",
) -> list[AgentApplicationResponse]:
    parsed: AgentApplicationStatus | None = None
    if status_filter:
        try:
            parsed = AgentApplicationStatus(status_filter)
        except ValueError as error:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="status must be pending, approved, or rejected",
            ) from error
    rows = await service.list_applications(parsed)
    return [AgentApplicationResponse.model_validate(row) for row in rows]


@router.post("/{application_id}/approve", response_model=AgentApplicationResponse)
async def approve_application(
    application_id: UUID,
    service: Annotated[AgentApplicationService, Depends(get_agent_application_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AgentApplicationResponse:
    try:
        row = await service.approve(
            application_id,
            reviewer_user_id=current_user.id,
        )
    except AgentApplicationNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except AgentApplicationConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error
    return AgentApplicationResponse.model_validate(row)


@router.post("/{application_id}/reject", response_model=AgentApplicationResponse)
async def reject_application(
    application_id: UUID,
    body: AgentApplicationRejectRequest,
    service: Annotated[AgentApplicationService, Depends(get_agent_application_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AgentApplicationResponse:
    try:
        row = await service.reject(
            application_id,
            reviewer_user_id=current_user.id,
            review_note=body.review_note,
        )
    except AgentApplicationNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except AgentApplicationConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error
    return AgentApplicationResponse.model_validate(row)
