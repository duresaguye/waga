from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies import get_brief_service
from app.services.brief import BriefService

router = APIRouter(tags=["briefs"])


class MonthlyBriefRequest(BaseModel):
    household_count: int = Field(default=50000, ge=1)
    language: str = "en"


@router.post("/briefs/monthly")
async def monthly_brief(
    request: MonthlyBriefRequest,
    service: Annotated[BriefService, Depends(get_brief_service)],
) -> dict:
    """One-click NGO monthly brief (markdown) from published index facts."""
    return await service.monthly(
        household_count=request.household_count,
        language=request.language,
    )
