from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.contributors import AgentInviteCode, AgentScoreEvent, Contributor
from app.models.enums import ContributorKind
from app.models.reward_settings import AgentRedeemRequest, AgentRewardSettings
from app.services.agent_score import AgentScoreService
from app.services.agent_score_rules import POINTS_ACCEPT, REDEEM_THRESHOLD
from app.services.exceptions import (
    AgentBannedError,
    AgentInviteInvalidError,
    AgentRedeemNotReadyError,
)


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, obj: object) -> None:
        _ = obj


class FakeContributorRepository:
    def __init__(self) -> None:
        self.contributors: dict[str, Contributor] = {}
        self.invites: dict[str, AgentInviteCode] = {
            "waga-addis-01": AgentInviteCode(
                id=uuid4(),
                code="waga-addis-01",
                is_active=True,
                max_uses=0,
                uses_count=0,
            )
        }
        self.events: list[AgentScoreEvent] = []

    def add(self, contributor: Contributor) -> None:
        assert contributor.telegram_id is not None
        self.contributors[contributor.telegram_id] = contributor

    def add_score_event(self, event: AgentScoreEvent) -> None:
        self.events.append(event)

    async def get_by_telegram_id(self, telegram_id: str) -> Contributor | None:
        return self.contributors.get(telegram_id)

    async def get_invite_by_code(self, code: str) -> AgentInviteCode | None:
        return self.invites.get(code.strip().lower())


class FakeRewardSettingsRepository:
    def __init__(self) -> None:
        self.settings = AgentRewardSettings(
            id=uuid4(),
            birr_per_point=Decimal("2"),
            redeem_min_points=REDEEM_THRESHOLD,
            currency_code="ETB",
            is_active=True,
        )
        self.requests: list[AgentRedeemRequest] = []

    async def get_active(self) -> AgentRewardSettings | None:
        return self.settings

    def add_settings(self, settings: AgentRewardSettings) -> None:
        self.settings = settings

    def add_redeem_request(self, request: AgentRedeemRequest) -> None:
        self.requests.append(request)


@pytest.fixture
def service() -> tuple[AgentScoreService, FakeContributorRepository, FakeSession]:
    session = FakeSession()
    repo = FakeContributorRepository()
    rewards = FakeRewardSettingsRepository()
    return AgentScoreService(session, repo, rewards), repo, session  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_activate_and_score_lifecycle(
    service: tuple[AgentScoreService, FakeContributorRepository, FakeSession],
) -> None:
    score_service, repo, session = service
    contributor = await score_service.activate_with_invite(
        telegram_id="12345",
        invite_code="WAGA-ADDIS-01",
        display_name="Test Agent",
    )
    assert contributor.is_agent is True
    assert contributor.kind == ContributorKind.AGENT
    assert repo.invites["waga-addis-01"].uses_count == 1

    contributor = await score_service.record_pending_submit("12345")
    assert contributor.reputation_score == 1
    assert contributor.pending_count == 1

    contributor = await score_service.apply_review("12345", accepted=True)
    assert contributor.reputation_score == POINTS_ACCEPT
    assert contributor.accepted_count == 1
    assert contributor.pending_count == 0
    assert session.commits >= 3


@pytest.mark.asyncio
async def test_flag_can_ban_and_block_redeem(
    service: tuple[AgentScoreService, FakeContributorRepository, FakeSession],
) -> None:
    score_service, _, _ = service
    await score_service.activate_with_invite(
        telegram_id="99",
        invite_code="waga-addis-01",
    )
    for _ in range(3):
        await score_service.record_pending_submit("99")
        contributor = await score_service.apply_review("99", accepted=False)
    assert contributor.banned is True

    with pytest.raises(AgentBannedError):
        await score_service.record_pending_submit("99")


@pytest.mark.asyncio
async def test_redeem_converts_points_to_birr(
    service: tuple[AgentScoreService, FakeContributorRepository, FakeSession],
) -> None:
    score_service, repo, _ = service
    await score_service.activate_with_invite(telegram_id="7", invite_code="waga-addis-01")
    agent = repo.contributors["7"]
    agent.reputation_score = REDEEM_THRESHOLD - 1

    with pytest.raises(AgentRedeemNotReadyError):
        await score_service.redeem("7")

    agent.reputation_score = REDEEM_THRESHOLD
    contributor, points, birr_amount, request = await score_service.redeem("7")
    assert points == REDEEM_THRESHOLD
    assert birr_amount == Decimal("100.00")  # 50 × 2 birr
    assert contributor.reputation_score == 0
    assert contributor.redeemed_total == REDEEM_THRESHOLD
    assert request.status == "pending"
    assert request.birr_amount == Decimal("100.00")


@pytest.mark.asyncio
async def test_invalid_invite(
    service: tuple[AgentScoreService, FakeContributorRepository, FakeSession],
) -> None:
    score_service, _, _ = service
    with pytest.raises(AgentInviteInvalidError):
        await score_service.activate_with_invite(
            telegram_id="1",
            invite_code="nope",
        )
