from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_research_service
from app.services.research import ResearchService

router = APIRouter(tags=["research"])


@router.get("/research/snapshots")
async def get_snapshots(
    service: Annotated[ResearchService, Depends(get_research_service)],
) -> dict:
    return await service.get_snapshots()


@router.get("/research/methodology")
async def get_methodology(
    service: Annotated[ResearchService, Depends(get_research_service)],
) -> dict:
    return await service.get_methodology()


@router.get("/research/codebook")
async def get_codebook(
    service: Annotated[ResearchService, Depends(get_research_service)],
) -> dict:
    return await service.get_codebook()
