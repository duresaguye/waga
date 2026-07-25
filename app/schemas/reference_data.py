from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Script

# -- Sector -------------------------------------------------------------------


class SectorCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name_en: str = Field(min_length=1, max_length=160)
    name_am: str = Field(min_length=1, max_length=160)
    description: str | None = None
    is_active: bool = True


class SectorUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name_en: str | None = Field(default=None, min_length=1, max_length=160)
    name_am: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    is_active: bool | None = None


class SectorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name_en: str
    name_am: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# -- Market -------------------------------------------------------------------


class MarketCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name_en: str = Field(min_length=1, max_length=160)
    name_am: str = Field(min_length=1, max_length=160)
    city_en: str = Field(min_length=1, max_length=160)
    city_am: str = Field(min_length=1, max_length=160)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    is_active: bool = True


class MarketUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name_en: str | None = Field(default=None, min_length=1, max_length=160)
    name_am: str | None = Field(default=None, min_length=1, max_length=160)
    city_en: str | None = Field(default=None, min_length=1, max_length=160)
    city_am: str | None = Field(default=None, min_length=1, max_length=160)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    is_active: bool | None = None


class MarketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name_en: str
    name_am: str
    city_en: str
    city_am: str
    latitude: Decimal | None
    longitude: Decimal | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# -- Commodity ----------------------------------------------------------------


class CommodityCreate(BaseModel):
    sector_id: int
    code: str = Field(min_length=1, max_length=64)
    name_en: str = Field(min_length=1, max_length=160)
    name_am: str = Field(min_length=1, max_length=160)
    canonical_unit: str = Field(min_length=1, max_length=32)
    allow_conversion: bool = True
    price_hint_low: Decimal | None = None
    price_hint_high: Decimal | None = None
    is_active: bool = True


class CommodityUpdate(BaseModel):
    sector_id: int | None = None
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name_en: str | None = Field(default=None, min_length=1, max_length=160)
    name_am: str | None = Field(default=None, min_length=1, max_length=160)
    canonical_unit: str | None = Field(default=None, min_length=1, max_length=32)
    allow_conversion: bool | None = None
    price_hint_low: Decimal | None = None
    price_hint_high: Decimal | None = None
    is_active: bool | None = None


class CommodityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sector_id: int
    code: str
    name_en: str
    name_am: str
    canonical_unit: str
    allow_conversion: bool
    price_hint_low: Decimal | None
    price_hint_high: Decimal | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# -- CommoditySynonym ---------------------------------------------------------


class SynonymCreate(BaseModel):
    commodity_id: int
    surface: str = Field(min_length=1, max_length=160)
    normalized: str = Field(min_length=1, max_length=160)
    script: Script
    is_active: bool = True


class SynonymUpdate(BaseModel):
    commodity_id: int | None = None
    surface: str | None = Field(default=None, min_length=1, max_length=160)
    normalized: str | None = Field(default=None, min_length=1, max_length=160)
    script: Script | None = None
    is_active: bool | None = None


class SynonymResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commodity_id: int
    surface: str
    normalized: str
    script: Script
    is_active: bool
