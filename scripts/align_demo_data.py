"""Align catalogue codes + ensure pitch demo index data."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.commands.seed_phase1 import seed as seed_phase1
from app.config import get_settings
from app.models.enums import IndexStatus
from app.models.index_values import IndexValue
from app.models.reference_data import Commodity, Market
from app.repositories.index_values import IndexValueRepository
from app.repositories.reference_data import ReferenceDataRepository
from app.repositories.submissions import SubmissionRepository
from app.services.basket_config import PHASE1_BASKET
from app.services.index_calculation import IndexCalculationService
from app.services.index_rules import PHASE1_COMMODITY_CODES, PHASE1_MARKET_CODES


def _async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


async def inspect(session) -> None:
    markets = (
        await session.execute(select(Market.id, Market.code, Market.name_en, Market.is_active))
    ).all()
    commodities = (
        await session.execute(
            select(Commodity.id, Commodity.code, Commodity.name_en, Commodity.is_active)
        )
    ).all()
    print("MARKETS:")
    for row in markets:
        print(" ", row)
    print("COMMODITIES:")
    for row in commodities:
        print(" ", row)
    print(
        "VERIFICATIONS:",
        (
            await session.execute(
                text(
                    "SELECT outcome, count(*)::int "
                    "FROM submission_verifications GROUP BY 1"
                )
            )
        ).all(),
    )
    print(
        "INDEX_VALUES:",
        (
            await session.execute(
                text("SELECT status, count(*)::int FROM index_values GROUP BY 1")
            )
        ).all(),
    )


async def rename_codes(session) -> None:
    commodity_renames = {
        "teff": "teff_mixed",
        "cooking-oil": "cooking_oil",
        "cooking oil": "cooking_oil",
    }
    market_renames = {
        "ehil-berenda": "ehil_berenda",
        "atikilt-tera": "atikilt_tera",
    }

    for old, new in commodity_renames.items():
        old_row = (
            await session.execute(select(Commodity).where(Commodity.code == old))
        ).scalar_one_or_none()
        new_row = (
            await session.execute(select(Commodity).where(Commodity.code == new))
        ).scalar_one_or_none()
        if old_row is None:
            continue
        if new_row is None:
            print(f"rename commodity {old} -> {new}")
            old_row.code = new
            if new == "teff_mixed":
                old_row.name_en = "Teff (mixed)"
            if new == "cooking_oil":
                old_row.name_en = "Cooking oil"
                old_row.canonical_unit = "liter"
        else:
            print(f"merge commodity {old} -> {new}")
            await session.execute(
                text(
                    "UPDATE submissions SET commodity_id = :new WHERE commodity_id = :old"
                ),
                {"new": new_row.id, "old": old_row.id},
            )
            await session.execute(
                text(
                    "UPDATE index_values SET commodity_id = :new WHERE commodity_id = :old"
                ),
                {"new": new_row.id, "old": old_row.id},
            )
            old_row.is_active = False
            old_row.code = f"dep_{old_row.id}"

    for old, new in market_renames.items():
        old_row = (
            await session.execute(select(Market).where(Market.code == old))
        ).scalar_one_or_none()
        new_row = (
            await session.execute(select(Market).where(Market.code == new))
        ).scalar_one_or_none()
        if old_row is None:
            continue
        if new_row is None:
            print(f"rename market {old} -> {new}")
            old_row.code = new
        else:
            print(f"merge market {old} -> {new}")
            await session.execute(
                text("UPDATE submissions SET market_id = :new WHERE market_id = :old"),
                {"new": new_row.id, "old": old_row.id},
            )
            await session.execute(
                text("UPDATE index_values SET market_id = :new WHERE market_id = :old"),
                {"new": new_row.id, "old": old_row.id},
            )
            old_row.is_active = False
            old_row.code = f"dep_{old_row.id}"

    await session.commit()


async def seed_pitch_index(session, settings) -> None:
    ref = ReferenceDataRepository(session)
    markets = []
    for code in PHASE1_MARKET_CODES:
        market = await ref.get_market_by_code(code)
        if market is not None and market.is_active:
            markets.append(market)
    if len(markets) < 3:
        raise RuntimeError(f"Need >=3 phase1 markets, found {len(markets)}")

    now_prices = {
        "teff_mixed": Decimal("120"),
        "wheat": Decimal("85"),
        "maize": Decimal("55"),
        "onion": Decimal("70"),
        "cooking_oil": Decimal("280"),
    }
    prior_prices = {
        "teff_mixed": Decimal("100"),
        "wheat": Decimal("78"),
        "maize": Decimal("50"),
        "onion": Decimal("60"),
        "cooking_oil": Decimal("250"),
    }

    now = datetime.now(UTC)
    prior = now - timedelta(days=30)
    ver_id = (
        await session.execute(text("SELECT id FROM submission_verifications LIMIT 1"))
    ).scalar_one_or_none()
    if ver_id is None:
        print("No verification row for index FK — skipping pitch seed")
        return

    for code in PHASE1_COMMODITY_CODES:
        commodity = await ref.get_commodity_by_code(code)
        if commodity is None:
            print("missing commodity", code)
            continue
        for when, price_map, tag in (
            (prior, prior_prices, "p"),
            (now, now_prices, "n"),
        ):
            price = price_map[code]
            for market in markets[:3]:
                # method_version max 32 chars
                method = f"pitch-{tag}-m{market.id}-c{commodity.id}"
                assert len(method) <= 32, method
                existing = (
                    await session.execute(
                        select(IndexValue).where(
                            IndexValue.trigger_verification_id == ver_id,
                            IndexValue.method_version == method,
                        )
                    )
                ).scalar_one_or_none()
                if existing is not None:
                    existing.value = price
                    existing.status = IndexStatus.PUBLISHED
                    existing.n_submissions = 3
                    existing.n_contributors = 3
                    existing.computed_at = when
                    existing.window_start = when - timedelta(
                        hours=settings.index_window_hours
                    )
                    existing.window_end = when
                    existing.unit = commodity.canonical_unit
                    existing.source_mix = {"seed": 3}
                    existing.market_id = market.id
                    existing.commodity_id = commodity.id
                    print("update", method, price)
                    continue
                session.add(
                    IndexValue(
                        id=uuid4(),
                        market_id=market.id,
                        commodity_id=commodity.id,
                        trigger_verification_id=ver_id,
                        method_version=method,
                        window_start=when
                        - timedelta(hours=settings.index_window_hours),
                        window_end=when,
                        value=price,
                        unit=commodity.canonical_unit,
                        n_submissions=3,
                        n_contributors=3,
                        source_mix={"seed": 3},
                        status=IndexStatus.PUBLISHED,
                        computed_at=when,
                    )
                )
                print("insert", method, price)

    await session.commit()


async def rebuild(session, settings) -> None:
    service = IndexCalculationService(
        session,
        SubmissionRepository(session),
        IndexValueRepository(session),
        ReferenceDataRepository(session),
        settings,
    )
    count = await service.rebuild_all()
    print("rebuild_all processed", count)


async def main() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    url = _async_url(os.environ["WAGA_DATABASE_URL"])
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    print("=== BEFORE ===")
    async with factory() as session:
        await inspect(session)

    print("\n=== RENAME CODES ===")
    async with factory() as session:
        await rename_codes(session)

    print("\n=== SEED PHASE1 CATALOGUE ===")
    # seed_phase1 uses app.database.session_factory (same DB URL from settings)
    await seed_phase1()

    print("\n=== REBUILD FROM ACCEPTED ===")
    async with factory() as session:
        await rebuild(session, settings)

    print("\n=== SEED PITCH INDEX CELLS ===")
    async with factory() as session:
        await seed_pitch_index(session, settings)

    print("\n=== AFTER ===")
    async with factory() as session:
        await inspect(session)
        for item in PHASE1_BASKET["items"]:
            code = item["commodity_code"]
            row = (
                await session.execute(
                    text(
                        "SELECT c.code, "
                        "count(*) FILTER (WHERE i.status = 'published')::int "
                        "FROM commodities c "
                        "LEFT JOIN index_values i ON i.commodity_id = c.id "
                        "WHERE c.code = :code GROUP BY c.code"
                    ),
                    {"code": code},
                )
            ).first()
            print("basket", code, row)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
