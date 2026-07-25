from __future__ import annotations

import secrets
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contributors import AgentInviteCode, AgentScoreEvent, Contributor
from app.models.enums import AgentScoreEventType, ContributorKind
from app.models.reward_settings import AgentRedeemRequest, AgentRewardSettings
from app.repositories.contributors import ContributorRepository
from app.repositories.reward_settings import RewardSettingsRepository
from app.services.agent_score_rules import (
    BAN_FLAG_LIMIT,
    BAN_SCORE_FLOOR,
    POINTS_ACCEPT,
    POINTS_FLAG,
    POINTS_PENDING,
    REDEEM_THRESHOLD,
    status_label,
)
from app.services.exceptions import (
    AgentBannedError,
    AgentInviteInvalidError,
    AgentNotFoundError,
    AgentRedeemNotReadyError,
    AgentScoreError,
)

# Avoid ambiguous characters (0/O, 1/I) so codes are easy to read aloud.
_INVITE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class AgentScoreService:
    def __init__(
        self,
        session: AsyncSession,
        contributors: ContributorRepository,
        rewards: RewardSettingsRepository,
    ) -> None:
        self._session = session
        self._contributors = contributors
        self._rewards = rewards

    async def get_reward_settings(self) -> AgentRewardSettings:
        settings = await self._rewards.get_active()
        if settings is None:
            # Safe fallback if migration/seed missing
            settings = AgentRewardSettings(
                id=uuid4(),
                birr_per_point=Decimal("2"),
                redeem_min_points=REDEEM_THRESHOLD,
                currency_code="ETB",
                is_active=True,
            )
            self._rewards.add_settings(settings)
            await self._session.commit()
            await self._session.refresh(settings)
        return settings

    async def update_reward_settings(
        self,
        *,
        birr_per_point: Decimal,
        redeem_min_points: int,
        currency_code: str = "ETB",
    ) -> AgentRewardSettings:
        current = await self._rewards.get_active()
        if current is not None:
            current.is_active = False
        settings = AgentRewardSettings(
            id=uuid4(),
            birr_per_point=birr_per_point,
            redeem_min_points=redeem_min_points,
            currency_code=currency_code.upper(),
            is_active=True,
        )
        self._rewards.add_settings(settings)
        await self._session.commit()
        await self._session.refresh(settings)
        return settings

    @staticmethod
    def generate_invite_code() -> str:
        """Hard-to-guess code, e.g. WAGA-K7M2-9XQR-4HNP."""
        chunks = [
            "".join(secrets.choice(_INVITE_ALPHABET) for _ in range(4))
            for _ in range(3)
        ]
        return "WAGA-" + "-".join(chunks)

    async def create_invite(
        self,
        *,
        max_uses: int = 1,
        label_note: str | None = None,
    ) -> AgentInviteCode:
        """Create a random invite code. Default: single-use (others cannot reuse)."""
        if max_uses < 0:
            raise AgentScoreError("max_uses must be >= 0 (0 = unlimited)")

        for _ in range(8):
            code = self.generate_invite_code()
            existing = await self._contributors.get_invite_by_code(code)
            if existing is not None:
                continue
            invite = AgentInviteCode(
                id=uuid4(),
                code=code,
                is_active=True,
                max_uses=max_uses,
                uses_count=0,
            )
            self._contributors.add_invite(invite)
            try:
                await self._session.commit()
            except IntegrityError:
                await self._session.rollback()
                continue
            await self._session.refresh(invite)
            _ = label_note
            return invite

        raise AgentScoreError("Could not generate a unique invite code")

    async def list_invites(self, *, limit: int = 50) -> list[AgentInviteCode]:
        return await self._contributors.list_invites(limit=limit)

    async def deactivate_invite(self, invite_id: UUID) -> AgentInviteCode:
        invite = await self._contributors.get_invite_by_id(invite_id)
        if invite is None:
            raise AgentInviteInvalidError("Invite code not found")
        invite.is_active = False
        await self._session.commit()
        await self._session.refresh(invite)
        return invite

    async def activate_with_invite(
        self,
        *,
        telegram_id: str,
        invite_code: str,
        display_name: str | None = None,
    ) -> Contributor:
        telegram_id = telegram_id.strip()
        if not telegram_id:
            raise AgentScoreError("telegram_id is required")

        invite = await self._contributors.get_invite_by_code(invite_code)
        if invite is None or not invite.is_active:
            raise AgentInviteInvalidError("Invalid invite code")
        if invite.max_uses > 0 and invite.uses_count >= invite.max_uses:
            raise AgentInviteInvalidError("Invite code has no remaining uses")

        contributor = await self._contributors.get_by_telegram_id(telegram_id)
        if contributor is None:
            contributor = Contributor(
                id=uuid4(),
                user_id=None,
                external_id=uuid4(),
                kind=ContributorKind.AGENT,
                telegram_id=telegram_id,
                is_agent=True,
                reputation_score=0,
                pending_count=0,
                accepted_count=0,
                flagged_count=0,
                redeemed_total=0,
                banned=False,
                ban_reason=None,
            )
            self._contributors.add(contributor)
        else:
            contributor.is_agent = True
            contributor.kind = ContributorKind.AGENT
            if contributor.reputation_score is None:
                contributor.reputation_score = 0
            if contributor.pending_count is None:
                contributor.pending_count = 0
            if contributor.accepted_count is None:
                contributor.accepted_count = 0
            if contributor.flagged_count is None:
                contributor.flagged_count = 0
            if contributor.redeemed_total is None:
                contributor.redeemed_total = 0
            if contributor.banned is None:
                contributor.banned = False

        if contributor.banned:
            raise AgentBannedError(contributor.ban_reason or "Agent is banned")

        invite.uses_count += 1
        self._record_event(
            contributor,
            event_type=AgentScoreEventType.ACTIVATE,
            points_delta=0,
            note=f"invite:{invite.code}"
            + (f" name:{display_name}" if display_name else ""),
        )

        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise AgentScoreError("Could not activate agent") from error

        await self._session.refresh(contributor)
        return contributor

    async def get_by_telegram_id(self, telegram_id: str) -> Contributor:
        contributor = await self._contributors.get_by_telegram_id(telegram_id.strip())
        if contributor is None or not contributor.is_agent:
            raise AgentNotFoundError("Agent not found")
        return contributor

    async def ensure_agent(self, telegram_id: str) -> Contributor:
        return await self.get_by_telegram_id(telegram_id)

    async def record_pending_submit(
        self, telegram_id: str, *, commit: bool = True
    ) -> Contributor:
        contributor = await self.ensure_agent(telegram_id)
        if contributor.banned:
            raise AgentBannedError(contributor.ban_reason or "Agent is banned")

        contributor.pending_count += 1
        contributor.reputation_score += POINTS_PENDING
        self._record_event(
            contributor,
            event_type=AgentScoreEventType.PENDING_SUBMIT,
            points_delta=POINTS_PENDING,
            note="submission pending review",
        )
        if commit:
            await self._session.commit()
            await self._session.refresh(contributor)
        return contributor

    async def apply_review(
        self, telegram_id: str, *, accepted: bool, commit: bool = True
    ) -> Contributor:
        contributor = await self.ensure_agent(telegram_id)
        if accepted:
            contributor.accepted_count += 1
            delta = POINTS_ACCEPT - POINTS_PENDING
            contributor.reputation_score += delta
            if contributor.pending_count > 0:
                contributor.pending_count -= 1
            self._record_event(
                contributor,
                event_type=AgentScoreEventType.ACCEPTED,
                points_delta=delta,
                note="submission accepted",
            )
        else:
            contributor.flagged_count += 1
            contributor.reputation_score += POINTS_FLAG
            if contributor.pending_count > 0:
                contributor.pending_count -= 1
            self._record_event(
                contributor,
                event_type=AgentScoreEventType.FLAGGED,
                points_delta=POINTS_FLAG,
                note="submission flagged",
            )
            self._refresh_ban(contributor)

        if commit:
            await self._session.commit()
            await self._session.refresh(contributor)
        return contributor

    async def redeem(
        self, telegram_id: str
    ) -> tuple[Contributor, int, Decimal, AgentRedeemRequest]:
        contributor = await self.ensure_agent(telegram_id)
        if contributor.banned:
            raise AgentBannedError(contributor.ban_reason or "Agent is banned")

        settings = await self.get_reward_settings()
        min_points = int(settings.redeem_min_points)
        if contributor.reputation_score < min_points:
            raise AgentRedeemNotReadyError(
                f"Need {min_points} points to redeem "
                f"(current: {contributor.reputation_score})"
            )

        points = contributor.reputation_score
        birr_per_point = Decimal(str(settings.birr_per_point))
        birr_amount = (birr_per_point * points).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        contributor.redeemed_total += points
        contributor.reputation_score = 0
        request = AgentRedeemRequest(
            id=uuid4(),
            contributor_id=contributor.id,
            telegram_id=contributor.telegram_id,
            points_redeemed=points,
            birr_per_point=birr_per_point,
            birr_amount=birr_amount,
            currency_code=settings.currency_code,
            status="pending",
        )
        self._rewards.add_redeem_request(request)
        self._record_event(
            contributor,
            event_type=AgentScoreEventType.REDEEM,
            points_delta=-points,
            note=f"redeem {points} pts → {birr_amount} {settings.currency_code}",
        )
        await self._session.commit()
        await self._session.refresh(contributor)
        await self._session.refresh(request)
        return contributor, points, birr_amount, request

    async def to_score_dict(self, contributor: Contributor) -> dict[str, object]:
        settings = await self.get_reward_settings()
        birr_per_point = Decimal(str(settings.birr_per_point))
        estimated = (birr_per_point * contributor.reputation_score).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        min_points = int(settings.redeem_min_points)
        return {
            "telegram_id": contributor.telegram_id or "",
            "is_agent": contributor.is_agent,
            "score": contributor.reputation_score,
            "status": status_label(
                banned=contributor.banned,
                score=contributor.reputation_score,
            ),
            "pending_count": contributor.pending_count,
            "accepted_count": contributor.accepted_count,
            "flagged_count": contributor.flagged_count,
            "redeemed_total": contributor.redeemed_total,
            "banned": contributor.banned,
            "ban_reason": contributor.ban_reason,
            "can_redeem": (
                not contributor.banned and contributor.reputation_score >= min_points
            ),
            "redeem_threshold": min_points,
            "birr_per_point": birr_per_point,
            "estimated_birr": estimated,
            "currency_code": settings.currency_code,
        }

    def settings_example(self, settings: AgentRewardSettings) -> str:
        pts = int(settings.redeem_min_points)
        birr = (Decimal(str(settings.birr_per_point)) * pts).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return (
            f"{pts} points × {settings.birr_per_point} "
            f"= {birr} {settings.currency_code}"
        )

    def _refresh_ban(self, contributor: Contributor) -> None:
        if contributor.flagged_count >= BAN_FLAG_LIMIT:
            contributor.banned = True
            contributor.ban_reason = f"{BAN_FLAG_LIMIT}+ flagged submissions"
            self._record_event(
                contributor,
                event_type=AgentScoreEventType.BAN,
                points_delta=0,
                note=contributor.ban_reason,
            )
            return
        _ = BAN_SCORE_FLOOR

    def _record_event(
        self,
        contributor: Contributor,
        *,
        event_type: AgentScoreEventType,
        points_delta: int,
        note: str | None,
    ) -> None:
        self._contributors.add_score_event(
            AgentScoreEvent(
                id=uuid4(),
                contributor_id=contributor.id,
                event_type=event_type,
                points_delta=points_delta,
                score_after=contributor.reputation_score,
                note=note,
            )
        )
