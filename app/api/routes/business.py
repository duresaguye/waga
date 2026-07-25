from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.dependencies import get_business_service
from app.services.api_errors import contract_error
from app.services.business import BusinessService

router = APIRouter(tags=["business"])


class BusinessBenchmarkRequest(BaseModel):
    commodity_code: str = Field(min_length=1)
    quoted_price: float = Field(gt=0)
    unit: str = "kg"


class BusinessAskRequest(BaseModel):
    question: str = Field(min_length=1)
    language: str = "en"


def _parse_items(raw_items: list[str]) -> list[tuple[str, float]]:
    parsed: list[tuple[str, float]] = []
    for item in raw_items:
        if ":" not in item:
            raise contract_error(
                "invalid_range",
                "Each items entry must be commodity_code:quantity",
                field="items",
            )
        code, quantity_raw = item.split(":", 1)
        try:
            quantity = float(quantity_raw)
        except ValueError as error:
            raise contract_error(
                "invalid_range",
                f"Invalid quantity in items entry '{item}'",
                field="items",
            ) from error
        if quantity <= 0:
            raise contract_error(
                "invalid_range",
                f"Quantity must be positive in items entry '{item}'",
                field="items",
            )
        parsed.append((code.strip(), quantity))
    if not parsed:
        raise contract_error(
            "invalid_range",
            "At least one items entry is required",
            field="items",
        )
    return parsed


@router.get("/business/cost-index")
async def get_cost_index(
    service: Annotated[BusinessService, Depends(get_business_service)],
    items: Annotated[list[str], Query()],
    base_date: Annotated[date | None, Query()] = None,
) -> dict:
    return await service.get_cost_index(items=_parse_items(items), base_date=base_date)


@router.get("/business/sourcing")
async def get_sourcing(
    service: Annotated[BusinessService, Depends(get_business_service)],
    commodity: Annotated[list[str], Query()],
) -> dict:
    return await service.get_sourcing(commodity_codes=commodity)


@router.post("/business/benchmark")
async def benchmark_quote(
    request: BusinessBenchmarkRequest,
    service: Annotated[BusinessService, Depends(get_business_service)],
) -> dict:
    return await service.benchmark_quote(
        commodity_code=request.commodity_code,
        quoted_price=request.quoted_price,
        unit=request.unit,
    )


@router.post("/business/ask")
async def business_ask(
    request: BusinessAskRequest,
    service: Annotated[BusinessService, Depends(get_business_service)],
) -> dict:
    return await service.ask(question=request.question, language=request.language)
