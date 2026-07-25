"""Seed Phase 1 Addis markets, staples, and commodity synonyms."""

from __future__ import annotations

import asyncio

from app.database import session_factory
from app.models.reference_data import Commodity, CommoditySynonym, Market, Sector
from app.repositories.reference_data import ReferenceDataRepository
from app.services.text_normalization import STAPLE_SYNONYMS
from telegram_bot.reference import COMMODITIES as BOT_COMMODITIES
from telegram_bot.reference import MARKETS as BOT_MARKETS

SECTOR_CODE = "staples"
SECTOR_NAME_EN = "Staple foods"
SECTOR_NAME_AM = "Staple foods"


async def seed() -> None:
    async with session_factory() as session:
        repo = ReferenceDataRepository(session)
        sector = await _ensure_sector(repo)

        for market in BOT_MARKETS:
            existing = await repo.get_market_by_code(market.code)
            if existing is None:
                repo.add_market(
                    Market(
                        code=market.code,
                        name_en=market.name_en,
                        name_am=market.name_am,
                        city_en="Addis Ababa",
                        city_am="Addis Ababa",
                        is_active=True,
                    )
                )
                print(f"market + {market.code}")
            else:
                print(f"market = {market.code}")

        commodity_ids: dict[str, int] = {}
        for commodity in BOT_COMMODITIES:
            existing = await repo.get_commodity_by_code(commodity.code)
            if existing is None:
                row = Commodity(
                    sector_id=sector.id,
                    code=commodity.code,
                    name_en=commodity.name_en,
                    name_am=commodity.name_am,
                    canonical_unit=commodity.unit,
                    is_active=True,
                )
                repo.add_commodity(row)
                await session.flush()
                commodity_ids[commodity.code] = row.id
                print(f"commodity + {commodity.code}")
            else:
                commodity_ids[commodity.code] = existing.id
                print(f"commodity = {commodity.code}")

        for code, surface, normalized, script in STAPLE_SYNONYMS:
            commodity_id = commodity_ids.get(code)
            if commodity_id is None:
                print(f"synonym skip (missing commodity) {code}: {surface}")
                continue
            existing = await repo.get_synonym_by_normalized_script(
                normalized=normalized,
                script=script,
            )
            if existing is None:
                repo.add_synonym(
                    CommoditySynonym(
                        commodity_id=commodity_id,
                        surface=surface,
                        normalized=normalized,
                        script=script,
                        is_active=True,
                    )
                )
                print(f"synonym + {code}: {surface} ({script.value})")
            else:
                print(f"synonym = {code}: {surface}")

        await session.commit()
        print("Phase 1 seed complete.")


async def _ensure_sector(repo: ReferenceDataRepository) -> Sector:
    sectors = await repo.list_sectors()
    for sector in sectors:
        if sector.code == SECTOR_CODE:
            return sector
    sector = Sector(
        code=SECTOR_CODE,
        name_en=SECTOR_NAME_EN,
        name_am=SECTOR_NAME_AM,
        description="Phase 1 staple foods",
        is_active=True,
    )
    repo.add_sector(sector)
    await repo._session.flush()
    print(f"sector + {SECTOR_CODE}")
    return sector


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
