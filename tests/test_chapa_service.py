import hashlib
import hmac
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest

from app.config import Settings
from app.models.auth import User
from app.models.enums import (
    BillingPlan,
    DataTier,
    PaymentProvider,
    PaymentStatus,
    SubscriptionStatus,
    UserRole,
    UserStatus,
)
from app.models.subscriptions import PaymentTransaction, Subscription, SubscriptionPlan
from app.services.chapa import ChapaPaymentService
from app.services.exceptions import ChapaNotConfiguredError, ChapaWebhookInvalidError


class FakeDatabaseSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def flush(self) -> None:
        return None


class FakeSubscriptionRepository:
    def __init__(self) -> None:
        self.payments: dict[str, PaymentTransaction] = {}
        self.payments_by_id: dict = {}
        self.subscription: Subscription | None = None

    def add_payment(self, payment: PaymentTransaction) -> None:
        self.payments[payment.tx_ref] = payment
        self.payments_by_id[payment.id] = payment

    async def get_subscription_by_user_id(self, user_id, *, for_update=False):
        _ = (user_id, for_update)
        return self.subscription

    async def get_payment_by_tx_ref(self, tx_ref, *, for_update=False):
        _ = for_update
        return self.payments.get(tx_ref)

    async def get_payment_by_id(self, payment_id, *, for_update=False):
        _ = for_update
        return self.payments_by_id.get(payment_id)


class FakeSubscriptionService:
    def __init__(self) -> None:
        self.activated: list[tuple] = []

    async def activate_subscription(self, user_id, billing_plan, **kwargs):
        self.activated.append((user_id, billing_plan, kwargs))


class FakePlanService:
    def __init__(self) -> None:
        self.plan = SubscriptionPlan(
            id=uuid4(),
            code="professional_monthly",
            tier=DataTier.PROFESSIONAL,
            billing_plan=BillingPlan.MONTHLY,
            name_en="Professional Monthly",
            name_am="Professional Monthly",
            amount_etb=Decimal("1600"),
            is_active=True,
            is_public=True,
            sort_order=1,
        )

    async def get_checkout_plan(self, *, plan_id=None, billing_plan=None):
        _ = plan_id
        if billing_plan == BillingPlan.ANNUAL:
            return SubscriptionPlan(
                id=uuid4(),
                code="professional_annual",
                tier=DataTier.PROFESSIONAL,
                billing_plan=BillingPlan.ANNUAL,
                name_en="Professional Annual",
                name_am="Professional Annual",
                amount_etb=Decimal("16000"),
                is_active=True,
                is_public=True,
                sort_order=2,
            )
        return self.plan

    async def get_plan(self, plan_id):
        _ = plan_id
        return self.plan


def _settings(*, with_webhook: bool = True) -> Settings:
    return Settings(
        jwt_secret_key="test-secret-key-with-enough-bytes-123456",
        password_min_length=8,
        chapa_test_secret_key="CHASECK_TEST-secret",
        chapa_webhook_secret="webhook-secret" if with_webhook else None,
        chapa_return_url="http://localhost:5173/account/billing",
    )


def _user() -> User:
    return User(
        id=uuid4(),
        email="subscriber@example.com",
        password_hash="unused",
        display_name="Ada Lovelace",
        role=UserRole.SUBSCRIBER,
        status=UserStatus.ACTIVE,
        auth_version=1,
        failed_login_attempts=0,
        created_at=datetime(2026, 7, 26, tzinfo=UTC),
    )


def _subscription(user_id) -> Subscription:
    return Subscription(
        id=uuid4(),
        user_id=user_id,
        tier=DataTier.PROFESSIONAL,
        status=SubscriptionStatus.TRIAL,
        billing_plan=BillingPlan.MONTHLY,
    )


