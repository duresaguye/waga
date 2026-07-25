from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_agent_score_service, require_roles
from app.models.enums import UserRole
from app.schemas.agents import AgentInviteCreateRequest, AgentInviteResponse
from app.services.agent_score import AgentScoreService
from app.services.exceptions import AgentInviteInvalidError, AgentScoreError

router = APIRouter(
    prefix="/agent-invites",
    tags=["admin-agent-invites"],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.OPERATOR))],
)


@router.post(
    "",
    response_model=AgentInviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_agent_invite(
    service: Annotated[AgentScoreService, Depends(get_agent_score_service)],
    body: AgentInviteCreateRequest | None = None,
) -> AgentInviteResponse:
    """Generate a hard-to-guess invite code to send to one agent."""
    max_uses = 1 if body is None else body.max_uses
    try:
        invite = await service.create_invite(max_uses=max_uses)
    except AgentScoreError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return AgentInviteResponse.from_invite(invite)


@router.get("", response_model=list[AgentInviteResponse])
async def list_agent_invites(
    service: Annotated[AgentScoreService, Depends(get_agent_score_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[AgentInviteResponse]:
    invites = await service.list_invites(limit=limit)
    return [AgentInviteResponse.from_invite(row) for row in invites]


@router.post("/{invite_id}/deactivate", response_model=AgentInviteResponse)
async def deactivate_agent_invite(
    invite_id: UUID,
    service: Annotated[AgentScoreService, Depends(get_agent_score_service)],
) -> AgentInviteResponse:
    try:
        invite = await service.deactivate_invite(invite_id)
    except AgentInviteInvalidError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return AgentInviteResponse.from_invite(invite)
