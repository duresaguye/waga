"""Spike detection alerts (waga-spike-v1 interim)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from statistics import mean, pstdev

from app.config import Settings
from app.models.enums import IndexStatus
from app.repositories.index_values import IndexValueRepository
from app.repositories.reference_data import ReferenceDataRepository
from app.services.prices_read import PricesReadService
from app.services.read_meta import build_meta, iso_z

Z_THRESHOLDS = [1.0, 2.0, 3.0]
DEVIATION_THRESHOLDS = [2.0, 5.0, 10.0]
SPIKE_BANDS = ["normal", "stress", "alert", "crisis"]
MIN_BAND_RANK = {"normal": 0, "stress": 1, "alert": 2, "crisis": 3}


def _band_from_z(z: float) -> str:
    if z < Z_THRESHOLDS[0]:
        return "normal"
    if z < Z_THRESHOLDS[1]:
        return "stress"
    if z < Z_THRESHOLDS[2]:
        return "alert"
    return "crisis"


def _band_from_deviation(deviation_pct: float) -> str:
    if deviation_pct < DEVIATION_THRESHOLDS[0]:
        return "normal"
    if deviation_pct < DEVIATION_THRESHOLDS[1]:
        return "stress"
    if deviation_pct < DEVIATION_THRESHOLDS[2]:
        return "alert"
    return "crisis"


def _weaker_band(left: str, right: str) -> str:
    return left if MIN_BAND_RANK[left] <= MIN_BAND_RANK[right] else right


class AlertsService:
    def __init__(
        self,
        prices: PricesReadService,
        reference_data: ReferenceDataRepository,
        index_values: IndexValueRepository,
        settings: Settings,
    ) -> None:
        self._prices = prices
        self._reference_data = reference_data
        self._index_values = index_values
        self._settings = settings

    async def get_alerts(self, *, min_band: str = "stress") -> dict:
        markets = await self._reference_data.list_markets(active_only=True)
        commodities = await self._reference_data.list_commodities(active_only=True)
        latest = await self._prices._load_latest_cells(markets, commodities)
        meta = build_meta(
            self._settings,
            latest_values=latest,
            matrix_size=len(markets) * len(commodities),
            method_version=self._settings.spike_method_version,
        )
        min_rank = MIN_BAND_RANK.get(min_band, MIN_BAND_RANK["stress"])

        alerts: list[dict] = []
        window_days = 30
        now = datetime.now(UTC)
        start = now - timedelta(days=window_days)

        for market in markets:
            for commodity in commodities:
                current = next(
                    (
                        row
                        for row in latest
                        if row.market_id == market.id
                        and row.commodity_id == commodity.id
                    ),
                    None,
                )
                if current is None or current.status != IndexStatus.PUBLISHED or current.value is None:
                    continue

                rows = await self._index_values.list_for_cell_in_range(
                    market_id=market.id,
                    commodity_id=commodity.id,
                    start=start,
                    end=now,
                )
                published = [
                    (row.computed_at, float(row.value))
                    for row in rows
                    if row.status == IndexStatus.PUBLISHED and row.value is not None
                ]
                if len(published) < 5:
                    continue

                xs = list(range(len(published)))
                ys = [value for _, value in published]
                x_mean = mean(xs)
                y_mean = mean(ys)
                slope_num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys, strict=True))
                slope_den = sum((x - x_mean) ** 2 for x in xs) or 1.0
                slope = slope_num / slope_den
                intercept = y_mean - slope * x_mean
                expected = intercept + slope * (len(published) - 1)
                current_value = float(current.value)
                residual = current_value - expected
                residuals = [
                    value - (intercept + slope * index)
                    for index, value in zip(xs, ys, strict=True)
                ]
                sigma = pstdev(residuals) if len(residuals) > 1 else 0.0
                spike = abs(residual / sigma) if sigma else 0.0
                pct_above = ((current_value - expected) / expected * 100) if expected else 0.0
                z_band = _band_from_z(spike)
                dev_band = _band_from_deviation(abs(pct_above))
                band = _weaker_band(z_band, dev_band)
                if MIN_BAND_RANK[band] < min_rank:
                    continue

                median_30d = mean(ys)
                alerts.append(
                    {
                        "market_code": market.code,
                        "commodity_code": commodity.code,
                        "spike": round(spike, 2),
                        "band": band,
                        "value": round(current_value, 2),
                        "expected": round(expected, 2),
                        "median_30d": round(median_30d, 2),
                        "pct_above_expected": round(pct_above, 1),
                        "first_detected_at": iso_z(current.computed_at),
                        "consecutive_days": 1,
                    }
                )

        alerts.sort(key=lambda item: item["spike"], reverse=True)
        return {
            "meta": meta,
            "data": {
                "method_version": self._settings.spike_method_version,
                "alps_comparable": False,
                "alps_comparable_note": (
                    "Detrended residual z-score over a 30-day daily window, banded jointly "
                    "with the percent deviation from trend. Same structure as WFP ALPS but daily "
                    "rather than monthly. Real ALPS needs 24 monthly observations per cell."
                ),
                "window_days": window_days,
                "min_deviation_pct": DEVIATION_THRESHOLDS[0],
                "z_thresholds": Z_THRESHOLDS,
                "deviation_thresholds_pct": DEVIATION_THRESHOLDS,
                "alerts": alerts,
            },
        }