def _make_service(
    handler,
) -> tuple[ChapaPaymentService, FakeSubscriptionRepository, FakeSubscriptionService]:
    session = FakeDatabaseSession()
    repo = FakeSubscriptionRepository()
    sub_service = FakeSubscriptionService()
    plan_service = FakePlanService()
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = ChapaPaymentService(
        session,  # type: ignore[arg-type]
        repo,  # type: ignore[arg-type]
        sub_service,  # type: ignore[arg-type]
        plan_service,  # type: ignore[arg-type]
        _settings(),
        http_client=client,
    )
    return service, repo, sub_service


async def test_create_checkout_returns_checkout_url() -> None:
    user = _user()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path.endswith("/transaction/initialize")
        return httpx.Response(
            200,
            json={
                "status": "success",
                "message": "Hosted Link",
                "data": {"checkout_url": "https://checkout.chapa.co/pay/xyz"},
            },
        )

    service, repo, _ = _make_service(handler)
    repo.subscription = _subscription(user.id)

    payment = await service.create_checkout(user, billing_plan=BillingPlan.MONTHLY)

    assert payment.provider == PaymentProvider.CHAPA
    assert payment.checkout_url == "https://checkout.chapa.co/pay/xyz"
    assert payment.tx_ref.startswith("waga-")
    assert payment.plan_id is not None


async def test_verify_and_finalize_success_activates_subscription() -> None:
    user = _user()
    plan_id = uuid4()
    payment = PaymentTransaction(
        id=uuid4(),
        user_id=user.id,
        provider=PaymentProvider.CHAPA,
        amount_etb=Decimal("1600"),
        billing_plan=BillingPlan.MONTHLY,
        plan_id=plan_id,
        status=PaymentStatus.PENDING,
        tx_ref="waga-test-success",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        return httpx.Response(
            200,
            json={
                "status": "success",
                "data": {"status": "success", "reference": "CHAPA-123"},
            },
        )

    service, repo, sub_service = _make_service(handler)
    repo.payments[payment.tx_ref] = payment
    repo.payments_by_id[payment.id] = payment

    finalized = await service.verify_and_finalize("waga-test-success")

    assert finalized.status == PaymentStatus.SUCCEEDED
    assert finalized.chapa_ref_id == "CHAPA-123"
    assert sub_service.activated[0][0] == user.id
    assert sub_service.activated[0][1] == BillingPlan.MONTHLY


def _pending_payment(tx_ref: str) -> PaymentTransaction:
    return PaymentTransaction(
        id=uuid4(),
        user_id=uuid4(),
        provider=PaymentProvider.CHAPA,
        amount_etb=Decimal("1600"),
        billing_plan=BillingPlan.MONTHLY,
        plan_id=uuid4(),
        status=PaymentStatus.PENDING,
        tx_ref=tx_ref,
    )


@pytest.mark.parametrize("chapa_status", ["pending", "processing", "queued", ""])
async def test_verify_and_finalize_keeps_payment_open_when_not_yet_settled(
    chapa_status: str,
) -> None:
    payment = _pending_payment("waga-test-pending")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"status": "success", "data": {"status": chapa_status}},
        )

    service, repo, sub_service = _make_service(handler)
    repo.payments[payment.tx_ref] = payment
    repo.payments_by_id[payment.id] = payment

    result = await service.verify_and_finalize(payment.tx_ref)

    assert result.status == PaymentStatus.PENDING
    assert result.failure_reason is None
    assert result.confirmed_at is None
    assert sub_service.activated == []


@pytest.mark.parametrize("chapa_status", ["failed", "cancelled", "expired"])
async def test_verify_and_finalize_marks_failed_on_terminal_status(
    chapa_status: str,
) -> None:
    payment = _pending_payment("waga-test-terminal")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"status": "success", "data": {"status": chapa_status}},
        )

    service, repo, sub_service = _make_service(handler)
    repo.payments[payment.tx_ref] = payment
    repo.payments_by_id[payment.id] = payment

    result = await service.verify_and_finalize(payment.tx_ref)

    assert result.status == PaymentStatus.FAILED
    assert result.failure_reason == chapa_status
    assert result.confirmed_at is not None
    assert sub_service.activated == []


