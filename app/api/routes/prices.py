from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_intelligence_service
from app.schemas.intelligence import Envelope
from app.services.intelligence import IntelligenceService

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/current", response_model=Envelope)
async def prices_current(
    service: Annotated[IntelligenceService, Depends(get_intelligence_service)],
    market: Annotated[list[str] | None, Query()] = None,
    commodity: Annotated[list[str] | None, Query()] = None,
    include_insufficient: bool = True,
) -> Envelope:
    return await service.current_prices(
        market_codes=market,
        commodity_codes=commodity,
        include_insufficient=include_insufficient,
    )


@router.get("/series", response_model=Envelope)
async def prices_series(
    service: Annotated[IntelligenceService, Depends(get_intelligence_service)],
    commodity: Annotated[list[str] | None, Query()] = None,
    market: Annotated[list[str] | None, Query()] = None,
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: Annotated[date | None, Query()] = None,
    interval: str = "day",
) -> Envelope:
    return await service.price_series(
        commodity_codes=commodity,
        market_codes=market,
        from_date=from_,
        to_date=to,
        interval=interval,
    )
