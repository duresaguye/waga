"""Rule + Addis LLM triage for pending price submissions."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass
from decimal import Decimal
from statistics import median
from typing import Any, Literal

from app.services.addis_chat import AddisChatClient, AddisChatError

logger = logging.getLogger(__name__)

AiVerdict = Literal["accept", "hold", "flag"]
AiConfidence = Literal["high", "medium", "low"]

# Soft sanity bands for Phase-1 staples (ETB per canonical unit).
PRICE_BANDS: dict[str, tuple[Decimal, Decimal]] = {
    "teff_mixed": (Decimal("40"), Decimal("300")),
    "teff_white": (Decimal("40"), Decimal("350")),
    "wheat": (Decimal("20"), Decimal("200")),
    "maize": (Decimal("15"), Decimal("150")),
    "onion": (Decimal("10"), Decimal("200")),
    "tomato": (Decimal("10"), Decimal("200")),
    "potato": (Decimal("5"), Decimal("120")),
    "cooking_oil": (Decimal("80"), Decimal("800")),
}
DEFAULT_BAND = (Decimal("1"), Decimal("5000"))

SYSTEM_PROMPT = (
    "You are Waga's price review assistant for Ethiopian market reports. "
    "Use ONLY the facts in the user message. Do not invent prices. "
    "Reply with a single JSON object and nothing else, using English keys: "
    '{"verdict":"accept|hold|flag","confidence":"high|medium|low",'
    '"reason":"one short sentence"}.'
)


@dataclass(frozen=True)
class TriageFacts:
    market_code: str
    commodity_code: str
    price: Decimal
    unit: str
    agent_score: int
    agent_accepted_count: int
    agent_flagged_count: int
    same_market_accepted_prices: tuple[Decimal, ...]
    same_agent_recent_prices: tuple[Decimal, ...]
    market_median: Decimal | None
    agent_median: Decimal | None
    pct_vs_market_median: float | None
    pct_vs_agent_median: float | None
    in_sanity_band: bool


@dataclass(frozen=True)
class TriageResult:
    verdict: AiVerdict
    confidence: AiConfidence
    reason: str
    model: str
    facts: TriageFacts


class ReviewTriageService:
    def __init__(self, chat: AddisChatClient | None = None) -> None:
        self._chat = chat

    def build_facts(
        self,
        *,
        market_code: str,
        commodity_code: str,
        price: Decimal,
        unit: str,
        agent_score: int,
        agent_accepted_count: int,
        agent_flagged_count: int,
        same_market_accepted_prices: list[Decimal],
        same_agent_recent_prices: list[Decimal],
    ) -> TriageFacts:
        market_prices = tuple(same_market_accepted_prices)
        agent_prices = tuple(same_agent_recent_prices)
        market_med = _safe_median(market_prices)
        agent_med = _safe_median(agent_prices)
        low, high = PRICE_BANDS.get(commodity_code, DEFAULT_BAND)
        return TriageFacts(
            market_code=market_code,
            commodity_code=commodity_code,
            price=price,
            unit=unit,
            agent_score=agent_score,
            agent_accepted_count=agent_accepted_count,
            agent_flagged_count=agent_flagged_count,
            same_market_accepted_prices=market_prices,
            same_agent_recent_prices=agent_prices,
            market_median=market_med,
            agent_median=agent_med,
            pct_vs_market_median=_pct_diff(price, market_med),
            pct_vs_agent_median=_pct_diff(price, agent_med),
            in_sanity_band=low <= price <= high,
        )

    def rules_triage(self, facts: TriageFacts) -> TriageResult:
        if not facts.in_sanity_band:
            return TriageResult(
                verdict="flag",
                confidence="high",
                reason="Price outside expected range for this commodity.",
                model="rules-v1",
                facts=facts,
            )

        market_pct = facts.pct_vs_market_median
        agent_pct = facts.pct_vs_agent_median

        if market_pct is not None and abs(market_pct) >= 60:
            return TriageResult(
                verdict="flag",
                confidence="high",
                reason=(
                    f"Far from same-market median "
                    f"({facts.market_median} ETB/{facts.unit})."
                ),
                model="rules-v1",
                facts=facts,
            )

        if agent_pct is not None and abs(agent_pct) >= 70:
            return TriageResult(
                verdict="hold",
                confidence="medium",
                reason=(
                    "Large jump vs this agent's recent prices "
                    f"for {facts.commodity_code}."
                ),
                model="rules-v1",
                facts=facts,
            )

        if market_pct is not None and abs(market_pct) >= 25:
            return TriageResult(
                verdict="hold",
                confidence="medium",
                reason=(
                    f"Somewhat away from same-market median "
                    f"({facts.market_median} ETB/{facts.unit})."
                ),
                model="rules-v1",
                facts=facts,
            )

        if facts.agent_flagged_count >= 2 and facts.agent_accepted_count < 3:
            return TriageResult(
                verdict="hold",
                confidence="medium",
                reason="Agent has recent flags; keep for human review.",
                model="rules-v1",
                facts=facts,
            )

        if market_pct is None and agent_pct is None:
            return TriageResult(
                verdict="hold",
                confidence="low",
                reason="No local comparison history yet; needs human review.",
                model="rules-v1",
                facts=facts,
            )

        return TriageResult(
            verdict="accept",
            confidence="high" if market_pct is not None else "medium",
            reason="Consistent with same-market and/or this agent's recent prices.",
            model="rules-v1",
            facts=facts,
        )

    async def triage(self, facts: TriageFacts) -> TriageResult:
        rules = self.rules_triage(facts)
        if self._chat is None or not self._chat.enabled:
            return rules

        try:
            chat = await self._chat.generate(
                prompt=_facts_prompt(facts, rules),
                system=SYSTEM_PROMPT,
                temperature=0.2,
                max_output_tokens=250,
            )
            parsed = _parse_llm_json(chat.text)
            if parsed is None:
                logger.warning("Could not parse Addis review JSON; using rules")
                return rules
            verdict, confidence, reason = parsed
            return TriageResult(
                verdict=verdict,
                confidence=confidence,
                reason=reason,
                model=chat.model,
                facts=facts,
            )
        except AddisChatError:
            logger.exception("Addis review assist failed; using rules")
            return rules


def _safe_median(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return Decimal(str(median(values)))


def _pct_diff(price: Decimal, baseline: Decimal | None) -> float | None:
    if baseline is None or baseline <= 0:
        return None
    return float((price - baseline) / baseline * Decimal("100"))


def _facts_prompt(facts: TriageFacts, rules: TriageResult) -> str:
    payload: dict[str, Any] = {
        "submission": {
            "market_code": facts.market_code,
            "commodity_code": facts.commodity_code,
            "price": str(facts.price),
            "unit": facts.unit,
        },
        "agent": {
            "score": facts.agent_score,
            "accepted_count": facts.agent_accepted_count,
            "flagged_count": facts.agent_flagged_count,
        },
        "comparisons": {
            "same_market_accepted_prices": [str(p) for p in facts.same_market_accepted_prices],
            "same_agent_recent_prices": [str(p) for p in facts.same_agent_recent_prices],
            "market_median": None if facts.market_median is None else str(facts.market_median),
            "agent_median": None if facts.agent_median is None else str(facts.agent_median),
            "pct_vs_market_median": facts.pct_vs_market_median,
            "pct_vs_agent_median": facts.pct_vs_agent_median,
            "in_sanity_band": facts.in_sanity_band,
        },
        "rules_suggestion": {
            "verdict": rules.verdict,
            "confidence": rules.confidence,
            "reason": rules.reason,
        },
    }
    return (
        "Review this market price report and return JSON only.\n"
        f"{json.dumps(payload, ensure_ascii=True)}"
    )


def _parse_llm_json(text: str) -> tuple[AiVerdict, AiConfidence, str] | None:
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL)
    if fence:
        cleaned = fence.group(1)
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            cleaned = cleaned[start : end + 1]
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None

    verdict = str(data.get("verdict", "")).strip().lower()
    confidence = str(data.get("confidence", "")).strip().lower()
    reason = str(data.get("reason", "")).strip()
    if verdict not in {"accept", "hold", "flag"}:
        return None
    if confidence not in {"high", "medium", "low"}:
        confidence = "medium"
    if not reason:
        reason = "AI review completed."
    return verdict, confidence, reason[:500]  # type: ignore[return-value]


def facts_as_dict(facts: TriageFacts) -> dict[str, Any]:
    raw = asdict(facts)
    raw["price"] = str(facts.price)
    raw["market_median"] = (
        None if facts.market_median is None else str(facts.market_median)
    )
    raw["agent_median"] = (
        None if facts.agent_median is None else str(facts.agent_median)
    )
    raw["same_market_accepted_prices"] = [
        str(p) for p in facts.same_market_accepted_prices
    ]
    raw["same_agent_recent_prices"] = [str(p) for p in facts.same_agent_recent_prices]
    return raw
