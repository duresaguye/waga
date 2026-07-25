from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_agent_score_service, get_reward_settings_repository, require_roles
from app.models.enums import UserRole
from app.repositories.reward_settings import RewardSettingsRepository
from app.schemas.rewards import (
    AgentRedeemRequestResponse,
    AgentRedeemResolveRequest,
    AgentRewardSettingsResponse,
    AgentRewardSettingsUpdate,
)
from app.services.agent_score import AgentScoreService

router = APIRouter(
    prefix="/agent-rewards",
    tags=["admin-agent-rewards"],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.OPERATOR))],
)


@router.get("/settings", response_model=AgentRewardSettingsResponse)
async def get_reward_settings(
    service: Annotated[AgentScoreService, Depends(get_agent_score_service)],
) -> AgentRewardSettingsResponse:
    settings = await service.get_reward_settings()
    return AgentRewardSettingsResponse(
        id=settings.id,
        birr_per_point=settings.birr_per_point,
        redeem_min_points=settings.redeem_min_points,
        currency_code=settings.currency_code,
        is_active=settings.is_active,
        example=service.settings_example(settings),
    )


@router.put("/settings", response_model=AgentRewardSettingsResponse)
async def update_reward_settings(
    body: AgentRewardSettingsUpdate,
    service: Annotated[AgentScoreService, Depends(get_agent_score_service)],
) -> AgentRewardSettingsResponse:
    """Admin sets how many birr each score point is worth."""
    settings = await service.update_reward_settings(
        birr_per_point=body.birr_per_point,
        redeem_min_points=body.redeem_min_points,
        currency_code=body.currency_code,
    )
    return AgentRewardSettingsResponse(
        id=settings.id,
        birr_per_point=settings.birr_per_point,
        redeem_min_points=settings.redeem_min_points,
        currency_code=settings.currency_code,
        is_active=settings.is_active,
        example=service.settings_example(settings),
    )


@router.get("/redeem-requests", response_model=list[AgentRedeemRequestResponse])
async def list_redeem_requests(
    rewards: Annotated[RewardSettingsRepository, Depends(get_reward_settings_repository)],
    status_filter: Annotated[str | None, Query(alias="status")] = "pending",
) -> list[AgentRedeemRequestResponse]:
    rows = await rewards.list_redeem_requests(status=status_filter)
    return [AgentRedeemRequestResponse.model_validate(row) for row in rows]


@router.post(
    "/redeem-requests/{request_id}/resolve",
    response_model=AgentRedeemRequestResponse,
)
async def resolve_redeem_request(
    request_id: UUID,
    body: AgentRedeemResolveRequest,
    rewards: Annotated[RewardSettingsRepository, Depends(get_reward_settings_repository)],
) -> AgentRedeemRequestResponse:
    row = await rewards.get_redeem_request(request_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Redeem request not found")
    if row.status != "pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Request already resolved")

    row = await rewards.resolve_redeem_request(
        row,
        status=body.status,
        admin_note=body.admin_note,
    )
    return AgentRedeemRequestResponse.model_validate(row)
