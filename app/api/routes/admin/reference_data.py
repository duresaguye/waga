from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_reference_data_service, require_roles
from app.models.enums import UserRole
from app.schemas.reference_data import (
    CommodityCreate,
    CommodityResponse,
    CommodityUpdate,
    MarketCreate,
    MarketResponse,
    MarketUpdate,
    SectorCreate,
    SectorResponse,
    SectorUpdate,
    SynonymCreate,
    SynonymResponse,
    SynonymUpdate,
)
from app.services.exceptions import (
    ReferenceDataConflictError,
    ReferenceDataNotFoundError,
)
from app.services.reference_data import ReferenceDataService

router = APIRouter(
    prefix="/catalogue",
    tags=["admin-catalogue"],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.OPERATOR))],
)


# ── Sectors (Categories) ────────────────────────────────────────────────────


@router.get("/categories", response_model=list[SectorResponse])
async def list_sectors(
    service: Annotated[ReferenceDataService, Depends(get_reference_data_service)],
) -> list[SectorResponse]:
    sectors = await service.list_sectors()
    return [SectorResponse.model_validate(s) for s in sectors]


@router.post(
    "/categories",
    response_model=SectorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sector(
    request: SectorCreate,
    service: Annotated[ReferenceDataService, Depends(get_reference_data_service)],
) -> SectorResponse:
    try:
        sector = await service.create_sector(
            code=request.code,
            name_en=request.name_en,
            name_am=request.name_am,
            description=request.description,
            is_active=request.is_active,
        )
    except ReferenceDataConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return SectorResponse.model_validate(sector)


@router.put("/categories/{sector_id}", response_model=SectorResponse)
async def update_sector(
    sector_id: int,
    request: SectorUpdate,
    service: Annotated[ReferenceDataService, Depends(get_reference_data_service)],
) -> SectorResponse:
    try:
        fields = request.model_dump(exclude_unset=True)
        sector = await service.update_sector(sector_id, **fields)
    except ReferenceDataNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ReferenceDataConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return SectorResponse.model_validate(sector)


# ── Markets ──────────────────────────────────────────────────────────────────


@router.get("/markets", response_model=list[MarketResponse])
async def list_markets(
    service: Annotated[ReferenceDataService, Depends(get_reference_data_service)],
) -> list[MarketResponse]:
    markets = await service.list_markets()
    return [MarketResponse.model_validate(m) for m in markets]


@router.post(
    "/markets",
    response_model=MarketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_market(
    request: MarketCreate,
    service: Annotated[ReferenceDataService, Depends(get_reference_data_service)],
) -> MarketResponse:
    try:
        market = await service.create_market(
            code=request.code,
            name_en=request.name_en,
            name_am=request.name_am,
            city_en=request.city_en,
            city_am=request.city_am,
            latitude=request.latitude,
            longitude=request.longitude,
            is_active=request.is_active,
        )
    except ReferenceDataConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return MarketResponse.model_validate(market)


@router.put("/markets/{market_id}", response_model=MarketResponse)
async def update_market(
    market_id: int,
    request: MarketUpdate,
    service: Annotated[ReferenceDataService, Depends(get_reference_data_service)],
) -> MarketResponse:
    try:
        fields = request.model_dump(exclude_unset=True)
        market = await service.update_market(market_id, **fields)
    except ReferenceDataNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ReferenceDataConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return MarketResponse.model_validate(market)


# ── Commodities ──────────────────────────────────────────────────────────────


@router.get("/commodities", response_model=list[CommodityResponse])
async def list_commodities(
    service: Annotated[ReferenceDataService, Depends(get_reference_data_service)],
    sector_id: int | None = None,
) -> list[CommodityResponse]:
    commodities = await service.list_commodities(sector_id=sector_id)
    return [CommodityResponse.model_validate(c) for c in commodities]


@router.post(
    "/commodities",
    response_model=CommodityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_commodity(
    request: CommodityCreate,
    service: Annotated[ReferenceDataService, Depends(get_reference_data_service)],
) -> CommodityResponse:
    try:
        commodity = await service.create_commodity(
            sector_id=request.sector_id,
            code=request.code,
            name_en=request.name_en,
            name_am=request.name_am,
            canonical_unit=request.canonical_unit,
            allow_conversion=request.allow_conversion,
            price_hint_low=request.price_hint_low,
            price_hint_high=request.price_hint_high,
            is_active=request.is_active,
        )
    except ReferenceDataNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ReferenceDataConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return CommodityResponse.model_validate(commodity)


@router.put("/commodities/{commodity_id}", response_model=CommodityResponse)
async def update_commodity(
    commodity_id: int,
    request: CommodityUpdate,
    service: Annotated[ReferenceDataService, Depends(get_reference_data_service)],
) -> CommodityResponse:
    try:
        fields = request.model_dump(exclude_unset=True)
        commodity = await service.update_commodity(commodity_id, **fields)
    except ReferenceDataNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ReferenceDataConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return CommodityResponse.model_validate(commodity)


# ── Synonyms ─────────────────────────────────────────────────────────────────


@router.get("/synonyms", response_model=list[SynonymResponse])
async def list_synonyms(
    service: Annotated[ReferenceDataService, Depends(get_reference_data_service)],
    commodity_id: int | None = None,
) -> list[SynonymResponse]:
    synonyms = await service.list_synonyms(commodity_id=commodity_id)
    return [SynonymResponse.model_validate(s) for s in synonyms]


@router.post(
    "/synonyms",
    response_model=SynonymResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_synonym(
    request: SynonymCreate,
    service: Annotated[ReferenceDataService, Depends(get_reference_data_service)],
) -> SynonymResponse:
    try:
        synonym = await service.create_synonym(
            commodity_id=request.commodity_id,
            surface=request.surface,
            normalized=request.normalized,
            script=request.script,
            is_active=request.is_active,
        )
    except ReferenceDataNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ReferenceDataConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return SynonymResponse.model_validate(synonym)


@router.put("/synonyms/{synonym_id}", response_model=SynonymResponse)
async def update_synonym(
    synonym_id: int,
    request: SynonymUpdate,
    service: Annotated[ReferenceDataService, Depends(get_reference_data_service)],
) -> SynonymResponse:
    try:
        fields = request.model_dump(exclude_unset=True)
        synonym = await service.update_synonym(synonym_id, **fields)
    except ReferenceDataNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ReferenceDataConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return SynonymResponse.model_validate(synonym)
