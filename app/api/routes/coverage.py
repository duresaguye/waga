from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_prices_read_service
from app.services.prices_read import PricesReadService

router = APIRouter(tags=["coverage"])


@router.get("/coverage")
async def get_coverage(
    service: Annotated[PricesReadService, Depends(get_prices_read_service)],
) -> dict:
    return await service.get_coverage()
