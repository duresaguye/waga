"""One-click monthly NGO brief from published index facts (+ optional Addis narrative)."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from app.config import Settings
from app.services.addis_chat import AddisChatClient, AddisChatError
from app.services.affordability import AffordabilityService
from app.services.alerts import AlertsService
from app.services.copilot import CopilotService

logger = logging.getLogger(__name__)

BRIEF_SYSTEM = (
    "You write a short executive summary for an NGO cash programme in Addis Ababa. "
    "Use ONLY the JSON facts. Never invent prices. "
    "2-4 sentences. Mention basket change %, severity band, and transfer uplift band if present. "
    "Note coverage gaps if insufficient cells are high."
)


class BriefService:
    def __init__(
        self,
        affordability: AffordabilityService,
        alerts: AlertsService,
        copilot: CopilotService,
        settings: Settings,
        chat: AddisChatClient | None = None,
    ) -> None:
        self._affordability = affordability
        self._alerts = alerts
        self._copilot = copilot
        self._settings = settings
        self._chat = chat if chat is not None else AddisChatClient(settings)

    async def monthly(
        self,
        *,
        household_count: int = 50000,
        language: str = "en",
    ) -> dict:
        afford = await self._affordability.get_affordability()
        alerts = await self._alerts.get_alerts(min_band="stress")
        copilot = await self._copilot.ask(
            question="How should we adjust cash assistance for Addis this month?",
            household_count=household_count,
            language=language,
        )

        afford_data = afford["data"]
        afford_meta = afford["meta"]
        coverage = afford_meta.get("coverage") or {}
        alert_rows = alerts.get("data", {}).get("alerts") or []
        copilot_data = copilot.get("data") or {}

        generated_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        title = f"Waga monthly cash-assistance brief — {generated_at[:10]}"

        template_summary = _template_summary(afford_data, coverage, copilot_data, alert_rows)
        summary, mode, model = await self._executive_summary(
            language=language,
            facts={
                "affordability": afford_data,
                "coverage": coverage,
                "copilot": {
                    "answer": copilot_data.get("answer"),
                    "recommendation": copilot_data.get("recommendation"),
                    "impact": copilot_data.get("impact"),
                    "mode": copilot_data.get("mode"),
                },
                "alerts_count": len(alert_rows),
                "top_alerts": alert_rows[:5],
                "template_summary": template_summary,
            },
            fallback=template_summary,
        )

        markdown = _render_markdown(
            title=title,
            generated_at=generated_at,
            summary=summary,
            afford_data=afford_data,
            coverage=coverage,
            copilot_data=copilot_data,
            alert_rows=alert_rows,
            mode=mode,
            model=model,
            household_count=household_count,
        )

        return {
            "meta": afford_meta,
            "data": {
                "title": title,
                "generated_at": generated_at,
                "language": language,
                "executive_summary": summary,
                "markdown": markdown,
                "mode": mode,
                "model": model,
                "household_count": household_count,
                "citations": copilot_data.get("citations") or [],
            },
        }

    async def _executive_summary(
        self,
        *,
        language: str,
        facts: dict,
        fallback: str,
    ) -> tuple[str, str, str | None]:
        if not self._chat.enabled:
            return fallback, "template", None
        lang = "am" if language.lower().startswith("am") else "en"
        try:
            chat = await self._chat.generate(
                prompt=(
                    "Write the executive summary from these facts only:\n\n"
                    f"{json.dumps(facts, ensure_ascii=False, default=str)}"
                ),
                system=BRIEF_SYSTEM,
                target_language=lang,
                temperature=0.3,
                max_output_tokens=280,
                persona="Waga NGO briefing writer",
            )
            return chat.text, "addis_ai", chat.model
        except AddisChatError:
            logger.exception("Addis brief summary failed; using template")
            return fallback, "template", None


def _template_summary(
    afford_data: dict,
    coverage: dict,
    copilot_data: dict,
    alert_rows: list,
) -> str:
    if afford_data.get("status") != "published" or afford_data.get("cost_now") is None:
        missing = ", ".join(afford_data.get("missing_commodities") or []) or "unknown"
        return (
            f"Basket not fully published. Missing commodities: {missing}. "
            "No transfer adjustment should be inferred until coverage improves."
        )

    rec = copilot_data.get("recommendation") or {}
    band_low = rec.get("band_low_pct")
    band_high = rec.get("band_high_pct")
    uplift = (
        f" Suggested transfer uplift: {band_low}–{band_high}%."
        if band_low is not None and band_high is not None
        else ""
    )
    pub = coverage.get("cells_published")
    exp = coverage.get("cells_expected")
    cov = (
        f" Coverage: {pub} of {exp} cells published."
        if pub is not None and exp is not None
        else ""
    )
    return (
        f"The Addis staple basket is {afford_data['cost_now']:,.0f} ETB "
        f"({afford_data.get('change_pct')}% vs prior; band {afford_data.get('band')})."
        f"{uplift}{cov} Active stress-or-above alerts: {len(alert_rows)}."
    )


def _render_markdown(
    *,
    title: str,
    generated_at: str,
    summary: str,
    afford_data: dict,
    coverage: dict,
    copilot_data: dict,
    alert_rows: list,
    mode: str,
    model: str | None,
    household_count: int,
) -> str:
    lines = [
        f"# {title}",
        "",
        f"_Generated {generated_at} · narrative mode: {mode}"
        + (f" · model: {model}" if model else "")
        + "_",
        "",
        "## Executive summary",
        "",
        summary,
        "",
        "## Staple basket",
        "",
    ]

    if afford_data.get("status") == "published" and afford_data.get("cost_now") is not None:
        lines.extend(
            [
                f"- Cost now: **{afford_data['cost_now']:,.0f} ETB**",
                f"- Prior: {afford_data.get('cost_prior')} ETB",
                f"- Change: {afford_data.get('change_pct')}% ({afford_data.get('change_abs')} ETB)",
                f"- Severity band: **{afford_data.get('band')}**",
                "",
                "### Drivers",
                "",
            ]
        )
        items = sorted(
            afford_data.get("items") or [],
            key=lambda i: abs(i.get("contribution_to_change_pct") or 0),
            reverse=True,
        )
        for item in items:
            if item.get("status") != "published":
                continue
            lines.append(
                f"- {item.get('commodity_code')}: "
                f"{item.get('change_pct')}% MoM · "
                f"contribution {item.get('contribution_to_change_pct')} pp"
            )
    else:
        lines.append(
            f"- Status: `{afford_data.get('status')}` · "
            f"missing: {', '.join(afford_data.get('missing_commodities') or [])}"
        )

    lines.extend(
        [
            "",
            "## Coverage",
            "",
            f"- Published: {coverage.get('cells_published')} / {coverage.get('cells_expected')}",
            f"- Insufficient: {coverage.get('cells_insufficient')}",
            f"- Coverage %: {coverage.get('coverage_pct')}",
            "",
            "## Cash assistance signal",
            "",
            copilot_data.get("answer") or "_No copilot answer._",
            "",
        ]
    )

    rec = copilot_data.get("recommendation") or {}
    if rec.get("band_low_pct") is not None:
        lines.extend(
            [
                f"- Recommended uplift: **{rec.get('band_low_pct')}–{rec.get('band_high_pct')}%**",
                f"- Confidence: {rec.get('confidence')} ({rec.get('confidence_reason')})",
                "",
            ]
        )

    impact = copilot_data.get("impact")
    if impact:
        lines.extend(
            [
                "## Cost of doing nothing",
                "",
                f"- Households: {impact.get('household_count') or household_count}",
                f"- Gap / household: {impact.get('gap_per_household_etb')} ETB",
                f"- Monthly total: **{impact.get('monthly_total_etb')} ETB**",
                "",
            ]
        )

    lines.extend(["## Alerts", ""])
    if not alert_rows:
        lines.append("_No stress-or-above spike alerts in the current window._")
    else:
        for alert in alert_rows[:10]:
            lines.append(
                f"- `{alert.get('band')}` · {alert.get('commodity_code')} @ "
                f"{alert.get('market_code')}: {alert.get('pct_above_expected')}% vs trend"
            )

    lines.extend(
        [
            "",
            "## Methodology",
            "",
            "- Index: weighted median of accepted submissions, 72h window, ≥3 accepts to publish.",
            "- No imputation: `insufficient_data` cells stay null in exports.",
            "- AI narrative (when enabled) may only restate published facts; it never invents prices.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"
