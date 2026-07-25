from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from app.config import Settings
from app.models.enums import (
    BillingPlan,
    DataTier,
    GateFeature,
    SubscriptionStatus,
)
from app.models.subscriptions import Subscription
from app.services.subscriptions import SubscriptionService


def _settings() -> Settings:
    return Settings(
        jwt_secret_key="test-secret-key-with-enough-bytes-123456",
        password_min_length=8,
    )


def _service() -> SubscriptionService:
    return SubscriptionService(
        session=None,  # type: ignore[arg-type]
        users=None,  # type: ignore[arg-type]
        subscriptions=None,  # type: ignore[arg-type]
        auth_sessions=None,  # type: ignore[arg-type]
        passwords=None,  # type: ignore[arg-type]
        jwt_service=None,  # type: ignore[arg-type]
        settings=_settings(),
    )


def _subscription(
    *,
    tier: DataTier = DataTier.PROFESSIONAL,
    status: SubscriptionStatus = SubscriptionStatus.TRIAL,
    billing_plan: BillingPlan = BillingPlan.MONTHLY,
    trial_ends_at: date | None = None,
) -> Subscription:
    return Subscription(
        id=uuid4(),
        user_id=uuid4(),
        organisation="Demo NGO",
        tier=tier,
        status=status,
        billing_plan=billing_plan,
        trial_started_at=date(2026, 7, 1),
        trial_ends_at=trial_ends_at,
    )


def test_public_tier_blocks_pro_features() -> None:
    service = _service()
    for feature in (
        GateFeature.HISTORY,
        GateFeature.MAP,
        GateFeature.EXPORT,
        GateFeature.API,
    ):
        result = service.can_access(None, feature)
        assert result.allowed is False
        assert result.reason == "paywall"


def test_professional_allows_pro_surfaces() -> None:
    service = _service()
    subscription = _subscription()
    for feature in (
        GateFeature.HISTORY,
        GateFeature.SOURCE,
        GateFeature.CONFIDENCE,
        GateFeature.COMPARISON,
        GateFeature.MAP,
    ):
        result = service.can_access(subscription, feature)
        assert result.allowed is True
        assert result.reason == "ok"


def test_professional_blocks_enterprise_features() -> None:
    service = _service()
    subscription = _subscription()
    for feature in (GateFeature.API, GateFeature.BASKET):
        result = service.can_access(subscription, feature)
        assert result.allowed is False
        assert result.reason == "upgrade"


def test_export_quota_enforced_for_professional() -> None:
    service = _service()
    subscription = _subscription(status=SubscriptionStatus.ACTIVE)
    assert service.can_access(subscription, GateFeature.EXPORT, exports_used_today=0).allowed
    assert service.can_access(
        subscription,
        GateFeature.EXPORT,
        exports_used_today=1,
    ).allowed is False


def test_enterprise_has_unlimited_exports() -> None:
    service = _service()
    subscription = _subscription(tier=DataTier.ENTERPRISE, status=SubscriptionStatus.ACTIVE)
    assert service.export_quota(DataTier.ENTERPRISE) is None
    assert service.can_access(
        subscription,
        GateFeature.EXPORT,
        exports_used_today=99,
    ).allowed is True


def test_history_depth_by_plan() -> None:
    service = _service()
    monthly = _subscription(billing_plan=BillingPlan.MONTHLY)
    annual = _subscription(billing_plan=BillingPlan.ANNUAL)
    enterprise = _subscription(tier=DataTier.ENTERPRISE, status=SubscriptionStatus.ACTIVE)

    assert service.history_depth_days(monthly) == 30
    assert service.history_depth_days(annual) == 90
    assert service.history_depth_days(enterprise) is None
    assert service.history_depth_days(None) == 0


def test_cancelled_subscription_falls_back_to_public() -> None:
    service = _service()
    subscription = _subscription(status=SubscriptionStatus.CANCELLED)
    assert service.get_effective_tier(subscription) == DataTier.PUBLIC
    assert service.can_access(subscription, GateFeature.MAP).reason == "paywall"


def test_expired_trial_falls_back_to_public() -> None:
    service = _service()
    subscription = _subscription(
        trial_ends_at=date(2026, 7, 1),
    )
    service._clock = lambda: datetime(2026, 7, 20, tzinfo=UTC)  # noqa: SLF001
    assert service.get_effective_tier(subscription) == DataTier.PUBLIC
    assert service.can_access(subscription, GateFeature.MAP).reason == "paywall"


@pytest.mark.parametrize(
    ("tier", "expected"),
    [
        (DataTier.PUBLIC, "public"),
        (DataTier.PROFESSIONAL, "full"),
        (DataTier.ENTERPRISE, "research"),
    ],
)
def test_api_contract_tier_mapping(tier: DataTier, expected: str) -> None:
    assert SubscriptionService.api_contract_tier(tier) == expected
