from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_heatmap_service
from app.services.heatmap import HeatmapService

router = APIRouter(tags=["heatmap"])


@router.get("/heatmap")
async def get_heatmap(
    service: Annotated[HeatmapService, Depends(get_heatmap_service)],
    metric: str = Query(default="pct_change_7d"),
    commodity: str | None = None,
) -> dict:
    return await service.get_heatmap(metric=metric, commodity_code=commodity)
