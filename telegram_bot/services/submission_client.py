from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any
from uuid import uuid4

import httpx

from telegram_bot.config import TelegramBotSettings
from telegram_bot.services.reputation import ContributorReputation, ReputationStore

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DraftSubmission:
    telegram_user_id: int
    telegram_username: str | None
    market_code: str
    commodity_code: str
    price: float
    unit: str
    consent_version: str
    market_label: str | None = None


class SubmissionClient:
    """Posts structured drafts to POST /api/v1/submissions."""

    def __init__(
        self,
        settings: TelegramBotSettings,
        reputation: ReputationStore,
    ) -> None:
        self._settings = settings
        self._reputation = reputation

    def reputation_for(self, telegram_user_id: int) -> ContributorReputation:
        return self._reputation.get(telegram_user_id)

    def is_banned(self, telegram_user_id: int) -> bool:
        return self._reputation.get(telegram_user_id).banned

    async def submit(self, draft: DraftSubmission) -> dict[str, Any]:
        profile = self._reputation.get(draft.telegram_user_id)
        if profile.banned:
            return {
                "status": "banned",
                "reputation": profile,
                "message": profile.ban_reason or "banned",
            }

        payload = {
            "client_submission_id": str(uuid4()),
            "input_mode": "telegram",
            "source": "user",
            "external_contributor_id": f"telegram:{draft.telegram_user_id}",
            "telegram_username": draft.telegram_username,
            "market_code": draft.market_code,
            "market_label": draft.market_label,
            "commodity_code": draft.commodity_code,
            "price": draft.price,
            "unit": draft.unit,
            "consent_version": draft.consent_version,
        }

        if self._settings.telegram_dry_run:
            logger.info("Dry-run submission: %s", payload)
            updated = self._reputation.record_pending_submission(draft.telegram_user_id)
            return {
                "status": "pending_review",
                "mode": "dry_run",
                "payload": payload,
                "reputation": updated,
                "points_note": (
                    "Pending review. You gained +1 for submitting. "
                    "If accepted later: +10 total path; if flagged: score drops."
                ),
            }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{self._settings.api_base_url.rstrip('/')}/submissions",
                json=payload,
            )
            if response.status_code == 403:
                profile.banned = True
                profile.ban_reason = "blocked by API"
                return {"status": "banned", "reputation": profile}
            if response.status_code == 400:
                detail = response.json().get("detail", "Invalid submission")
                return {
                    "status": "error",
                    "reputation": profile,
                    "message": str(detail),
                }
            response.raise_for_status()
            data = response.json()

        score = data.get("score") or {}
        updated = self._reputation.get(draft.telegram_user_id)
        updated.score = int(score.get("score", updated.score))
        updated.pending_count = int(score.get("pending_count", updated.pending_count))
        updated.accepted_count = int(
            score.get("accepted_count", updated.accepted_count)
        )
        updated.flagged_count = int(score.get("flagged_count", updated.flagged_count))
        updated.banned = bool(score.get("banned", False))
        updated.ban_reason = score.get("ban_reason")
        return {
            "status": "pending_review",
            "reputation": updated,
            "submission_id": data.get("id"),
            "points_note": "Score updated in Waga backend.",
        }

    @staticmethod
    def draft_summary(draft: DraftSubmission) -> str:
        return str(asdict(draft))
