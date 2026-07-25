from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_alerts_service
from app.services.alerts import AlertsService

router = APIRouter(tags=["alerts"])


@router.get("/alerts")
async def get_alerts(
    service: Annotated[AlertsService, Depends(get_alerts_service)],
    min_band: str = Query(default="stress"),
) -> dict:
    return await service.get_alerts(min_band=min_band)
