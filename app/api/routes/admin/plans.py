from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_subscription_plan_service, require_roles
from app.models.enums import UserRole
from app.schemas.subscription_plans import (
    SubscriptionPlanCreate,
    SubscriptionPlanResponse,
    SubscriptionPlanUpdate,
)
from app.services.exceptions import PlanConflictError, PlanInUseError, PlanNotFoundError
from app.services.subscription_plans import SubscriptionPlanService

router = APIRouter(
    prefix="/plans",
    tags=["admin-plans"],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.OPERATOR))],
)


@router.get("", response_model=list[SubscriptionPlanResponse])
async def list_plans(
    service: Annotated[SubscriptionPlanService, Depends(get_subscription_plan_service)],
    active_only: Annotated[bool, Query()] = False,
) -> list[SubscriptionPlanResponse]:
    plans = await service.list_plans(active_only=active_only)
    return [SubscriptionPlanResponse.model_validate(plan) for plan in plans]


@router.post(
    "",
    response_model=SubscriptionPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_plan(
    request: SubscriptionPlanCreate,
    service: Annotated[SubscriptionPlanService, Depends(get_subscription_plan_service)],
) -> SubscriptionPlanResponse:
    try:
        plan = await service.create_plan(**request.model_dump())
    except PlanConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error
    return SubscriptionPlanResponse.model_validate(plan)


@router.get("/{plan_id}", response_model=SubscriptionPlanResponse)
async def get_plan(
    plan_id: UUID,
    service: Annotated[SubscriptionPlanService, Depends(get_subscription_plan_service)],
) -> SubscriptionPlanResponse:
    try:
        plan = await service.get_plan(plan_id)
    except PlanNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return SubscriptionPlanResponse.model_validate(plan)


@router.patch("/{plan_id}", response_model=SubscriptionPlanResponse)
async def update_plan(
    plan_id: UUID,
    request: SubscriptionPlanUpdate,
    service: Annotated[SubscriptionPlanService, Depends(get_subscription_plan_service)],
) -> SubscriptionPlanResponse:
    try:
        plan = await service.update_plan(plan_id, **request.model_dump(exclude_unset=True))
    except PlanNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except PlanConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error
    return SubscriptionPlanResponse.model_validate(plan)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: UUID,
    service: Annotated[SubscriptionPlanService, Depends(get_subscription_plan_service)],
) -> None:
    try:
        await service.delete_plan(plan_id)
    except PlanNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except PlanInUseError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error
