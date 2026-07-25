from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_affordability_service
from app.services.affordability import AffordabilityService

router = APIRouter(tags=["affordability"])


@router.get("/affordability")
async def get_affordability(
    service: Annotated[AffordabilityService, Depends(get_affordability_service)],
    basket: str = Query(default="phase1_staple5"),
    household_size: int = Query(default=5, ge=1),
    compare_days: int = Query(default=30, ge=1, le=366),
) -> dict:
    return await service.get_affordability(
        basket_code=basket,
        household_size=household_size,
        compare_days=compare_days,
    )


@router.get("/meb/food-line")
async def get_meb_food_line(
    service: Annotated[AffordabilityService, Depends(get_affordability_service)],
    household_size: int = Query(default=5, ge=1),
) -> dict:
    return await service.get_meb_food_line(household_size=household_size)
