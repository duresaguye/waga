from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.config import settings
from app.dependencies import (
    get_optional_user,
    get_prices_read_service,
    get_subscription_context,
    get_subscription_service,
)
from app.models.auth import User
from app.services.prices_read import PricesReadService
from app.services.subscriptions import SubscriptionContext, SubscriptionService

router = APIRouter(tags=["reference"])


@router.get("/reference")
async def get_reference(
    service: Annotated[PricesReadService, Depends(get_prices_read_service)],
) -> dict:
    return await service.get_reference()


@router.get("/prices/current")
async def get_current_prices(
    service: Annotated[PricesReadService, Depends(get_prices_read_service)],
    market: Annotated[list[str] | None, Query()] = None,
    commodity: Annotated[list[str] | None, Query()] = None,
    include_insufficient: bool = True,
) -> dict:
    return await service.get_current_prices(
        market_codes=market,
        commodity_codes=commodity,
        include_insufficient=include_insufficient,
    )


@router.get("/prices/series")
async def get_price_series(
    service: Annotated[PricesReadService, Depends(get_prices_read_service)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    context: Annotated[SubscriptionContext, Depends(get_subscription_context)],
    optional_user: Annotated[User | None, Depends(get_optional_user)],
    commodity: Annotated[list[str], Query()],
    market: Annotated[list[str] | None, Query()] = None,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    interval: str = "day",
) -> dict:
    _ = interval
    end = to_date or date.today()
    start = from_date or end.replace(day=max(1, end.day - 30))
    history_depth = settings.public_history_days
    if context.subscription is not None:
        subscriber_depth = subscription_service.history_depth_days(context.subscription)
        if subscriber_depth is not None:
            history_depth = subscriber_depth
    elif optional_user is not None:
        history_depth = settings.public_history_days
    return await service.get_series(
        commodity_codes=commodity,
        market_codes=market,
        start=start,
        end=end,
        history_depth_days=history_depth,
    )
