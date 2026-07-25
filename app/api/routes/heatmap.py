from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_intelligence_service
from app.schemas.intelligence import Envelope
from app.services.intelligence import IntelligenceService

router = APIRouter(tags=["heatmap"])


@router.get("/heatmap", response_model=Envelope)
async def get_heatmap(
    service: Annotated[IntelligenceService, Depends(get_intelligence_service)],
    metric: Literal["pct_change_7d", "pct_change_30d"] = "pct_change_7d",
    commodity: Annotated[list[str] | None, Query()] = None,
) -> Envelope:
    return await service.heatmap(metric=metric, commodity_codes=commodity)
