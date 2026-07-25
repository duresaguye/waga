from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_intelligence_service
from app.schemas.intelligence import CopilotAskRequest, Envelope, ImpactAskRequest
from app.services.intelligence import IntelligenceService

router = APIRouter(tags=["copilot"])


@router.post("/copilot/ask", response_model=Envelope)
async def copilot_ask(
    body: CopilotAskRequest,
    service: Annotated[IntelligenceService, Depends(get_intelligence_service)],
) -> Envelope:
    return await service.copilot_ask(
        question=body.question,
        household_count=body.household_count,
        language=body.language,
    )


@router.post("/impact", response_model=Envelope)
async def impact(
    body: ImpactAskRequest,
    service: Annotated[IntelligenceService, Depends(get_intelligence_service)],
) -> Envelope:
    return await service.impact(
        household_count=body.household_count,
        compare_days=body.compare_days,
    )
