"""NGO copilot: rule-based numbers + optional Addis AI narrative (facts only)."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from app.config import Settings
from app.services.addis_chat import AddisChatClient, AddisChatError
from app.services.affordability import AffordabilityService
from app.services.read_meta import build_meta

logger = logging.getLogger(__name__)

COPILOT_SYSTEM = (
    "You are Waga's cash-assistance copilot for Addis Ababa. "
    "Use ONLY the JSON facts provided. Never invent prices, markets, or percentages. "
    "Do not fill insufficient_data gaps. "
    "Write 3-5 short sentences for NGO programme staff. "
    "Mention the recommended transfer uplift band exactly as given. "
    "If language is Amharic, write in Amharic; otherwise English."
)


class CopilotService:
    def __init__(
        self,
        affordability: AffordabilityService,
        settings: Settings,
        chat: AddisChatClient | None = None,
    ) -> None:
        self._affordability = affordability
        self._settings = settings
        self._chat = chat if chat is not None else AddisChatClient(settings)

    async def ask(
        self,
        *,
        question: str,
        household_count: int | None = None,
        language: str = "en",
    ) -> dict:
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
                mode="rule_based",
                model=None,
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

        rule_answer = (
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
            },
            {
                "label": "Basket change",
                "value": change_pct,
                "unit": "%",
                "source": "/affordability",
                "cell_refs": [
                    f"{self._settings.city_code}:{data['basket_code']}:change_pct"
                ],
            },
        ]
        confidence = (
            "medium"
            if cells_expected and cells_published / cells_expected >= 0.7
            else "low"
        )
        confidence_reason = (
            f"{cells_published} of {cells_expected} cells published"
            if cells_expected
            else "Limited coverage data"
        )

        facts = {
            "question": question,
            "language": language,
            "basket": {
                "cost_now_etb": data["cost_now"],
                "cost_prior_etb": data["cost_prior"],
                "change_pct": change_pct,
                "change_abs_etb": data["change_abs"],
                "band": data.get("band"),
                "period_days": data["period_days"],
                "top_driver": top_item["commodity_code"],
                "top_driver_contribution_pct": contribution,
                "purchasing_power_pct": purchasing_power,
            },
            "recommendation": {
                "action": "increase_transfer_value",
                "band_low_pct": band_low,
                "band_high_pct": band_high,
            },
            "coverage": {
                "cells_published": cells_published,
                "cells_expected": cells_expected,
            },
            "household_count": household_count,
            "impact": impact,
            "rule_answer": rule_answer,
        }

        answer, mode, model = await self._narrate(facts=facts, language=language, fallback=rule_answer)

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
            mode=mode,
            model=model,
        )

    async def _narrate(
        self,
        *,
        facts: dict,
        language: str,
        fallback: str,
    ) -> tuple[str, str, str | None]:
        if not self._chat.enabled:
            return fallback, "rule_based", None
        lang = "am" if language.lower().startswith("am") else "en"
        try:
            chat = await self._chat.generate(
                prompt=(
                    "Rewrite the cash-assistance guidance using only these facts. "
                    "Keep every number exactly as given.\n\n"
                    f"{json.dumps(facts, ensure_ascii=False)}"
                ),
                system=COPILOT_SYSTEM,
                target_language=lang,
                temperature=0.25,
                max_output_tokens=350,
                persona="Waga NGO cash-assistance copilot",
            )
            return chat.text, "addis_ai", chat.model
        except AddisChatError:
            logger.exception("Addis copilot narrative failed; using rule answer")
            return fallback, "rule_based", None

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
        mode: str,
        model: str | None,
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
                "mode": mode,
                "model": model,
            },
        }
        if impact is not None:
            payload["data"]["impact"] = impact
        elif household_count is not None:
            payload["data"]["impact"] = None
        return payload


def date_label() -> str:
    return datetime.now(UTC).date().isoformat()
