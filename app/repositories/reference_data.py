from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference_data import (
    Commodity,
    CommoditySynonym,
    Market,
    Sector,
    UnitConversion,
)


class ReferenceDataRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -- sectors -----------------------------------------------------------------

    async def list_sectors(self, *, active_only: bool = False) -> list[Sector]:
        statement = select(Sector).order_by(Sector.id)
        if active_only:
            statement = statement.where(Sector.is_active.is_(True))
        return list(await self._session.scalars(statement))

    async def get_sector(self, sector_id: int) -> Sector | None:
        return cast(Sector | None, await self._session.get(Sector, sector_id))

    def add_sector(self, sector: Sector) -> None:
        self._session.add(sector)

    # -- markets -----------------------------------------------------------------

    async def list_markets(self, *, active_only: bool = False) -> list[Market]:
        statement = select(Market).order_by(Market.id)
        if active_only:
            statement = statement.where(Market.is_active.is_(True))
        return list(await self._session.scalars(statement))

    async def get_market(self, market_id: int) -> Market | None:
        return cast(Market | None, await self._session.get(Market, market_id))

    def add_market(self, market: Market) -> None:
        self._session.add(market)

    # -- commodities -------------------------------------------------------------

    async def list_commodities(
        self,
        *,
        sector_id: int | None = None,
        active_only: bool = False,
    ) -> list[Commodity]:
        statement = select(Commodity).order_by(Commodity.id)
        if sector_id is not None:
            statement = statement.where(Commodity.sector_id == sector_id)
        if active_only:
            statement = statement.where(Commodity.is_active.is_(True))
        return list(await self._session.scalars(statement))

    async def get_commodity(self, commodity_id: int) -> Commodity | None:
        return cast(Commodity | None, await self._session.get(Commodity, commodity_id))

    def add_commodity(self, commodity: Commodity) -> None:
        self._session.add(commodity)

    # -- synonyms ----------------------------------------------------------------

    async def list_synonyms(
        self,
        *,
        commodity_id: int | None = None,
        active_only: bool = False,
    ) -> list[CommoditySynonym]:
        statement = select(CommoditySynonym).order_by(CommoditySynonym.id)
        if commodity_id is not None:
            statement = statement.where(CommoditySynonym.commodity_id == commodity_id)
        if active_only:
            statement = statement.where(CommoditySynonym.is_active.is_(True))
        return list(await self._session.scalars(statement))

    async def get_synonym(self, synonym_id: int) -> CommoditySynonym | None:
        return cast(
            CommoditySynonym | None,
            await self._session.get(CommoditySynonym, synonym_id),
        )

    def add_synonym(self, synonym: CommoditySynonym) -> None:
        self._session.add(synonym)

    # -- unit conversions --------------------------------------------------------

    async def list_unit_conversions(
        self,
        *,
        commodity_id: int | None = None,
    ) -> list[UnitConversion]:
        statement = select(UnitConversion).order_by(UnitConversion.id)
        if commodity_id is not None:
            statement = statement.where(UnitConversion.commodity_id == commodity_id)
        return list(await self._session.scalars(statement))
