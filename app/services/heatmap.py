"""Market heat map aggregation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from statistics import mean

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.enums import IndexStatus
from app.repositories.index_values import IndexValueRepository
from app.repositories.reference_data import ReferenceDataRepository
from app.services.prices_read import PricesReadService
from app.services.read_meta import build_meta, decimal_to_float


def heat_band(pct_change: float | None) -> str | None:
    if pct_change is None:
        return None
    if pct_change < -2:
        return "cool"
    if pct_change <= 2:
        return "stable"
    if pct_change <= 5:
        return "warm"
    if pct_change <= 10:
        return "hot"
    return "critical"


class HeatmapService:
    def __init__(
        self,
        session: AsyncSession,
        reference_data: ReferenceDataRepository,
        index_values: IndexValueRepository,
        settings: Settings,
    ) -> None:
        self._session = session
        self._reference_data = reference_data
        self._index_values = index_values
        self._settings = settings
        self._prices = PricesReadService(session, reference_data, index_values, settings)

    async def get_heatmap(
        self,
        *,
        metric: str = "pct_change_7d",
        commodity_code: str | None = None,
    ) -> dict:
        _ = metric
        markets = await self._reference_data.list_markets(active_only=True)
        commodities = await self._reference_data.list_commodities(active_only=True)
        if commodity_code:
            filtered = await self._reference_data.get_commodity_by_code(commodity_code)
            commodities = [filtered] if filtered is not None else []

        latest = await self._prices._load_latest_cells(markets, commodities)
        meta = build_meta(
            self._settings,
            latest_values=latest,
            method_version=self._settings.heat_method_version,
        )

        market_payload = []
        hottest_cell = None
        hottest_value = float("-inf")

        for market in markets:
            cells = []
            pct_changes: list[float] = []
            published_count = 0
            for commodity in commodities:
                current = _find(latest, market.id, commodity.id)
                if current is None:
                    continue
                if current.status == IndexStatus.PUBLISHED:
                    published_count += 1
                pct_change = await self._pct_change_7d(market.id, commodity.id, current)
                band = heat_band(pct_change)
                if pct_change is not None:
                    pct_changes.append(pct_change)
                    if pct_change > hottest_value:
                        hottest_value = pct_change
                        hottest_cell = {
                            "market_code": market.code,
                            "commodity_code": commodity.code,
                            "pct_change": round(pct_change, 1),
                        }
                cells.append(
                    {
                        "commodity_code": commodity.code,
                        "status": current.status.value,
                        "value": decimal_to_float(current.value),
                        "pct_change": round(pct_change, 1) if pct_change is not None else None,
                        "band": band,
                    }
                )

            market_status = (
                IndexStatus.PUBLISHED.value
                if published_count >= 2
                else IndexStatus.INSUFFICIENT_DATA.value
            )
            heat = round(mean(pct_changes), 1) if pct_changes else None
            market_payload.append(
                {
                    "market_code": market.code,
                    "market_name_en": market.name_en,
                    "latitude": decimal_to_float(market.latitude),
                    "longitude": decimal_to_float(market.longitude),
                    "status": market_status,
                    "heat": heat,
                    "band": heat_band(heat),
                    "cells_published": published_count,
                    "cells_expected": len(commodities),
                    "cells": cells,
                }
            )

        return {
            "meta": meta,
            "data": {
                "metric": "pct_change_7d",
                "method_version": self._settings.heat_method_version,
                "markets": market_payload,
                "hottest_cell": hottest_cell,
            },
        }

    async def _pct_change_7d(
        self,
        market_id: int,
        commodity_id: int,
        current,
    ) -> float | None:
        if current.status != IndexStatus.PUBLISHED or current.value is None:
            return None
        now = datetime.now(UTC)
        prior_start = now - timedelta(days=14)
        rows = await self._index_values.list_for_cell_in_range(
            market_id=market_id,
            commodity_id=commodity_id,
            start=prior_start,
            end=now - timedelta(days=7),
        )
        published = [
            Decimal(str(row.value))
            for row in rows
            if row.status == IndexStatus.PUBLISHED and row.value is not None
        ]
        if not published:
            return None
        prior = float(mean(published))
        current_value = float(current.value)
        if prior == 0:
            return None
        return ((current_value - prior) / prior) * 100


def _find(latest, market_id: int, commodity_id: int):
    for row in latest:
        if row.market_id == market_id and row.commodity_id == commodity_id:
            return row
    return None
