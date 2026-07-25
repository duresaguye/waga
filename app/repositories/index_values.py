from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.index_values import IndexValue
from app.models.reference_data import Commodity, Market


class IndexValueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, index_value: IndexValue) -> None:
        self._session.add(index_value)

    async def get_latest_for_cell(
        self,
        *,
        market_id: int,
        commodity_id: int,
    ) -> IndexValue | None:
        statement = (
            select(IndexValue)
            .where(
                IndexValue.market_id == market_id,
                IndexValue.commodity_id == commodity_id,
            )
            .order_by(IndexValue.computed_at.desc())
            .limit(1)
        )
        return cast(IndexValue | None, await self._session.scalar(statement))

    async def list_latest_per_cell(
        self,
        *,
        market_ids: list[int] | None = None,
        commodity_ids: list[int] | None = None,
    ) -> list[IndexValue]:
        subquery = (
            select(
                IndexValue.market_id,
                IndexValue.commodity_id,
                func.max(IndexValue.computed_at).label("max_computed_at"),
            )
            .group_by(IndexValue.market_id, IndexValue.commodity_id)
            .subquery()
        )
        statement = (
            select(IndexValue)
            .join(
                subquery,
                (IndexValue.market_id == subquery.c.market_id)
                & (IndexValue.commodity_id == subquery.c.commodity_id)
                & (IndexValue.computed_at == subquery.c.max_computed_at),
            )
            .order_by(IndexValue.market_id, IndexValue.commodity_id)
        )
        values = list(await self._session.scalars(statement))
        if market_ids is not None:
            allowed_markets = set(market_ids)
            values = [row for row in values if row.market_id in allowed_markets]
        if commodity_ids is not None:
            allowed_commodities = set(commodity_ids)
            values = [row for row in values if row.commodity_id in allowed_commodities]
        return values

    async def list_for_cell_in_range(
        self,
        *,
        market_id: int | None,
        commodity_id: int,
        start: datetime,
        end: datetime,
    ) -> list[IndexValue]:
        statement: Select[tuple[IndexValue]] = select(IndexValue).where(
            IndexValue.commodity_id == commodity_id,
            IndexValue.computed_at >= start,
            IndexValue.computed_at <= end,
        )
        if market_id is not None:
            statement = statement.where(IndexValue.market_id == market_id)
        statement = statement.order_by(IndexValue.computed_at.asc())
        return list(await self._session.scalars(statement))

    async def list_panel_rows(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        statement = (
            select(
                IndexValue,
                Market,
                Commodity,
            )
            .join(Market, Market.id == IndexValue.market_id)
            .join(Commodity, Commodity.id == IndexValue.commodity_id)
            .where(
                IndexValue.computed_at >= start,
                IndexValue.computed_at <= end,
            )
            .order_by(IndexValue.computed_at.asc(), Market.code, Commodity.code)
        )
        rows = await self._session.execute(statement)
        items: list[dict[str, Any]] = []
        for index_value, market, commodity in rows.all():
            items.append(
                {
                    "index_value": index_value,
                    "market": market,
                    "commodity": commodity,
                }
            )
        return items

    async def get_by_trigger_verification(
        self,
        verification_id: UUID,
        *,
        method_version: str,
    ) -> IndexValue | None:
        statement = select(IndexValue).where(
            IndexValue.trigger_verification_id == verification_id,
            IndexValue.method_version == method_version,
        )
        return cast(IndexValue | None, await self._session.scalar(statement))
