"""Read APIs for reference data, current prices, series, and coverage."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from statistics import median

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.enums import IndexStatus
from app.models.index_values import IndexValue
from app.models.reference_data import Commodity, Market
from app.repositories.index_values import IndexValueRepository
from app.repositories.reference_data import ReferenceDataRepository
from app.services.api_errors import contract_error
from app.services.basket_config import PHASE1_BASKET
from app.services.read_meta import (
    build_meta,
    commodity_to_dict,
    index_value_to_cell,
    iso_z,
    market_to_dict,
)


class PricesReadService:
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

    async def get_reference(self) -> dict:
        markets = await self._reference_data.list_markets(active_only=True)
        commodities = await self._reference_data.list_commodities(active_only=True)
        sectors = await self._reference_data.list_sectors(active_only=True)
        sector_by_id = {sector.id: sector for sector in sectors}
        latest = await self._load_latest_cells(markets, commodities)
        meta = self._build_meta(markets, commodities, latest)
        city = markets[0] if markets else None
        return {
            "meta": meta,
            "data": {
                "city": {
                    "code": self._settings.city_code,
                    "name_en": city.city_en if city else "Addis Ababa",
                    "name_am": city.city_am if city else "Addis Ababa",
                },
                "markets": [market_to_dict(market) for market in markets],
                "commodities": [
                    commodity_to_dict(
                        commodity,
                        sector=sector_by_id.get(commodity.sector_id),
                    )
                    for commodity in commodities
                ],
                "baskets": [PHASE1_BASKET],
            },
        }

    async def get_current_prices(
        self,
        *,
        market_codes: list[str] | None = None,
        commodity_codes: list[str] | None = None,
        include_insufficient: bool = True,
    ) -> dict:
        markets, commodities, market_by_id, commodity_by_id = await self._resolve_catalog(
            market_codes=market_codes,
            commodity_codes=commodity_codes,
        )
        latest = await self._load_latest_cells(
            markets,
            commodities,
            market_by_id=market_by_id,
            commodity_by_id=commodity_by_id,
        )
        cells = []
        for index_value in latest:
            if not include_insufficient and index_value.status != IndexStatus.PUBLISHED:
                continue
            market = market_by_id[index_value.market_id]
            commodity = commodity_by_id[index_value.commodity_id]
            cells.append(
                index_value_to_cell(
                    index_value,
                    market=market,
                    commodity=commodity,
                    settings=self._settings,
                )
            )
        meta = self._build_meta(markets, commodities, latest)
        return {
            "meta": meta,
            "data": {
                "cells": cells,
                "city_prices": _build_city_prices(
                    latest,
                    markets=markets,
                    commodities=commodities,
                    market_by_id=market_by_id,
                    commodity_by_id=commodity_by_id,
                ),
            },
        }

    async def get_series(
        self,
        *,
        commodity_codes: list[str],
        market_codes: list[str] | None,
        start: date,
        end: date,
        history_depth_days: int | None,
    ) -> dict:
        if end < start:
            raise contract_error(
                "invalid_range",
                "End date must be on or after start date",
                field="to",
            )
        if (end - start).days > 366:
            raise contract_error(
                "range_too_large",
                "Date range must not exceed 366 days",
                field="to",
            )

        effective_start = start
        if history_depth_days is not None:
            earliest = date.today() - timedelta(days=history_depth_days)
            effective_start = max(start, earliest)

        commodities = []
        for code in commodity_codes:
            row = await self._reference_data.get_commodity_by_code(code)
            if row is None:
                raise contract_error(
                    "unknown_commodity",
                    f"No commodity with code '{code}'",
                    field="commodity",
                )
            commodities.append(row)

        markets: list[Market] = []
        if market_codes:
            for code in market_codes:
                row = await self._reference_data.get_market_by_code(code)
                if row is None:
                    raise contract_error(
                        "unknown_market",
                        f"No market with code '{code}'",
                        field="market",
                    )
                markets.append(row)

        series = []
        start_dt = datetime.combine(effective_start, datetime.min.time(), tzinfo=UTC)
        end_dt = datetime.combine(end, datetime.max.time(), tzinfo=UTC)

        if markets:
            for market in markets:
                for commodity in commodities:
                    series.append(
                        await self._series_for_cell(
                            market=market,
                            commodity=commodity,
                            start_dt=start_dt,
                            end_dt=end_dt,
                        )
                    )
        else:
            for commodity in commodities:
                series.append(
                    await self._city_series_for_commodity(
                        commodity=commodity,
                        start_dt=start_dt,
                        end_dt=end_dt,
                    )
                )

        latest = await self._load_latest_cells(
            await self._reference_data.list_markets(active_only=True),
            commodities,
        )
        all_markets = await self._reference_data.list_markets(active_only=True)
        return {
            "meta": self._build_meta(all_markets, commodities, latest),
            "data": {"interval": "day", "series": series},
        }

    async def get_coverage(self) -> dict:
        markets = await self._reference_data.list_markets(active_only=True)
        commodities = await self._reference_data.list_commodities(active_only=True)
        market_by_id = {market.id: market for market in markets}
        commodity_by_id = {commodity.id: commodity for commodity in commodities}
        latest = await self._load_latest_cells(markets, commodities)
        now = datetime.now(UTC)

        matrix = []
        worst_covered: list[dict] = []
        for market in markets:
            market_cells = []
            for commodity in commodities:
                index_value = _find_latest(latest, market.id, commodity.id)
                if index_value is None:
                    continue
                hours_since_last = (now - index_value.computed_at).total_seconds() / 3600
                cell = {
                    "commodity_code": commodity.code,
                    "status": index_value.status.value,
                    "n_submissions": index_value.n_submissions,
                    "hours_since_last": round(hours_since_last, 1),
                }
                market_cells.append(cell)
                worst_covered.append(
                    {
                        "market_code": market.code,
                        "commodity_code": commodity.code,
                        "hours_since_last": round(hours_since_last, 1),
                    }
                )
            matrix.append({"market_code": market.code, "cells": market_cells})

        worst_covered.sort(key=lambda item: item["hours_since_last"], reverse=True)
        meta = self._build_meta(markets, commodities, latest)
        return {
            "meta": meta,
            "data": {
                "matrix": matrix,
                "worst_covered": worst_covered[:10],
            },
        }

    async def get_city_median_on_date(
        self,
        commodity: Commodity,
        target: date,
    ) -> float | None:
        start_dt = datetime.combine(target, datetime.min.time(), tzinfo=UTC)
        end_dt = datetime.combine(target, datetime.max.time(), tzinfo=UTC)
        rows = await self._index_values.list_for_cell_in_range(
            market_id=None,
            commodity_id=commodity.id,
            start=start_dt,
            end=end_dt,
        )
        by_market: dict[int, IndexValue] = {}
        for row in rows:
            if row.status != IndexStatus.PUBLISHED or row.value is None:
                continue
            existing = by_market.get(row.market_id)
            if existing is None or row.computed_at > existing.computed_at:
                by_market[row.market_id] = row
        if not by_market:
            return None
        return float(median([Decimal(str(row.value)) for row in by_market.values()]))

    async def _resolve_catalog(
        self,
        *,
        market_codes: list[str] | None,
        commodity_codes: list[str] | None,
    ) -> tuple[list[Market], list[Commodity], dict[int, Market], dict[int, Commodity]]:
        if market_codes:
            markets = []
            for code in market_codes:
                row = await self._reference_data.get_market_by_code(code)
                if row is None:
                    raise contract_error(
                        "unknown_market",
                        f"No market with code '{code}'",
                        field="market",
                    )
                markets.append(row)
        else:
            markets = await self._reference_data.list_markets(active_only=True)

        if commodity_codes:
            commodities = []
            for code in commodity_codes:
                row = await self._reference_data.get_commodity_by_code(code)
                if row is None:
                    raise contract_error(
                        "unknown_commodity",
                        f"No commodity with code '{code}'",
                        field="commodity",
                    )
                commodities.append(row)
        else:
            commodities = await self._reference_data.list_commodities(active_only=True)

        market_by_id = {market.id: market for market in markets}
        commodity_by_id = {commodity.id: commodity for commodity in commodities}
        return markets, commodities, market_by_id, commodity_by_id

    async def _load_latest_cells(
        self,
        markets: list[Market],
        commodities: list[Commodity],
        *,
        market_by_id: dict[int, Market] | None = None,
        commodity_by_id: dict[int, Commodity] | None = None,
    ) -> list[IndexValue]:
        _ = (market_by_id, commodity_by_id)
        market_ids = [market.id for market in markets] if markets else None
        commodity_ids = [commodity.id for commodity in commodities] if commodities else None
        if not markets or not commodities:
            return []

        latest_from_db = await self._index_values.list_latest_per_cell(
            market_ids=market_ids,
            commodity_ids=commodity_ids,
        )
        by_key = {
            (row.market_id, row.commodity_id): row for row in latest_from_db
        }

        result: list[IndexValue] = []
        for market in markets:
            for commodity in commodities:
                key = (market.id, commodity.id)
                if key in by_key:
                    result.append(by_key[key])
                    continue
                now = datetime.now(UTC)
                result.append(
                    IndexValue(
                        market_id=market.id,
                        commodity_id=commodity.id,
                        trigger_verification_id=_zero_uuid(),
                        method_version=self._settings.method_version,
                        window_start=now - timedelta(hours=self._settings.index_window_hours),
                        window_end=now,
                        value=None,
                        unit=commodity.canonical_unit,
                        n_submissions=0,
                        n_contributors=0,
                        source_mix={},
                        status=IndexStatus.INSUFFICIENT_DATA,
                    )
                )
        return result

    def _build_meta(
        self,
        markets: list[Market],
        commodities: list[Commodity],
        latest: list[IndexValue],
    ) -> dict:
        return build_meta(
            self._settings,
            latest_values=latest,
            matrix_size=len(markets) * len(commodities),
        )

    async def _series_for_cell(
        self,
        *,
        market: Market,
        commodity: Commodity,
        start_dt: datetime,
        end_dt: datetime,
    ) -> dict:
        rows = await self._index_values.list_for_cell_in_range(
            market_id=market.id,
            commodity_id=commodity.id,
            start=start_dt,
            end=end_dt,
        )
        points = _daily_points(rows, start_dt.date(), end_dt.date())
        return {
            "commodity_code": commodity.code,
            "market_code": market.code,
            "unit": commodity.canonical_unit,
            "points": points,
        }

    async def _city_series_for_commodity(
        self,
        *,
        commodity: Commodity,
        start_dt: datetime,
        end_dt: datetime,
    ) -> dict:
        rows = await self._index_values.list_for_cell_in_range(
            market_id=None,
            commodity_id=commodity.id,
            start=start_dt,
            end=end_dt,
        )
        by_day: dict[date, list[IndexValue]] = defaultdict(list)
        for row in rows:
            by_day[row.computed_at.date()].append(row)

        points = []
        current = start_dt.date()
        while current <= end_dt.date():
            day_rows = by_day.get(current, [])
            published_values = [
                Decimal(str(row.value))
                for row in day_rows
                if row.status == IndexStatus.PUBLISHED and row.value is not None
            ]
            if published_values:
                points.append(
                    {
                        "date": current.isoformat(),
                        "value": float(median(published_values)),
                        "status": IndexStatus.PUBLISHED.value,
                        "n_submissions": sum(row.n_submissions for row in day_rows),
                    }
                )
            elif day_rows:
                points.append(
                    {
                        "date": current.isoformat(),
                        "value": None,
                        "status": IndexStatus.INSUFFICIENT_DATA.value,
                        "n_submissions": max(row.n_submissions for row in day_rows),
                    }
                )
            current += timedelta(days=1)

        return {
            "commodity_code": commodity.code,
            "market_code": None,
            "unit": commodity.canonical_unit,
            "points": points,
        }


def _build_city_prices(
    latest: list[IndexValue],
    *,
    markets: list[Market],
    commodities: list[Commodity],
    market_by_id: dict[int, Market],
    commodity_by_id: dict[int, Commodity],
) -> list[dict]:
    city_prices = []
    for commodity in commodities:
        published_cells = [
            row
            for row in latest
            if row.commodity_id == commodity.id and row.status == IndexStatus.PUBLISHED
        ]
        values = [Decimal(str(row.value)) for row in published_cells if row.value is not None]
        if not values:
            city_prices.append(
                {
                    "commodity_code": commodity.code,
                    "unit": commodity.canonical_unit,
                    "status": IndexStatus.INSUFFICIENT_DATA.value,
                    "value": None,
                    "markets_published": 0,
                    "markets_expected": len(markets),
                    "min": None,
                    "max": None,
                    "spread_pct": None,
                }
            )
            continue

        min_row = min(published_cells, key=lambda row: Decimal(str(row.value)))
        max_row = max(published_cells, key=lambda row: Decimal(str(row.value)))
        city_median = float(median(values))
        min_value = float(min_row.value) if min_row.value is not None else None
        max_value = float(max_row.value) if max_row.value is not None else None
        spread_pct = None
        if min_value and max_value and city_median:
            spread_pct = round(((max_value - min_value) / city_median) * 100, 1)

        city_prices.append(
            {
                "commodity_code": commodity.code,
                "unit": commodity.canonical_unit,
                "status": IndexStatus.PUBLISHED.value,
                "value": city_median,
                "markets_published": len(published_cells),
                "markets_expected": len(markets),
                "min": {
                    "market_code": market_by_id[min_row.market_id].code,
                    "value": min_value,
                },
                "max": {
                    "market_code": market_by_id[max_row.market_id].code,
                    "value": max_value,
                },
                "spread_pct": spread_pct,
            }
        )
    return city_prices


def _find_latest(
    latest: list[IndexValue],
    market_id: int,
    commodity_id: int,
) -> IndexValue | None:
    for row in latest:
        if row.market_id == market_id and row.commodity_id == commodity_id:
            return row
    return None


def _daily_points(
    rows: list[IndexValue],
    start: date,
    end: date,
) -> list[dict]:
    by_day: dict[date, IndexValue] = {}
    for row in rows:
        day = row.computed_at.date()
        existing = by_day.get(day)
        if existing is None or row.computed_at > existing.computed_at:
            by_day[day] = row

    points = []
    current = start
    while current <= end:
        row = by_day.get(current)
        if row is None:
            current += timedelta(days=1)
            continue
        points.append(
            {
                "date": current.isoformat(),
                "value": float(row.value) if row.value is not None else None,
                "status": row.status.value,
                "n_submissions": row.n_submissions,
            }
        )
        current += timedelta(days=1)
    return points


def _zero_uuid():
    from uuid import UUID

    return UUID(int=0)
