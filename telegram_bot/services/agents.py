"""Approved market agents only — not open public submitters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentProfile:
    telegram_user_id: int
    display_name: str | None = None
    markets: tuple[str, ...] = ()
    active: bool = True
    onboarded_via: str = "allowlist"  # allowlist | invite


class AgentRegistry:
    """Who is allowed to submit for score / rewards."""

    def __init__(
        self,
        *,
        require_agent: bool = True,
        allowed_ids: set[int] | None = None,
        invite_codes: set[str] | None = None,
    ) -> None:
        self.require_agent = require_agent
        self._allowed_ids = set(allowed_ids or ())
        self._invite_codes = {
            code.strip().lower() for code in (invite_codes or set()) if code.strip()
        }
        self._activated: dict[int, AgentProfile] = {
            uid: AgentProfile(telegram_user_id=uid, onboarded_via="allowlist")
            for uid in self._allowed_ids
        }

    def is_agent(self, telegram_user_id: int) -> bool:
        if not self.require_agent:
            return True
        profile = self._activated.get(telegram_user_id)
        return profile is not None and profile.active

    def get(self, telegram_user_id: int) -> AgentProfile | None:
        return self._activated.get(telegram_user_id)

    def mark_approved(
        self,
        telegram_user_id: int,
        *,
        display_name: str | None = None,
        via: str = "admin_approve",
    ) -> None:
        """Mirror API-approved agent into the in-memory registry for this process."""
        self._activated[telegram_user_id] = AgentProfile(
            telegram_user_id=telegram_user_id,
            display_name=display_name,
            onboarded_via=via,
            active=True,
        )
        self._allowed_ids.add(telegram_user_id)

    def activate_with_invite(
        self,
        telegram_user_id: int,
        invite_code: str,
        *,
        display_name: str | None = None,
    ) -> tuple[bool, str]:
        code = invite_code.strip().lower()
        if not code:
            return False, "Send your invite code.\nExample: /agent WAGA-ADDIS-01"
        if code not in self._invite_codes:
            return False, (
                "That invite code is not valid.\n"
                "Contact the Waga team to join as a market agent."
            )
        if telegram_user_id in self._activated and self._activated[telegram_user_id].active:
            return True, (
                "You are already a Waga market agent.\n"
                "Use Submit price or /submit to report."
            )
        self._activated[telegram_user_id] = AgentProfile(
            telegram_user_id=telegram_user_id,
            display_name=display_name,
            onboarded_via="invite",
        )
        self._allowed_ids.add(telegram_user_id)
        return True, (
            "✅ You are now a Waga market agent.\n\n"
            "Next:\n"
            "1) Visit your assigned market\n"
            "2) Tap Submit price\n"
            "3) Earn score when reports are accepted\n"
            "4) Redeem score when you reach the threshold"
        )

    def denial_message(self) -> str:
        return (
            "To join as a market agent:\n"
            "1) Tap Apply to be agent\n"
            "2) Or tap Enter invite code if you already have one."
        )

    def join_prompt(self) -> str:
        return (
            "Enter your invite code.\n"
            "Send it as: /agent YOUR-CODE\n"
            "Example: /agent WAGA-ADDIS-01"
        )
