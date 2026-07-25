from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_intelligence_service
from app.schemas.intelligence import Envelope
from app.services.intelligence import IntelligenceService

router = APIRouter(tags=["affordability"])


@router.get("/affordability", response_model=Envelope)
async def get_affordability(
    service: Annotated[IntelligenceService, Depends(get_intelligence_service)],
    basket: str = "phase1_staple5",
    household_size: Annotated[int, Query(ge=1, le=20)] = 5,
    compare_days: Annotated[int, Query(ge=1, le=366)] = 30,
) -> Envelope:
    return await service.affordability(
        basket=basket,
        household_size=household_size,
        compare_days=compare_days,
    )
