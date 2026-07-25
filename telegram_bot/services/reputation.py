"""Local reputation store for dry-run when API score is unavailable."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.agent_score_rules import (
    BAN_FLAG_LIMIT,
    BAN_SCORE_FLOOR,
    POINTS_ACCEPT,
    POINTS_FLAG,
    POINTS_PENDING,
    REDEEM_THRESHOLD,
    status_label,
)


@dataclass
class ContributorReputation:
    telegram_user_id: int
    score: int = 0
    pending_count: int = 0
    accepted_count: int = 0
    flagged_count: int = 0
    redeemed_total: int = 0
    banned: bool = False
    ban_reason: str | None = None

    def status_label(self) -> str:
        return status_label(banned=self.banned, score=self.score)

    def can_redeem(self) -> bool:
        return not self.banned and self.score >= REDEEM_THRESHOLD


class ReputationStore:
    """In-memory store for the bot process (dry-run friendly)."""

    def __init__(self) -> None:
        self._by_user: dict[int, ContributorReputation] = {}

    def get(self, telegram_user_id: int) -> ContributorReputation:
        if telegram_user_id not in self._by_user:
            self._by_user[telegram_user_id] = ContributorReputation(
                telegram_user_id=telegram_user_id
            )
        return self._by_user[telegram_user_id]

    def record_pending_submission(self, telegram_user_id: int) -> ContributorReputation:
        profile = self.get(telegram_user_id)
        if profile.banned:
            return profile
        profile.pending_count += 1
        profile.score += POINTS_PENDING
        return profile

    def apply_review(
        self, telegram_user_id: int, *, accepted: bool
    ) -> ContributorReputation:
        profile = self.get(telegram_user_id)
        if accepted:
            profile.accepted_count += 1
            profile.score += POINTS_ACCEPT - POINTS_PENDING
            if profile.pending_count > 0:
                profile.pending_count -= 1
        else:
            profile.flagged_count += 1
            profile.score += POINTS_FLAG
            if profile.pending_count > 0:
                profile.pending_count -= 1
        self._refresh_ban(profile)
        return profile

    def redeem(self, telegram_user_id: int) -> tuple[bool, str, ContributorReputation]:
        profile = self.get(telegram_user_id)
        if profile.banned:
            return False, "Banned agents cannot redeem score.", profile
        if profile.score < REDEEM_THRESHOLD:
            need = REDEEM_THRESHOLD - profile.score
            return (
                False,
                (
                    f"Not enough score to redeem yet.\n"
                    f"Score: {profile.score}\n"
                    f"Need {need} more points (minimum {REDEEM_THRESHOLD}).\n"
                    "Keep submitting accurate market reports."
                ),
                profile,
            )
        amount = profile.score
        profile.redeemed_total += amount
        profile.score = 0
        return (
            True,
            (
                f"✅ Redeem request recorded for {amount} points.\n"
                f"Lifetime redeemed: {profile.redeemed_total}\n"
                "The Waga team will process your reward "
                "(airtime / mobile money) after verification.\n"
                "Keep reporting to build score again."
            ),
            profile,
        )

    def _refresh_ban(self, profile: ContributorReputation) -> None:
        # Match backend: ban after repeated flags, not first mistake.
        if profile.flagged_count >= BAN_FLAG_LIMIT:
            profile.banned = True
            profile.ban_reason = f"{BAN_FLAG_LIMIT}+ flagged submissions"
        _ = BAN_SCORE_FLOOR

    def format_card(self, profile: ContributorReputation) -> str:
        redeem_line = (
            "Ready to redeem (tap Redeem score or /redeem)"
            if profile.can_redeem()
            else f"Redeem from {REDEEM_THRESHOLD} points"
        )
        lines = [
            "📊 Agent score",
            f"• Score: {profile.score}",
            f"• Status: {profile.status_label()}",
            f"• Pending review: {profile.pending_count}",
            f"• Accepted reports: {profile.accepted_count}",
            f"• Flagged: {profile.flagged_count}",
            f"• Redeemed so far: {profile.redeemed_total}",
            f"• {redeem_line}",
            "",
            "How score works:",
            f"• Accepted report: +{POINTS_ACCEPT}",
            f"• Flagged report: {POINTS_FLAG}",
            f"• Redeem at {REDEEM_THRESHOLD}+ points",
            "• False reports can lead to a ban",
        ]
        if profile.banned:
            lines.extend(
                [
                    "",
                    f"🚫 Banned: {profile.ban_reason or 'policy violation'}",
                    "You cannot submit or redeem.",
                ]
            )
        return "\n".join(lines)
