"""Track B read APIs: prices, affordability, heatmap, copilot."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from statistics import median
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IndexStatus
from app.models.index_values import IndexValue
from app.repositories.index_values import IndexValueRepository
from app.repositories.reference_data import ReferenceDataRepository
from app.schemas.intelligence import Envelope, MetaCoverage, MetaWindow, ResponseMeta
from app.services.index_rules import (
    BASKET_PHASE1,
    CITY_CODE,
    CURRENCY,
    METHOD_VERSION_AFFORDABILITY,
    METHOD_VERSION_COPILOT,
    METHOD_VERSION_HEAT,
    METHOD_VERSION_INDEX,
    PHASE1_COMMODITY_CODES,
    PHASE1_MARKET_CODES,
    WINDOW_HOURS,
    affordability_band,
    heat_band,
)


class IntelligenceService:
    def __init__(
        self,
        session: AsyncSession,
        index_values: IndexValueRepository,
        reference: ReferenceDataRepository,
    ) -> None:
        self._session = session
        self._index = index_values
        self._reference = reference

    async def current_prices(
        self,
        *,
        market_codes: list[str] | None = None,
        commodity_codes: list[str] | None = None,
        include_insufficient: bool = True,
    ) -> Envelope:
        markets, commodities = await self._phase1_refs()
        if market_codes:
            wanted = {c.lower() for c in market_codes}
            markets = [m for m in markets if m.code in wanted]
        if commodity_codes:
            wanted = {c.lower() for c in commodity_codes}
            commodities = [c for c in commodities if c.code in wanted]

        market_ids = [m.id for m in markets]
        commodity_ids = [c.id for c in commodities]
        latest = await self._index.list_latest_cells(
            market_ids=market_ids or None,
            commodity_ids=commodity_ids or None,
        )
        by_cell = {(row.market_id, row.commodity_id): row for row in latest}

        cells: list[dict[str, Any]] = []
        published = 0
        insufficient = 0
        for market in markets:
            for commodity in commodities:
                row = by_cell.get((market.id, commodity.id))
                cell = self._cell_dict(market, commodity, row)
                if cell["status"] == "published":
                    published += 1
                else:
                    insufficient += 1
                if include_insufficient or cell["status"] == "published":
                    cells.append(cell)

        city_prices = self._city_prices(markets, commodities, by_cell)
        expected = len(markets) * len(commodities)
        meta = self._meta(
            METHOD_VERSION_INDEX,
            cells_expected=expected,
            cells_published=published,
            cells_insufficient=insufficient,
        )
        return Envelope(meta=meta, data={"cells": cells, "city_prices": city_prices})

    async def price_series(
        self,
        *,
        commodity_codes: list[str] | None = None,
        market_codes: list[str] | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        interval: str = "day",
    ) -> Envelope:
        _ = interval  # v1: daily buckets only
        markets, commodities = await self._phase1_refs()
        if commodity_codes:
            wanted = {c.lower() for c in commodity_codes}
            commodities = [c for c in commodities if c.code in wanted]
        else:
            commodities = [c for c in commodities if c.code == "teff_mixed"] or commodities[:1]

        end = datetime.combine(to_date or datetime.now(UTC).date(), datetime.min.time(), tzinfo=UTC)
        end = end.replace(hour=23, minute=59, second=59)
        start_day = from_date or (end.date() - timedelta(days=30))
        start = datetime.combine(start_day, datetime.min.time(), tzinfo=UTC)

        series: list[dict[str, Any]] = []
        if market_codes:
            market_map = {m.code: m for m in markets}
            selected_markets = [market_map[c] for c in market_codes if c in market_map]
        else:
            selected_markets = [None]  # type: ignore[list-item]

        for commodity in commodities:
            for market in selected_markets:
                market_id = None if market is None else market.id
                rows = await self._index.list_in_range(
                    commodity_id=commodity.id,
                    market_id=market_id,
                    start=start,
                    end=end,
                )
                by_day: dict[date, list[IndexValue]] = {}
                for row in rows:
                    day = row.computed_at.astimezone(UTC).date()
                    by_day.setdefault(day, []).append(row)

                points: list[dict[str, Any]] = []
                cursor = start_day
                last = end.date()
                while cursor <= last:
                    day_rows = by_day.get(cursor, [])
                    published_rows = [
                        r for r in day_rows if r.status == IndexStatus.PUBLISHED and r.value is not None
                    ]
                    if published_rows:
                        if market is None:
                            # City aggregate: median of latest value per market that day
                            per_market: dict[int, Decimal] = {}
                            for r in sorted(published_rows, key=lambda x: x.computed_at):
                                per_market[r.market_id] = Decimal(str(r.value))
                            value = Decimal(str(median(per_market.values())))
                            n = sum(r.n_submissions for r in published_rows)
                        else:
                            latest = max(published_rows, key=lambda r: r.computed_at)
                            value = Decimal(str(latest.value))
                            n = latest.n_submissions
                        points.append(
                            {
                                "date": cursor,
                                "value": value,
                                "status": "published",
                                "n_submissions": n,
                            }
                        )
                    else:
                        n = sum(r.n_submissions for r in day_rows)
                        points.append(
                            {
                                "date": cursor,
                                "value": None,
                                "status": "insufficient_data",
                                "n_submissions": n,
                            }
                        )
                    cursor += timedelta(days=1)

                series.append(
                    {
                        "commodity_code": commodity.code,
                        "market_code": None if market is None else market.code,
                        "unit": commodity.canonical_unit,
                        "points": points,
                    }
                )

        meta = self._meta(METHOD_VERSION_INDEX, cells_expected=0, cells_published=0, cells_insufficient=0)
        return Envelope(meta=meta, data={"interval": "day", "series": series})

    async def affordability(
        self,
        *,
        basket: str = "phase1_staple5",
        household_size: int = 5,
        compare_days: int = 30,
    ) -> Envelope:
        _ = basket
        markets, commodities = await self._phase1_refs()
        commodity_by_code = {c.code: c for c in commodities}
        latest = await self._index.list_latest_cells(
            market_ids=[m.id for m in markets],
            commodity_ids=[c.id for c in commodities],
        )
        by_cell = {(r.market_id, r.commodity_id): r for r in latest}
        city_now = {
            item["commodity_code"]: item
            for item in self._city_prices(markets, commodities, by_cell)
        }

        prior_as_of = datetime.now(UTC) - timedelta(days=compare_days)
        city_prior: dict[str, Decimal | None] = {}
        for code, _qty, _unit in BASKET_PHASE1:
            commodity = commodity_by_code.get(code)
            if commodity is None:
                city_prior[code] = None
                continue
            values: list[Decimal] = []
            for market in markets:
                row = await self._index.get_latest_for_cell(
                    market_id=market.id,
                    commodity_id=commodity.id,
                    as_of=prior_as_of,
                    published_only=True,
                )
                if row is not None and row.value is not None:
                    values.append(Decimal(str(row.value)))
            city_prior[code] = (
                Decimal(str(median(values))) if values else None
            )

        scale = Decimal(str(household_size)) / Decimal("5")
        items: list[dict[str, Any]] = []
        missing: list[str] = []
        cost_now_total = Decimal("0")
        cost_prior_total = Decimal("0")
        deltas: list[Decimal] = []

        for code, base_qty, unit in BASKET_PHASE1:
            qty = (base_qty * scale).quantize(Decimal("0.01"))
            now_info = city_now.get(code)
            unit_now = None if now_info is None else now_info.get("value")
            unit_prior = city_prior.get(code)
            status = "published"
            if unit_now is None:
                status = "insufficient_data"
                missing.append(code)
            cost_now = None if unit_now is None else (Decimal(str(unit_now)) * qty)
            cost_prior = None if unit_prior is None else (Decimal(str(unit_prior)) * qty)
            change_pct = None
            if cost_now is not None and cost_prior is not None and cost_prior > 0:
                change_pct = float((cost_now - cost_prior) / cost_prior * 100)
                deltas.append(cost_now - cost_prior)
                cost_now_total += cost_now
                cost_prior_total += cost_prior
            elif cost_now is not None:
                cost_now_total += cost_now

            items.append(
                {
                    "commodity_code": code,
                    "quantity": qty,
                    "unit": unit,
                    "unit_price_now": unit_now,
                    "unit_price_prior": unit_prior,
                    "cost_now": cost_now,
                    "cost_prior": cost_prior,
                    "change_pct": None if change_pct is None else round(change_pct, 1),
                    "contribution_to_change_pct": None,
                    "status": status,
                }
            )

        if missing:
            data = {
                "basket_code": "phase1_staple5",
                "household_size": household_size,
                "period_days": compare_days,
                "status": "insufficient_data",
                "cost_now": None,
                "cost_prior": None,
                "prior_date": prior_as_of.date().isoformat(),
                "change_abs": None,
                "change_pct": None,
                "score": None,
                "band": "Unknown",
                "method_version": METHOD_VERSION_AFFORDABILITY,
                "items": items,
                "missing_commodities": missing,
            }
        else:
            change_abs = cost_now_total - cost_prior_total
            change_pct = (
                float(change_abs / cost_prior_total * 100) if cost_prior_total > 0 else 0.0
            )
            total_delta = sum(deltas) if deltas else Decimal("0")
            for item in items:
                if item["cost_now"] is not None and item["cost_prior"] is not None and total_delta != 0:
                    part = (item["cost_now"] - item["cost_prior"]) / total_delta * 100
                    item["contribution_to_change_pct"] = round(float(part), 1)
            score, band = affordability_band(change_pct)
            data = {
                "basket_code": "phase1_staple5",
                "household_size": household_size,
                "period_days": compare_days,
                "status": "published",
                "cost_now": float(cost_now_total.quantize(Decimal("0.01"))),
                "cost_prior": float(cost_prior_total.quantize(Decimal("0.01"))),
                "prior_date": prior_as_of.date().isoformat(),
                "change_abs": float(change_abs.quantize(Decimal("0.01"))),
                "change_pct": round(change_pct, 1),
                "score": score,
                "band": band,
                "method_version": METHOD_VERSION_AFFORDABILITY,
                "items": items,
                "missing_commodities": [],
            }

        published = sum(1 for c in city_now.values() if c.get("status") == "published")
        expected = len(PHASE1_COMMODITY_CODES)
        meta = self._meta(
            METHOD_VERSION_AFFORDABILITY,
            cells_expected=expected,
            cells_published=published,
            cells_insufficient=max(0, expected - published),
        )
        return Envelope(meta=meta, data=data)

    async def heatmap(
        self,
        *,
        metric: str = "pct_change_7d",
        commodity_codes: list[str] | None = None,
    ) -> Envelope:
        days = 7 if metric == "pct_change_7d" else 30
        markets, commodities = await self._phase1_refs()
        if commodity_codes:
            wanted = {c.lower() for c in commodity_codes}
            commodities = [c for c in commodities if c.code in wanted]

        latest = await self._index.list_latest_cells(
            market_ids=[m.id for m in markets],
            commodity_ids=[c.id for c in commodities],
        )
        by_cell = {(r.market_id, r.commodity_id): r for r in latest}
        prior_as_of = datetime.now(UTC) - timedelta(days=days)

        market_rows: list[dict[str, Any]] = []
        hottest: dict[str, Any] | None = None
        hottest_pct = -999.0
        published_cells = 0
        expected_cells = 0

        for market in markets:
            cells: list[dict[str, Any]] = []
            pcts: list[float] = []
            cell_pub = 0
            for commodity in commodities:
                expected_cells += 1
                now = by_cell.get((market.id, commodity.id))
                prior = await self._index.get_latest_for_cell(
                    market_id=market.id,
                    commodity_id=commodity.id,
                    as_of=prior_as_of,
                    published_only=True,
                )
                if (
                    now is not None
                    and now.status == IndexStatus.PUBLISHED
                    and now.value is not None
                ):
                    cell_pub += 1
                    published_cells += 1
                    value = Decimal(str(now.value))
                    pct = None
                    if prior is not None and prior.value is not None and prior.value > 0:
                        pct = float((value - Decimal(str(prior.value))) / Decimal(str(prior.value)) * 100)
                        pcts.append(pct)
                        if pct > hottest_pct:
                            hottest_pct = pct
                            hottest = {
                                "market_code": market.code,
                                "commodity_code": commodity.code,
                                "pct_change": round(pct, 1),
                            }
                    cells.append(
                        {
                            "commodity_code": commodity.code,
                            "status": "published",
                            "value": value,
                            "pct_change": None if pct is None else round(pct, 1),
                            "band": heat_band(pct),
                        }
                    )
                else:
                    cells.append(
                        {
                            "commodity_code": commodity.code,
                            "status": "insufficient_data",
                            "value": None,
                            "pct_change": None,
                            "band": None,
                        }
                    )

            heat = round(sum(pcts) / len(pcts), 1) if pcts else None
            market_rows.append(
                {
                    "market_code": market.code,
                    "market_name_en": market.name_en,
                    "latitude": None if market.latitude is None else float(market.latitude),
                    "longitude": None if market.longitude is None else float(market.longitude),
                    "status": "published" if cell_pub else "insufficient_data",
                    "heat": heat,
                    "band": heat_band(heat),
                    "cells_published": cell_pub,
                    "cells_expected": len(commodities),
                    "cells": cells,
                }
            )

        meta = self._meta(
            METHOD_VERSION_HEAT,
            cells_expected=expected_cells,
            cells_published=published_cells,
            cells_insufficient=max(0, expected_cells - published_cells),
        )
        return Envelope(
            meta=meta,
            data={
                "metric": metric,
                "method_version": METHOD_VERSION_HEAT,
                "markets": market_rows,
                "hottest_cell": hottest,
            },
        )

    async def copilot_ask(
        self,
        *,
        question: str,
        household_count: int = 50_000,
        language: str = "en",
    ) -> Envelope:
        _ = question
        afford = await self.affordability(compare_days=30)
        data = afford.data
        prices = await self.current_prices()
        city = {
            item["commodity_code"]: item
            for item in prices.data.get("city_prices", [])
        }
        teff = city.get("teff_mixed", {})

        if data.get("status") != "published":
            answer = (
                "Not enough published staple prices yet to recommend a cash adjustment. "
                "Accept more market reports, then ask again."
            )
            _ = language
            payload = {
                "answer": answer,
                "recommendation": {
                    "action": "wait_for_more_data",
                    "band_low_pct": None,
                    "band_high_pct": None,
                    "confidence": "low",
                    "confidence_reason": "Affordability basket is insufficient_data",
                },
                "citations": [
                    {
                        "label": "Affordability status",
                        "value": None,
                        "unit": None,
                        "source": "/affordability",
                        "cell_refs": [f"{CITY_CODE}:phase1_staple5:insufficient"],
                    }
                ],
                "impact": None,
                "mode": "rule_based",
            }
        else:
            change = float(data["change_pct"])
            low = max(0.0, round(change - 3, 1))
            high = round(change, 1)
            if change < 2:
                action = "hold_transfer_value"
                answer = (
                    f"The Addis staple basket is roughly stable "
                    f"({data['cost_prior']} → {data['cost_now']} ETB, {change:+.1f}%). "
                    "No large transfer adjustment is indicated from Waga prices alone."
                )
            else:
                action = "increase_transfer_value"
                top = max(
                    (i for i in data["items"] if i.get("contribution_to_change_pct") is not None),
                    key=lambda i: i["contribution_to_change_pct"],
                    default=None,
                )
                top_bit = ""
                if top:
                    top_bit = (
                        f" {top['commodity_code']} accounts for "
                        f"{top['contribution_to_change_pct']}% of that increase."
                    )
                answer = (
                    f"The Addis staple basket rose from {data['cost_prior']} to {data['cost_now']} ETB "
                    f"over the last {data['period_days']} days, an increase of {change}%.{top_bit} "
                    f"An adjustment of {low}–{high}% would restore purchasing power."
                )
            gap = float(data["change_abs"])
            payload = {
                "answer": answer,
                "recommendation": {
                    "action": action,
                    "band_low_pct": low if action == "increase_transfer_value" else 0.0,
                    "band_high_pct": high if action == "increase_transfer_value" else 0.0,
                    "confidence": "medium",
                    "confidence_reason": (
                        f"{afford.meta.coverage.cells_published} of "
                        f"{afford.meta.coverage.cells_expected} city commodity lines published"
                    ),
                },
                "citations": [
                    {
                        "label": "Basket cost now",
                        "value": data["cost_now"],
                        "unit": "ETB",
                        "source": "/affordability",
                        "cell_refs": [
                            f"{CITY_CODE}:phase1_staple5:{datetime.now(UTC).date().isoformat()}"
                        ],
                    },
                    {
                        "label": "Basket cost prior",
                        "value": data["cost_prior"],
                        "unit": "ETB",
                        "source": "/affordability",
                        "cell_refs": [f"{CITY_CODE}:phase1_staple5:{data['prior_date']}"],
                    },
                    {
                        "label": "Teff city median",
                        "value": None if teff.get("value") is None else float(teff["value"]),
                        "unit": "ETB/kg",
                        "source": "/prices/current",
                        "cell_refs": [
                            f"{CITY_CODE}:teff_mixed:{datetime.now(UTC).date().isoformat()}"
                        ],
                    },
                ],
                "impact": {
                    "household_count": household_count,
                    "gap_per_household_etb": gap,
                    "monthly_total_etb": round(gap * household_count, 2),
                    "note": "Cost of leaving the transfer value unchanged for one month.",
                },
                "mode": "rule_based",
            }

        meta = self._meta(
            METHOD_VERSION_COPILOT,
            cells_expected=afford.meta.coverage.cells_expected,
            cells_published=afford.meta.coverage.cells_published,
            cells_insufficient=afford.meta.coverage.cells_insufficient,
        )
        return Envelope(meta=meta, data=payload)

    async def impact(
        self, *, household_count: int = 50_000, compare_days: int = 30
    ) -> Envelope:
        afford = await self.affordability(compare_days=compare_days)
        data = afford.data
        if data.get("status") != "published":
            payload = {
                "household_count": household_count,
                "gap_per_household_etb": None,
                "monthly_total_etb": None,
                "status": "insufficient_data",
                "note": "Basket not fully published yet.",
            }
        else:
            gap = float(data["change_abs"])
            payload = {
                "household_count": household_count,
                "gap_per_household_etb": gap,
                "monthly_total_etb": round(gap * household_count, 2),
                "status": "published",
                "note": "Cost of leaving the transfer value unchanged for one month.",
                "change_pct": data["change_pct"],
                "cost_now": data["cost_now"],
                "cost_prior": data["cost_prior"],
            }
        return Envelope(meta=afford.meta, data=payload)

    async def _phase1_refs(self) -> tuple[list[Any], list[Any]]:
        markets = [
            m
            for m in await self._reference.list_markets(active_only=True)
            if m.code in PHASE1_MARKET_CODES
        ]
        commodities = [
            c
            for c in await self._reference.list_commodities(active_only=True)
            if c.code in PHASE1_COMMODITY_CODES
        ]
        # Preserve frozen order
        markets.sort(key=lambda m: PHASE1_MARKET_CODES.index(m.code))
        commodities.sort(key=lambda c: PHASE1_COMMODITY_CODES.index(c.code))
        return markets, commodities

    def _city_prices(
        self,
        markets: list[Any],
        commodities: list[Any],
        by_cell: dict[tuple[int, int], IndexValue],
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for commodity in commodities:
            published: list[tuple[str, Decimal]] = []
            for market in markets:
                row = by_cell.get((market.id, commodity.id))
                if (
                    row is not None
                    and row.status == IndexStatus.PUBLISHED
                    and row.value is not None
                ):
                    published.append((market.code, Decimal(str(row.value))))
            if not published:
                result.append(
                    {
                        "commodity_code": commodity.code,
                        "unit": commodity.canonical_unit,
                        "status": "insufficient_data",
                        "value": None,
                        "markets_published": 0,
                        "markets_expected": len(markets),
                        "min": None,
                        "max": None,
                        "spread_pct": None,
                    }
                )
                continue
            values = [v for _, v in published]
            value = Decimal(str(median(values)))
            min_m, min_v = min(published, key=lambda x: x[1])
            max_m, max_v = max(published, key=lambda x: x[1])
            spread = None
            if min_v > 0:
                spread = round(float((max_v - min_v) / min_v * 100), 1)
            result.append(
                {
                    "commodity_code": commodity.code,
                    "unit": commodity.canonical_unit,
                    "status": "published",
                    "value": value,
                    "markets_published": len(published),
                    "markets_expected": len(markets),
                    "min": {"market_code": min_m, "value": min_v},
                    "max": {"market_code": max_m, "value": max_v},
                    "spread_pct": spread,
                }
            )
        return result

    def _cell_dict(
        self, market: Any, commodity: Any, row: IndexValue | None
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        window_end = now
        window_start = now - timedelta(hours=WINDOW_HOURS)
        if row is None:
            return {
                "market_code": market.code,
                "market_name_en": market.name_en,
                "market_name_am": market.name_am,
                "commodity_code": commodity.code,
                "commodity_name_en": commodity.name_en,
                "commodity_name_am": commodity.name_am,
                "unit": commodity.canonical_unit,
                "currency": CURRENCY,
                "status": "insufficient_data",
                "value": None,
                "n_submissions": 0,
                "n_contributors": 0,
                "source_mix": {},
                "window_start": window_start,
                "window_end": window_end,
                "computed_at": now,
                "method_version": METHOD_VERSION_INDEX,
                "insufficient_reason": "no_submissions",
            }
        reason = None
        if row.status != IndexStatus.PUBLISHED:
            reason = "below_threshold" if row.n_submissions > 0 else "no_submissions"
        return {
            "market_code": market.code,
            "market_name_en": market.name_en,
            "market_name_am": market.name_am,
            "commodity_code": commodity.code,
            "commodity_name_en": commodity.name_en,
            "commodity_name_am": commodity.name_am,
            "unit": row.unit,
            "currency": CURRENCY,
            "status": row.status.value,
            "value": row.value,
            "n_submissions": row.n_submissions,
            "n_contributors": row.n_contributors,
            "source_mix": row.source_mix or {},
            "window_start": row.window_start,
            "window_end": row.window_end,
            "computed_at": row.computed_at,
            "method_version": row.method_version,
            "insufficient_reason": reason,
        }

    def _meta(
        self,
        method_version: str,
        *,
        cells_expected: int,
        cells_published: int,
        cells_insufficient: int,
    ) -> ResponseMeta:
        now = datetime.now(UTC)
        coverage_pct = (
            round(cells_published / cells_expected * 100, 1) if cells_expected else 0.0
        )
        snap = f"snap_{now.strftime('%Y-%m-%dT%H')}_v1"
        return ResponseMeta(
            generated_at=now,
            method_version=method_version,
            city=CITY_CODE,
            currency=CURRENCY,
            window=MetaWindow(
                start=now - timedelta(hours=WINDOW_HOURS),
                end=now,
                hours=WINDOW_HOURS,
            ),
            coverage=MetaCoverage(
                cells_expected=cells_expected,
                cells_published=cells_published,
                cells_insufficient=cells_insufficient,
                coverage_pct=coverage_pct,
            ),
            licence_class="commercial_permitted",
            snapshot_id=snap,
        )
