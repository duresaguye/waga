"""Rule-based NGO copilot and impact calculator."""

from __future__ import annotations

from datetime import UTC, datetime

from app.config import Settings
from app.services.affordability import AffordabilityService
from app.services.read_meta import build_meta


class CopilotService:
    def __init__(
        self,
        affordability: AffordabilityService,
        settings: Settings,
    ) -> None:
        self._affordability = affordability
        self._settings = settings

    async def ask(
        self,
        *,
        question: str,
        household_count: int | None = None,
        language: str = "en",
    ) -> dict:
        _ = (question, language)
        result = await self._affordability.get_affordability()
        data = result["data"]
        meta = result["meta"]
        coverage = meta.get("coverage", {})
        cells_published = coverage.get("cells_published", 0)
        cells_expected = coverage.get("cells_expected", 0)

        if data["status"] != "published" or data["cost_now"] is None:
            answer = (
                "Insufficient published city prices to compute the staple basket. "
                f"Missing commodities: {', '.join(data['missing_commodities']) or 'unknown'}."
            )
            return self._response(
                meta=meta,
                answer=answer,
                action="wait_for_coverage",
                band_low_pct=None,
                band_high_pct=None,
                confidence="low",
                confidence_reason="Basket not fully published",
                citations=[],
                impact=None,
                household_count=household_count,
            )

        change_pct = data["change_pct"] or 0.0
        top_item = max(
            data["items"],
            key=lambda item: item.get("contribution_to_change_pct") or 0.0,
        )
        contribution = top_item.get("contribution_to_change_pct") or 0.0
        band_low = max(0.0, round(change_pct * 0.85, 1))
        band_high = round(change_pct * 1.05, 1)
        purchasing_power = max(0.0, round(100.0 - change_pct, 1))

        answer = (
            f"The Addis staple basket rose from {data['cost_prior']:,.0f} to "
            f"{data['cost_now']:,.0f} ETB over the last {data['period_days']} days, "
            f"an increase of {change_pct:.1f}%. "
            f"{top_item['commodity_code'].replace('_', ' ').title()} accounts for "
            f"{contribution:.1f}% of that increase. "
            f"If your transfer value was set against the prior basket, it now covers "
            f"about {purchasing_power:.0f}% of the same goods. "
            f"An adjustment of {band_low:.0f}–{band_high:.0f}% would restore purchasing power."
        )

        gap = data["change_abs"] or 0.0
        impact = self._impact_block(household_count, gap, months=1)
        citations = [
            {
                "label": "Basket cost now",
                "value": data["cost_now"],
                "unit": "ETB",
                "source": "/affordability",
                "cell_refs": [
                    f"{self._settings.city_code}:{data['basket_code']}:{date_label()}"
                ],
            }
        ]
        confidence = "medium" if cells_expected and cells_published / cells_expected >= 0.7 else "low"
        confidence_reason = (
            f"{cells_published} of {cells_expected} cells published"
            if cells_expected
            else "Limited coverage data"
        )

        return self._response(
            meta=meta,
            answer=answer,
            action="increase_transfer_value",
            band_low_pct=band_low,
            band_high_pct=band_high,
            confidence=confidence,
            confidence_reason=confidence_reason,
            citations=citations,
            impact=impact,
            household_count=household_count,
        )

    async def impact(
        self,
        *,
        household_count: int,
        gap_per_household_etb: float,
        months: int = 1,
    ) -> dict:
        meta = build_meta(self._settings, latest_values=[])
        return {
            "meta": meta,
            "data": self._impact_block(household_count, gap_per_household_etb, months),
        }

    def _impact_block(
        self,
        household_count: int | None,
        gap_per_household_etb: float,
        months: int,
    ) -> dict | None:
        if household_count is None:
            return None
        monthly_total = round(household_count * gap_per_household_etb * months, 2)
        return {
            "household_count": household_count,
            "gap_per_household_etb": round(gap_per_household_etb, 2),
            "monthly_total_etb": monthly_total,
            "note": "Cost of leaving the transfer value unchanged for one month.",
        }

    def _response(
        self,
        *,
        meta: dict,
        answer: str,
        action: str,
        band_low_pct: float | None,
        band_high_pct: float | None,
        confidence: str,
        confidence_reason: str,
        citations: list[dict],
        impact: dict | None,
        household_count: int | None,
    ) -> dict:
        payload: dict = {
            "meta": meta,
            "data": {
                "answer": answer,
                "recommendation": {
                    "action": action,
                    "band_low_pct": band_low_pct,
                    "band_high_pct": band_high_pct,
                    "confidence": confidence,
                    "confidence_reason": confidence_reason,
                },
                "citations": citations,
                "mode": "rule_based",
            },
        }
        if impact is not None:
            payload["data"]["impact"] = impact
        elif household_count is not None:
            payload["data"]["impact"] = None
        return payload


def date_label() -> str:
    return datetime.now(UTC).date().isoformat()
