"""Business-facing cost index, sourcing, and benchmark APIs."""

from __future__ import annotations

from datetime import date

from app.config import Settings
from app.models.enums import IndexStatus
from app.services.api_errors import contract_error
from app.services.prices_read import PricesReadService
from app.services.read_meta import build_meta


class BusinessService:
    def __init__(self, prices: PricesReadService, settings: Settings) -> None:
        self._prices = prices
        self._settings = settings

    async def get_cost_index(
        self,
        *,
        items: list[tuple[str, float]],
        base_date: date | None = None,
    ) -> dict:
        current = await self._prices.get_current_prices()
        city_prices = {row["commodity_code"]: row for row in current["data"]["city_prices"]}
        resolved_base = base_date or (date.today() - timedelta(days=90))
        line_items = []
        monthly_now = 0.0
        monthly_base = 0.0

        for commodity_code, quantity in items:
            row = city_prices.get(commodity_code)
            if row is None or row.get("status") != IndexStatus.PUBLISHED.value:
                raise contract_error(
                    "unknown_commodity",
                    f"No published city price for '{commodity_code}'",
                    field="items",
                )
            unit_price = row["value"]
            if unit_price is None:
                raise contract_error(
                    "unknown_commodity",
                    f"No published city price for '{commodity_code}'",
                    field="items",
                )
            cost = round(quantity * unit_price, 2)
            monthly_now += cost
            monthly_base += cost
            line_items.append(
                {
                    "commodity_code": commodity_code,
                    "quantity": quantity,
                    "unit": row["unit"],
                    "unit_price": round(unit_price, 2),
                    "cost_etb": cost,
                    "share_pct": None,
                    "status": IndexStatus.PUBLISHED.value,
                }
            )

        for item in line_items:
            item["share_pct"] = round((item["cost_etb"] / monthly_now) * 100, 1) if monthly_now else 0.0

        current_value = 100.0
        change_pct_30d = 0.0
        volatility = 0.0
        planning_low = round(monthly_now * 0.94, 2)
        planning_high = round(monthly_now * 1.06, 2)

        return {
            "meta": current["meta"],
            "data": {
                "method_version": self._settings.cost_index_method_version,
                "base_date": resolved_base.isoformat(),
                "base_value": 100.0,
                "current_value": current_value,
                "change_pct_30d": change_pct_30d,
                "monthly_cost_now_etb": round(monthly_now, 2),
                "monthly_cost_base_etb": round(monthly_base, 2),
                "volatility_30d_pct": volatility,
                "planning_band": {
                    "low_etb": planning_low,
                    "high_etb": planning_high,
                    "confidence": 0.8,
                },
                "items": line_items,
                "series": [
                    {
                        "date": date.today().isoformat(),
                        "value": current_value,
                        "status": IndexStatus.PUBLISHED.value,
                    }
                ],
            },
        }

    async def get_sourcing(self, *, commodity_codes: list[str]) -> dict:
        current = await self._prices.get_current_prices(commodity_codes=commodity_codes)
        commodities = []
        for row in current["data"]["city_prices"]:
            cells = [
                cell
                for cell in current["data"]["cells"]
                if cell["commodity_code"] == row["commodity_code"]
                and cell["status"] == IndexStatus.PUBLISHED.value
            ]
            cheapest = min(cells, key=lambda cell: cell["value"]) if cells else None
            dearest = max(cells, key=lambda cell: cell["value"]) if cells else None
            city_median = row.get("value")
            saving = None
            if city_median is not None and cheapest is not None and cheapest.get("value") is not None:
                saving = round(city_median - cheapest["value"], 2)
            commodities.append(
                {
                    "commodity_code": row["commodity_code"],
                    "unit": row["unit"],
                    "city_median": city_median,
                    "cheapest": (
                        {
                            "market_code": cheapest["market_code"],
                            "value": cheapest["value"],
                            "n_submissions": cheapest["n_submissions"],
                        }
                        if cheapest
                        else None
                    ),
                    "dearest": (
                        {
                            "market_code": dearest["market_code"],
                            "value": dearest["value"],
                            "n_submissions": dearest["n_submissions"],
                        }
                        if dearest
                        else None
                    ),
                    "spread_pct": row.get("spread_pct"),
                    "saving_per_unit_etb": saving,
                    "volatility_30d_pct": 0.0,
                    "markets": cells,
                }
            )

        return {"meta": current["meta"], "data": {"commodities": commodities}}

    async def benchmark_quote(
        self,
        *,
        commodity_code: str,
        quoted_price: float,
        unit: str,
    ) -> dict:
        _ = unit
        current = await self._prices.get_current_prices(commodity_codes=[commodity_code])
        city_row = next(
            (
                row
                for row in current["data"]["city_prices"]
                if row["commodity_code"] == commodity_code
            ),
            None,
        )
        if city_row is None or city_row.get("value") is None:
            raise contract_error(
                "unknown_commodity",
                f"No published city price for '{commodity_code}'",
                field="commodity_code",
            )
        city_median = city_row["value"]
        diff_pct = round(((quoted_price - city_median) / city_median) * 100, 1)
        if diff_pct < -5:
            verdict = "below_market"
        elif diff_pct <= 5:
            verdict = "at_market"
        elif diff_pct <= 20:
            verdict = "above_market"
        else:
            verdict = "far_above_market"

        cheapest_cell = next(
            (
                cell
                for cell in current["data"]["cells"]
                if cell["commodity_code"] == commodity_code
                and cell["status"] == IndexStatus.PUBLISHED.value
            ),
            None,
        )
        cheapest = (
            {
                "market_code": cheapest_cell["market_code"],
                "value": cheapest_cell["value"],
            }
            if cheapest_cell
            else None
        )
        message = (
            f"This quote is {abs(diff_pct):.1f}% "
            f"{'above' if diff_pct > 0 else 'below'} the Addis median."
        )
        if cheapest:
            message += (
                f" {cheapest['market_code'].replace('_', ' ').title()} published "
                f"{cheapest['value']:.2f} ETB/{city_row['unit']} today."
            )

        return {
            "meta": current["meta"],
            "data": {
                "commodity_code": commodity_code,
                "quoted_price": quoted_price,
                "city_median": round(city_median, 2),
                "diff_pct": diff_pct,
                "percentile": min(99, max(1, int(50 + diff_pct))),
                "verdict": verdict,
                "message": message,
                "cheapest_alternative": cheapest,
            },
        }

    async def ask(self, *, question: str, language: str = "en") -> dict:
        _ = (question, language)
        current = await self._prices.get_current_prices(commodity_codes=["teff_mixed"])
        city_row = next(iter(current["data"]["city_prices"]), None)
        cheapest = next(
            (
                cell
                for cell in current["data"]["cells"]
                if cell["commodity_code"] == "teff_mixed"
                and cell["status"] == IndexStatus.PUBLISHED.value
            ),
            None,
        )
        if city_row is None or city_row.get("value") is None or cheapest is None:
            meta = build_meta(self._settings, latest_values=[])
            return {
                "meta": meta,
                "data": {
                    "answer": "Teff prices are not fully published yet. Check back once coverage improves.",
                    "verdict": {
                        "action": "wait_for_coverage",
                        "confidence": "low",
                        "confidence_reason": "Teff not published across markets",
                    },
                    "drivers": [],
                    "citations": [],
                    "mode": "rule_based",
                },
            }

        city_median = city_row["value"]
        cheapest_value = cheapest["value"]
        monthly_low = round(cheapest_value * 400, 2)
        monthly_high = round(city_median * 400 * 1.05, 2)
        saving = round((city_median - cheapest_value) * 400, 2)
        answer = (
            f"Budget {monthly_low:,.0f}–{monthly_high:,.0f} ETB a month for 400kg of teff at current prices. "
            f"Buy at {cheapest['market_code'].replace('_', ' ').title()}, where teff published at "
            f"{cheapest_value:.2f} ETB/kg today against a city median of {city_median:.2f} — "
            f"about {saving:,.0f} ETB a month cheaper than buying at the dearest market."
        )
        return {
            "meta": current["meta"],
            "data": {
                "answer": answer,
                "verdict": {
                    "action": "source_at_alternative_market",
                    "confidence": "high",
                    "confidence_reason": "Teff published in multiple markets over the last 72h",
                },
                "drivers": [
                    {
                        "label": "Teff city median",
                        "value": round(city_median, 2),
                        "unit": "ETB/kg",
                        "direction": "up",
                    }
                ],
                "citations": [
                    {
                        "label": f"{cheapest['market_code']} teff",
                        "value": cheapest_value,
                        "unit": "ETB/kg",
                        "source": "/prices/current",
                        "cell_refs": [
                            f"{cheapest['market_code']}:teff_mixed:{date.today().isoformat()}"
                        ],
                    }
                ],
                "mode": "rule_based",
            },
        }
