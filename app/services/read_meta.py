"""Build standard API envelope metadata for read endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.config import Settings
from app.models.enums import IndexStatus, LicenceClass
from app.models.index_values import IndexValue
from app.models.reference_data import Commodity, Market, Sector


def iso_z(value: datetime | None) -> str:
    if value is None:
        value = datetime.now(UTC)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def snapshot_id(generated_at: datetime, method_version: str) -> str:
    stamp = generated_at.astimezone(UTC).strftime("%Y-%m-%dT%H")
    version_suffix = method_version.split("-")[-1]
    return f"snap_{stamp}_{version_suffix}"


def build_meta(
    settings: Settings,
    *,
    latest_values: list[IndexValue],
    matrix_size: int | None = None,
    method_version: str | None = None,
    licence_class: LicenceClass = LicenceClass.COMMERCIAL_PERMITTED,
) -> dict:
    now = datetime.now(UTC)
    window_end = now
    window_start = now - timedelta(hours=settings.index_window_hours)
    if latest_values:
        window_end = max(row.window_end for row in latest_values)
        window_start = min(row.window_start for row in latest_values)

    expected = matrix_size if matrix_size is not None else len(latest_values)
    published = sum(1 for row in latest_values if row.status == IndexStatus.PUBLISHED)
    insufficient = max(expected - published, 0)
    coverage_pct = round((published / expected) * 100, 1) if expected else 0.0

    return {
        "generated_at": iso_z(now),
        "method_version": method_version or settings.method_version,
        "city": settings.city_code,
        "currency": settings.currency_code,
        "window": {
            "start": iso_z(window_start),
            "end": iso_z(window_end),
            "hours": settings.index_window_hours,
        },
        "coverage": {
            "cells_expected": expected,
            "cells_published": published,
            "cells_insufficient": insufficient,
            "coverage_pct": coverage_pct,
        },
        "licence_class": licence_class.value,
        "snapshot_id": snapshot_id(now, method_version or settings.method_version),
    }


def insufficient_reason(index_value: IndexValue, *, threshold: int) -> str | None:
    if index_value.status == IndexStatus.PUBLISHED:
        return None
    if index_value.n_submissions == 0:
        return "no_submissions"
    if index_value.n_submissions < threshold:
        return "below_threshold"
    return "below_threshold"


def decimal_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def market_to_dict(market: Market) -> dict:
    return {
        "code": market.code,
        "name_en": market.name_en,
        "name_am": market.name_am,
        "latitude": decimal_to_float(market.latitude),
        "longitude": decimal_to_float(market.longitude),
        "is_active": market.is_active,
    }


def commodity_to_dict(commodity: Commodity, *, sector: Sector | None = None) -> dict:
    category = sector.name_en if sector is not None else "staples"
    return {
        "code": commodity.code,
        "name_en": commodity.name_en,
        "name_am": commodity.name_am,
        "category": category,
        "unit": commodity.canonical_unit,
        "price_hint_low": decimal_to_float(commodity.price_hint_low),
        "price_hint_high": decimal_to_float(commodity.price_hint_high),
    }


def index_value_to_cell(
    index_value: IndexValue,
    *,
    market: Market,
    commodity: Commodity,
    settings: Settings,
) -> dict:
    return {
        "market_code": market.code,
        "market_name_en": market.name_en,
        "market_name_am": market.name_am,
        "commodity_code": commodity.code,
        "commodity_name_en": commodity.name_en,
        "commodity_name_am": commodity.name_am,
        "unit": index_value.unit,
        "currency": settings.currency_code,
        "status": index_value.status.value,
        "value": decimal_to_float(index_value.value),
        "n_submissions": index_value.n_submissions,
        "n_contributors": index_value.n_contributors,
        "source_mix": index_value.source_mix,
        "window_start": iso_z(index_value.window_start),
        "window_end": iso_z(index_value.window_end),
        "computed_at": iso_z(index_value.computed_at),
        "method_version": index_value.method_version,
        "insufficient_reason": insufficient_reason(
            index_value,
            threshold=settings.publication_threshold,
        ),
    }
