from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.dependencies import (
    get_chapa_payment_service,
    get_current_subscriber,
    get_subscription_service,
    require_feature,
)
from app.main import app
from app.models.auth import User
from app.models.enums import (
    BillingPlan,
    DataTier,
    GateFeature,
    PaymentStatus,
    SubscriptionStatus,
    UserRole,
    UserStatus,
)
from app.models.subscriptions import PaymentTransaction, Subscription
from app.services.auth import IssuedTokens
from app.services.subscriptions import AccessResult, SubscriptionContext, SubscriptionService


class FakeSubscriptionService:
    def __init__(self) -> None:
        self.subscription = Subscription(
            id=uuid4(),
            user_id=uuid4(),
            organisation="Demo NGO",
            tier=DataTier.PROFESSIONAL,
            status=SubscriptionStatus.TRIAL,
            trial_started_at=datetime(2026, 7, 1, tzinfo=UTC).date(),
            trial_ends_at=datetime(2026, 8, 1, tzinfo=UTC).date(),
        )
        self.user = User(
            id=self.subscription.user_id,
            email="subscriber@example.com",
            password_hash="unused",
            display_name="Subscriber",
            role=UserRole.SUBSCRIBER,
            status=UserStatus.ACTIVE,
            auth_version=1,
            failed_login_attempts=0,
            created_at=datetime(2026, 7, 25, tzinfo=UTC),
        )

    async def register_subscriber(
        self,
        email,
        password,
        full_name,
        organisation=None,
        language=None,
    ):
        _ = (email, password, full_name, organisation, language)
        return IssuedTokens("access-token", "refresh-token", 900)

    async def get_context_for_user(self, user: User | None) -> SubscriptionContext:
        if user is None:
            return SubscriptionContext(None, None, DataTier.PUBLIC)
        return SubscriptionContext(user, self.subscription, DataTier.PROFESSIONAL)

    async def exports_used_today(self, user_id):
        _ = user_id
        return 0

    def access_matrix(self, subscription, exports_used_today):
        _ = (subscription, exports_used_today)
        return {GateFeature.MAP.value: AccessResult(True, "ok")}

    def api_contract_tier(self, tier):
        return SubscriptionService.api_contract_tier(tier)

    def can_access(self, subscription, feature, *, exports_used_today=0):
        _ = exports_used_today
        if subscription is None:
            return AccessResult(False, "paywall")
        if feature == GateFeature.MAP:
            return AccessResult(True, "ok")
        return AccessResult(False, "paywall")

    async def ensure_subscription(self, user):
        self.user = user
        self.subscription.user_id = user.id
        return self.subscription


class FakeChapaService:
    async def create_checkout(self, user, *, plan_id=None, billing_plan=None):
        _ = (plan_id, billing_plan)
        return PaymentTransaction(
            id=uuid4(),
            user_id=user.id,
            amount_etb=Decimal("1600"),
            billing_plan=billing_plan,
            status=PaymentStatus.PENDING,
            tx_ref="waga-test-checkout",
            checkout_url="https://checkout.chapa.co/pay/test",
            created_at=datetime(2026, 7, 26, tzinfo=UTC),
        )

    async def get_checkout_status(self, user, payment_id):
        _ = user
        return PaymentTransaction(
            id=payment_id,
            user_id=user.id,
            amount_etb=Decimal("1600"),
            billing_plan=BillingPlan.MONTHLY,
            status=PaymentStatus.SUCCEEDED,
            tx_ref="waga-test-checkout",
            checkout_url="https://checkout.chapa.co/pay/test",
            created_at=datetime(2026, 7, 26, tzinfo=UTC),
        )


async def test_subscriber_register_returns_token_pair() -> None:
    app.dependency_overrides[get_subscription_service] = lambda: FakeSubscriptionService()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/subscriber/register",
                json={
                    "email": "ngo@example.com",
                    "password": "valid-password",
                    "full_name": "NGO User",
                    "organisation": "Relief Org",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["access_token"] == "access-token"


async def test_access_matrix_for_anonymous_user() -> None:
    fake = FakeSubscriptionService()
    app.dependency_overrides[get_subscription_service] = lambda: fake
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/subscriptions/access")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["effective_tier"] == "public"
    assert body["api_contract_tier"] == "public"


async def test_checkout_returns_chapa_url() -> None:
    fake_user = FakeSubscriptionService().user
    app.dependency_overrides[get_chapa_payment_service] = lambda: FakeChapaService()
    app.dependency_overrides[get_current_subscriber] = lambda: fake_user
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/subscriptions/checkout",
                json={"billing_plan": "monthly"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["checkout_url"].startswith("https://checkout.chapa.co/")
    assert body["tx_ref"] == "waga-test-checkout"


async def test_get_checkout_status_returns_payment() -> None:
    fake_user = FakeSubscriptionService().user
    payment_id = uuid4()
    app.dependency_overrides[get_chapa_payment_service] = lambda: FakeChapaService()
    app.dependency_overrides[get_current_subscriber] = lambda: fake_user
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/subscriptions/checkout/{payment_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "succeeded"


async def test_require_feature_blocks_public_access() -> None:
    fake = FakeSubscriptionService()
    app.dependency_overrides[get_subscription_service] = lambda: fake
    dependency = require_feature(GateFeature.HISTORY)

    with pytest.raises(HTTPException) as error:
        await dependency(
            await fake.get_context_for_user(None),
            fake,  # type: ignore[arg-type]
            None,
        )

    assert error.value.status_code == 403
    assert error.value.detail["error"]["code"] == "tier_required"


async def test_get_current_subscriber_rejects_contributor() -> None:
    fake = FakeSubscriptionService()
    contributor = User(
        id=uuid4(),
        email="contributor@example.com",
        password_hash="unused",
        role=UserRole.CONTRIBUTOR,
        status=UserStatus.ACTIVE,
        auth_version=1,
        failed_login_attempts=0,
    )

    with pytest.raises(HTTPException) as error:
        await get_current_subscriber(contributor, fake)  # type: ignore[arg-type]

    assert error.value.status_code == 403
    assert error.value.detail == "Subscriber account required"
