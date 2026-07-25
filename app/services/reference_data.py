from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference_data import (
    Commodity,
    CommoditySynonym,
    Market,
    Sector,
)
from app.repositories.reference_data import ReferenceDataRepository
from app.services.exceptions import (
    ReferenceDataConflictError,
    ReferenceDataNotFoundError,
)


class ReferenceDataService:
    def __init__(
        self,
        session: AsyncSession,
        reference_data: ReferenceDataRepository,
    ) -> None:
        self._session = session
        self._repo = reference_data

    # -- sectors -----------------------------------------------------------------

    async def list_sectors(self, *, active_only: bool = False) -> list[Sector]:
        return await self._repo.list_sectors(active_only=active_only)

    async def get_sector(self, sector_id: int) -> Sector:
        sector = await self._repo.get_sector(sector_id)
        if sector is None:
            raise ReferenceDataNotFoundError(f"Sector {sector_id} not found")
        return sector

    async def create_sector(
        self,
        *,
        code: str,
        name_en: str,
        name_am: str,
        description: str | None,
        is_active: bool,
    ) -> Sector:
        sector = Sector(
            code=code,
            name_en=name_en,
            name_am=name_am,
            description=description,
            is_active=is_active,
        )
        self._repo.add_sector(sector)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise ReferenceDataConflictError("Sector code already exists") from error
        return sector

    async def update_sector(self, sector_id: int, **fields) -> Sector:
        sector = await self.get_sector(sector_id)
        for key, value in fields.items():
            if value is not None:
                setattr(sector, key, value)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise ReferenceDataConflictError("Sector code already exists") from error
        return sector

    # -- markets -----------------------------------------------------------------

    async def list_markets(self, *, active_only: bool = False) -> list[Market]:
        return await self._repo.list_markets(active_only=active_only)

    async def get_market(self, market_id: int) -> Market:
        market = await self._repo.get_market(market_id)
        if market is None:
            raise ReferenceDataNotFoundError(f"Market {market_id} not found")
        return market

    async def create_market(
        self,
        *,
        code: str,
        name_en: str,
        name_am: str,
        city_en: str,
        city_am: str,
        latitude,
        longitude,
        is_active: bool,
    ) -> Market:
        market = Market(
            code=code,
            name_en=name_en,
            name_am=name_am,
            city_en=city_en,
            city_am=city_am,
            latitude=latitude,
            longitude=longitude,
            is_active=is_active,
        )
        self._repo.add_market(market)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise ReferenceDataConflictError("Market code already exists") from error
        return market

    async def update_market(self, market_id: int, **fields) -> Market:
        market = await self.get_market(market_id)
        for key, value in fields.items():
            if value is not None:
                setattr(market, key, value)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise ReferenceDataConflictError("Market code already exists") from error
        return market

    # -- commodities -------------------------------------------------------------

    async def list_commodities(
        self,
        *,
        sector_id: int | None = None,
        active_only: bool = False,
    ) -> list[Commodity]:
        return await self._repo.list_commodities(
            sector_id=sector_id,
            active_only=active_only,
        )

    async def get_commodity(self, commodity_id: int) -> Commodity:
        commodity = await self._repo.get_commodity(commodity_id)
        if commodity is None:
            raise ReferenceDataNotFoundError(f"Commodity {commodity_id} not found")
        return commodity

    async def create_commodity(
        self,
        *,
        sector_id: int,
        code: str,
        name_en: str,
        name_am: str,
        canonical_unit: str,
        allow_conversion: bool,
        price_hint_low,
        price_hint_high,
        is_active: bool,
    ) -> Commodity:
        await self.get_sector(sector_id)
        commodity = Commodity(
            sector_id=sector_id,
            code=code,
            name_en=name_en,
            name_am=name_am,
            canonical_unit=canonical_unit,
            allow_conversion=allow_conversion,
            price_hint_low=price_hint_low,
            price_hint_high=price_hint_high,
            is_active=is_active,
        )
        self._repo.add_commodity(commodity)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise ReferenceDataConflictError("Commodity code already exists") from error
        return commodity

    async def update_commodity(self, commodity_id: int, **fields) -> Commodity:
        commodity = await self.get_commodity(commodity_id)
        if "sector_id" in fields and fields["sector_id"] is not None:
            await self.get_sector(fields["sector_id"])
        for key, value in fields.items():
            if value is not None:
                setattr(commodity, key, value)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise ReferenceDataConflictError("Commodity code already exists") from error
        return commodity

    # -- synonyms ----------------------------------------------------------------

    async def list_synonyms(
        self,
        *,
        commodity_id: int | None = None,
        active_only: bool = False,
    ) -> list[CommoditySynonym]:
        return await self._repo.list_synonyms(
            commodity_id=commodity_id,
            active_only=active_only,
        )

    async def create_synonym(
        self,
        *,
        commodity_id: int,
        surface: str,
        normalized: str,
        script,
        is_active: bool,
    ) -> CommoditySynonym:
        await self.get_commodity(commodity_id)
        synonym = CommoditySynonym(
            commodity_id=commodity_id,
            surface=surface,
            normalized=normalized,
            script=script,
            is_active=is_active,
        )
        self._repo.add_synonym(synonym)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise ReferenceDataConflictError("Synonym already exists for this commodity") from error
        return synonym

    async def update_synonym(self, synonym_id: int, **fields) -> CommoditySynonym:
        synonym = await self._repo.get_synonym(synonym_id)
        if synonym is None:
            raise ReferenceDataNotFoundError(f"Synonym {synonym_id} not found")
        if "commodity_id" in fields and fields["commodity_id"] is not None:
            await self.get_commodity(fields["commodity_id"])
        for key, value in fields.items():
            if value is not None:
                setattr(synonym, key, value)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise ReferenceDataConflictError("Synonym already exists for this commodity") from error
        return synonym
