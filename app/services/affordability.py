"""Food Affordability Score and MEB bridge."""

from __future__ import annotations

from datetime import date, timedelta

from app.config import Settings
from app.models.enums import IndexStatus
from app.repositories.reference_data import ReferenceDataRepository
from app.services.api_errors import contract_error
from app.services.basket_config import PHASE1_BASKET
from app.services.prices_read import PricesReadService
from app.services.read_meta import build_meta


def _affordability_band(change_pct: float) -> str:
    if change_pct < 3:
        return "Stable"
    if change_pct < 8:
        return "Watch"
    if change_pct < 15:
        return "Tightening"
    return "Severe"


def _affordability_score(change_pct: float) -> float:
    return round(max(0.0, min(100.0, 100.0 - 5.0 * change_pct)), 1)


class AffordabilityService:
    def __init__(
        self,
        prices: PricesReadService,
        reference_data: ReferenceDataRepository,
        settings: Settings,
    ) -> None:
        self._prices = prices
        self._reference_data = reference_data
        self._settings = settings

    async def get_affordability(
        self,
        *,
        basket_code: str = "phase1_staple5",
        household_size: int = 5,
        compare_days: int = 30,
    ) -> dict:
        basket = _resolve_basket(basket_code)
        current = await self._prices.get_current_prices()
        city_prices = {
            row["commodity_code"]: row for row in current["data"]["city_prices"]
        }
        prior_date = date.today() - timedelta(days=compare_days)

        items = []
        missing: list[str] = []
        cost_now = 0.0
        cost_prior = 0.0
        item_changes: list[tuple[str, float, float, float]] = []

        for basket_item in basket["items"]:
            code = basket_item["commodity_code"]
            quantity = float(basket_item["quantity"])
            city_row = city_prices.get(code)
            if city_row is None or city_row.get("status") != IndexStatus.PUBLISHED.value:
                missing.append(code)
                continue

            unit_now = city_row["value"]
            if unit_now is None:
                missing.append(code)
                continue

            commodity = await self._reference_data.get_commodity_by_code(code)
            if commodity is None:
                missing.append(code)
                continue

            unit_prior = await self._prices.get_city_median_on_date(commodity, prior_date)
            item_cost_now = round(quantity * unit_now, 2)
            item_cost_prior = (
                round(quantity * unit_prior, 2) if unit_prior is not None else None
            )
            cost_now += item_cost_now
            if item_cost_prior is not None:
                cost_prior += item_cost_prior

            change_pct = None
            if item_cost_prior and item_cost_prior > 0:
                change_pct = round(
                    ((item_cost_now - item_cost_prior) / item_cost_prior) * 100,
                    1,
                )
            items.append(
                {
                    "commodity_code": code,
                    "quantity": basket_item["quantity"],
                    "unit": basket_item["unit"],
                    "unit_price_now": round(unit_now, 2),
                    "unit_price_prior": round(unit_prior, 2) if unit_prior is not None else None,
                    "cost_now": item_cost_now,
                    "cost_prior": item_cost_prior,
                    "change_pct": change_pct,
                    "contribution_to_change_pct": None,
                    "status": IndexStatus.PUBLISHED.value,
                }
            )
            if change_pct is not None and item_cost_prior is not None:
                item_changes.append((code, item_cost_now - item_cost_prior, change_pct, item_cost_now))

        if missing:
            return {
                "meta": current["meta"],
                "data": {
                    "basket_code": basket_code,
                    "household_size": household_size,
                    "period_days": compare_days,
                    "status": IndexStatus.INSUFFICIENT_DATA.value,
                    "cost_now": None,
                    "cost_prior": None,
                    "prior_date": prior_date.isoformat(),
                    "change_abs": None,
                    "change_pct": None,
                    "score": None,
                    "band": None,
                    "method_version": self._settings.affordability_method_version,
                    "items": items,
                    "missing_commodities": missing,
                },
            }

        change_abs = round(cost_now - cost_prior, 2)
        change_pct = round((change_abs / cost_prior) * 100, 1) if cost_prior > 0 else 0.0
        total_delta = sum(delta for _, delta, _, _ in item_changes) or 0.0
        for item in items:
            code = item["commodity_code"]
            match = next((row for row in item_changes if row[0] == code), None)
            if match and total_delta:
                item["contribution_to_change_pct"] = round(
                    (match[1] / total_delta) * change_pct,
                    1,
                )

        return {
            "meta": current["meta"],
            "data": {
                "basket_code": basket_code,
                "household_size": household_size,
                "period_days": compare_days,
                "status": IndexStatus.PUBLISHED.value,
                "cost_now": round(cost_now, 2),
                "cost_prior": round(cost_prior, 2),
                "prior_date": prior_date.isoformat(),
                "change_abs": change_abs,
                "change_pct": change_pct,
                "score": _affordability_score(change_pct),
                "band": _affordability_band(change_pct),
                "method_version": self._settings.affordability_method_version,
                "items": items,
                "missing_commodities": [],
            },
        }

    async def get_meb_food_line(self, *, household_size: int = 5) -> dict:
        affordability = await self.get_affordability(household_size=household_size)
        data = affordability["data"]
        settings = self._settings
        meta = build_meta(settings, latest_values=[])
        return {
            "meta": meta,
            "data": {
                "household_size": household_size,
                "waga_food_line_now": data["cost_now"],
                "waga_food_line_prior": data["cost_prior"],
                "change_pct": data["change_pct"],
                "coverage_note": (
                    "Waga prices 5 of the 53 ECWG MEB items. "
                    "This is the tracked-staple line only."
                ),
                "ecwg_reference": {
                    "source": settings.ecwg_meb_source,
                    "national_meb_full_etb": settings.ecwg_national_meb_full_etb,
                    "national_meb_food_etb": settings.ecwg_national_meb_food_etb,
                    "as_of": settings.ecwg_as_of,
                    "review_cadence_months": settings.ecwg_review_cadence_months,
                    "revision_trigger": settings.ecwg_revision_trigger,
                },
                "consecutive_months_rising": 0,
                "revision_trigger_met": False,
            },
        }


def _resolve_basket(basket_code: str) -> dict:
    if basket_code == PHASE1_BASKET["code"]:
        return PHASE1_BASKET
    raise contract_error(
        "unknown_basket",
        f"No basket with code '{basket_code}'",
        field="basket",
    )