async def test_verify_and_finalize_keeps_payment_open_on_malformed_response() -> None:
    payment = _pending_payment("waga-test-malformed")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "success", "data": None})

    service, repo, _ = _make_service(handler)
    repo.payments[payment.tx_ref] = payment
    repo.payments_by_id[payment.id] = payment

    result = await service.verify_and_finalize(payment.tx_ref)

    assert result.status == PaymentStatus.PENDING
    assert result.failure_reason is None


async def test_get_checkout_status_returns_finalized_payment_without_verify() -> None:
    user = _user()
    payment = PaymentTransaction(
        id=uuid4(),
        user_id=user.id,
        provider=PaymentProvider.CHAPA,
        amount_etb=Decimal("1600"),
        billing_plan=BillingPlan.MONTHLY,
        status=PaymentStatus.SUCCEEDED,
        tx_ref="waga-test-status",
        confirmed_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("verify should not be called for finalized payment")

    service, repo, _ = _make_service(handler)
    repo.payments_by_id[payment.id] = payment

    result = await service.get_checkout_status(user, payment.id)

    assert result.id == payment.id
    assert result.status == PaymentStatus.SUCCEEDED


async def test_verify_and_finalize_is_idempotent_for_finalized_payment() -> None:
    payment = PaymentTransaction(
        id=uuid4(),
        user_id=uuid4(),
        provider=PaymentProvider.CHAPA,
        amount_etb=Decimal("1600"),
        billing_plan=BillingPlan.MONTHLY,
        status=PaymentStatus.SUCCEEDED,
        tx_ref="waga-test-final",
        confirmed_at=datetime.now(UTC),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("verify should not be called for finalized payment")

    service, repo, _ = _make_service(handler)
    repo.payments[payment.tx_ref] = payment
    repo.payments_by_id[payment.id] = payment

    result = await service.verify_and_finalize("waga-test-final")

    assert result.status == PaymentStatus.SUCCEEDED


def test_verify_webhook_signature_accepts_valid_signature() -> None:
    body = b'{"tx_ref":"waga-123","status":"success"}'
    secret = "webhook-secret"
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    service, _, _ = _make_service(lambda request: httpx.Response(200, json={}))

    service.verify_webhook_signature(body, signature)


def test_verify_webhook_signature_rejects_invalid_signature() -> None:
    service, _, _ = _make_service(lambda request: httpx.Response(200, json={}))

    with pytest.raises(ChapaWebhookInvalidError):
        service.verify_webhook_signature(b"{}", "bad-signature")


def test_chapa_not_configured_without_secret_key() -> None:
    service = ChapaPaymentService(
        FakeDatabaseSession(),  # type: ignore[arg-type]
        FakeSubscriptionRepository(),  # type: ignore[arg-type]
        FakeSubscriptionService(),  # type: ignore[arg-type]
        FakePlanService(),  # type: ignore[arg-type]
        Settings(
            jwt_secret_key="test-secret-key-with-enough-bytes-123456",
            password_min_length=8,
            chapa_test_secret_key=None,
        ),
    )

    with pytest.raises(ChapaNotConfiguredError):
        service._require_secret_key()  # noqa: SLF001


def test_format_chapa_error_handles_validation_object_message() -> None:
    detail = ChapaPaymentService._format_chapa_error(
        {"status": "failed", "message": {"email": ["validation.email"]}}
    )
    assert detail == "email: validation.email"


def test_checkout_customization_respects_chapa_limits() -> None:
    customization = ChapaPaymentService._checkout_customization("Professional Monthly (monthly)")
    assert len(customization["title"]) <= 16
    assert customization["title"] == "Waga"
    assert customization["description"] == "Professional Monthly monthly"
    assert "(" not in customization["description"]
