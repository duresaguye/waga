from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class MetaCoverage(BaseModel):
    cells_expected: int
    cells_published: int
    cells_insufficient: int
    cells_coverage_pct: float | None = None
    coverage_pct: float


class MetaWindow(BaseModel):
    start: datetime
    end: datetime
    hours: int


class ResponseMeta(BaseModel):
    generated_at: datetime
    method_version: str
    city: str = "addis_ababa"
    currency: str = "ETB"
    window: MetaWindow
    coverage: MetaCoverage
    licence_class: str = "commercial_permitted"
    snapshot_id: str


class Envelope(BaseModel):
    meta: ResponseMeta
    data: dict[str, Any]


class PriceCell(BaseModel):
    market_code: str
    market_name_en: str
    market_name_am: str
    commodity_code: str
    commodity_name_en: str
    commodity_name_am: str
    unit: str
    currency: str = "ETB"
    status: Literal["published", "insufficient_data"]
    value: Decimal | None
    n_submissions: int
    n_contributors: int
    source_mix: dict[str, int]
    window_start: datetime
    window_end: datetime
    computed_at: datetime
    method_version: str
    insufficient_reason: str | None = None


class CityPriceMinMax(BaseModel):
    market_code: str
    value: Decimal


class CityPrice(BaseModel):
    commodity_code: str
    unit: str
    status: Literal["published", "insufficient_data"]
    value: Decimal | None
    markets_published: int
    markets_expected: int
    min: CityPriceMinMax | None = None
    max: CityPriceMinMax | None = None
    spread_pct: float | None = None


class SeriesPoint(BaseModel):
    date: date
    value: Decimal | None
    status: Literal["published", "insufficient_data"]
    n_submissions: int


class SeriesItem(BaseModel):
    commodity_code: str
    market_code: str | None
    unit: str
    points: list[SeriesPoint]


class AffordabilityItem(BaseModel):
    commodity_code: str
    quantity: Decimal
    unit: str
    unit_price_now: Decimal | None
    unit_price_prior: Decimal | None
    cost_now: Decimal | None
    cost_prior: Decimal | None
    change_pct: float | None
    contribution_to_change_pct: float | None
    status: Literal["published", "insufficient_data"]


class HeatCell(BaseModel):
    commodity_code: str
    status: Literal["published", "insufficient_data"]
    value: Decimal | None
    pct_change: float | None
    band: str | None


class HeatMarket(BaseModel):
    market_code: str
    market_name_en: str
    latitude: float | None
    longitude: float | None
    status: Literal["published", "insufficient_data"]
    heat: float | None
    band: str | None
    cells_published: int
    cells_expected: int
    cells: list[HeatCell]


class CopilotAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    household_count: int = Field(default=50_000, ge=1, le=10_000_000)
    language: Literal["en", "am"] = "en"


class ImpactAskRequest(BaseModel):
    household_count: int = Field(default=50_000, ge=1, le=10_000_000)
    compare_days: int = Field(default=30, ge=1, le=366)
