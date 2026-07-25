from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies import get_copilot_service
from app.services.copilot import CopilotService

router = APIRouter(tags=["copilot"])


class CopilotAskRequest(BaseModel):
    question: str = Field(min_length=1)
    household_count: int | None = Field(default=None, ge=1)
    language: str = "en"


class ImpactRequest(BaseModel):
    household_count: int = Field(ge=1)
    gap_per_household_etb: float = Field(ge=0)
    months: int = Field(default=1, ge=1, le=12)


@router.post("/copilot/ask")
async def ask_copilot(
    request: CopilotAskRequest,
    service: Annotated[CopilotService, Depends(get_copilot_service)],
) -> dict:
    return await service.ask(
        question=request.question,
        household_count=request.household_count,
        language=request.language,
    )


@router.post("/impact")
async def calculate_impact(
    request: ImpactRequest,
    service: Annotated[CopilotService, Depends(get_copilot_service)],
) -> dict:
    return await service.impact(
        household_count=request.household_count,
        gap_per_household_etb=request.gap_per_household_etb,
        months=request.months,
    )
