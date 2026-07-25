from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.contributors import AgentScoreEvent, Contributor, ContributorConsent
from app.models.enums import ContributorKind
from app.models.reference_data import Commodity, Market
from app.models.reward_settings import AgentRedeemRequest, AgentRewardSettings
from app.models.submissions import Submission
from app.models.verification import SubmissionVerification
from app.services.agent_score import AgentScoreService
from app.services.agent_score_rules import POINTS_PENDING, REDEEM_THRESHOLD
from app.services.exceptions import SubmissionValidationError
from app.services.submissions import SubmissionService


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rolled_back = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rolled_back += 1

    async def refresh(self, obj: object) -> None:
        _ = obj


class FakeContributorRepository:
    def __init__(self) -> None:
        self.contributors: dict[str, Contributor] = {}
        self.events: list[AgentScoreEvent] = []
        self.consents: list[ContributorConsent] = []

    def add(self, contributor: Contributor) -> None:
        assert contributor.telegram_id is not None
        self.contributors[contributor.telegram_id] = contributor

    def add_score_event(self, event: AgentScoreEvent) -> None:
        self.events.append(event)

    def add_consent(self, consent: ContributorConsent) -> None:
        self.consents.append(consent)

    async def get_by_telegram_id(self, telegram_id: str) -> Contributor | None:
        return self.contributors.get(telegram_id)

    async def get_consent(
        self, contributor_id: object, consent_version: str
    ) -> ContributorConsent | None:
        for consent in self.consents:
            if (
                consent.contributor_id == contributor_id
                and consent.consent_version == consent_version
            ):
                return consent
        return None

    async def get_invite_by_code(self, code: str) -> None:
        _ = code
        return None


class FakeRewardSettingsRepository:
    def __init__(self) -> None:
        self.settings = AgentRewardSettings(
            id=uuid4(),
            birr_per_point=Decimal("2"),
            redeem_min_points=REDEEM_THRESHOLD,
            currency_code="ETB",
            is_active=True,
        )

    async def get_active(self) -> AgentRewardSettings | None:
        return self.settings

    def add_settings(self, settings: AgentRewardSettings) -> None:
        self.settings = settings

    def add_redeem_request(self, request: AgentRedeemRequest) -> None:
        _ = request


class FakeReferenceRepository:
    def __init__(self) -> None:
        self.markets = {
            "merkato": Market(
                id=1,
                code="merkato",
                name_en="Merkato",
                name_am="መርካቶ",
                city_en="Addis Ababa",
                city_am="አዲስ አበባ",
                is_active=True,
            ),
            "other": Market(
                id=2,
                code="other",
                name_en="Other",
                name_am="ሌላ",
                city_en="Addis Ababa",
                city_am="አዲስ አበባ",
                is_active=True,
            ),
        }
        self.commodities = {
            "teff_mixed": Commodity(
                id=1,
                sector_id=1,
                code="teff_mixed",
                name_en="Teff",
                name_am="ጤፍ",
                canonical_unit="kg",
                is_active=True,
            )
        }

    async def get_market_by_code(self, code: str) -> Market | None:
        return self.markets.get(code)

    async def get_commodity_by_code(self, code: str) -> Commodity | None:
        return self.commodities.get(code)


class FakeSubmissionRepository:
    def __init__(self) -> None:
        self.items: list[Submission] = []
        self.verifications: list[SubmissionVerification] = []

    def add(self, submission: Submission) -> None:
        self.items.append(submission)

    def add_verification(self, verification: SubmissionVerification) -> None:
        self.verifications.append(verification)

    async def get_by_client_submission_id(
        self, *, contributor_id: object, client_submission_id: object
    ) -> Submission | None:
        for item in self.items:
            if (
                item.contributor_id == contributor_id
                and item.client_submission_id == client_submission_id
            ):
                return item
        return None


@pytest.fixture
def harness() -> tuple[SubmissionService, Contributor, FakeSession]:
    session = FakeSession()
    contributors = FakeContributorRepository()
    agent = Contributor(
        id=uuid4(),
        user_id=None,
        external_id=uuid4(),
        kind=ContributorKind.AGENT,
        telegram_id="991122",
        is_agent=True,
        reputation_score=0,
        pending_count=0,
        accepted_count=0,
        flagged_count=0,
        redeemed_total=0,
        banned=False,
        ban_reason=None,
    )
    contributors.add(agent)
    scores = AgentScoreService(session, contributors, FakeRewardSettingsRepository())  # type: ignore[arg-type]
    service = SubmissionService(
        session,
        FakeSubmissionRepository(),  # type: ignore[arg-type]
        FakeReferenceRepository(),  # type: ignore[arg-type]
        contributors,  # type: ignore[arg-type]
        scores,
    )
    return service, agent, session


@pytest.mark.asyncio
async def test_create_pending_submission_awards_score(
    harness: tuple[SubmissionService, Contributor, FakeSession],
) -> None:
    service, agent, session = harness
    client_id = uuid4()
    submission, score, label = await service.create_from_bot(
        client_submission_id=client_id,
        external_contributor_id="telegram:991122",
        market_code="merkato",
        commodity_code="teff_mixed",
        price=Decimal("95.50"),
        unit="kg",
        consent_version="contributor-v1",
    )
    assert submission.price_canonical == Decimal("95.50")
    assert label is None
    assert score["score"] == POINTS_PENDING
    assert score["pending_count"] == 1
    assert agent.pending_count == 1
    assert session.commits == 1


@pytest.mark.asyncio
async def test_other_market_requires_label(
    harness: tuple[SubmissionService, Contributor, FakeSession],
) -> None:
    service, _, _ = harness
    with pytest.raises(SubmissionValidationError, match="market_label"):
        await service.create_from_bot(
            client_submission_id=uuid4(),
            external_contributor_id="telegram:991122",
            market_code="other",
            commodity_code="teff_mixed",
            price=Decimal("10"),
            unit="kg",
            consent_version="contributor-v1",
        )


@pytest.mark.asyncio
async def test_rejects_non_agent(
    harness: tuple[SubmissionService, Contributor, FakeSession],
) -> None:
    service, _, _ = harness
    with pytest.raises(SubmissionValidationError, match="approved market agents"):
        await service.create_from_bot(
            client_submission_id=uuid4(),
            external_contributor_id="telegram:000",
            market_code="merkato",
            commodity_code="teff_mixed",
            price=Decimal("10"),
            unit="kg",
            consent_version="contributor-v1",
        )
