from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_subscription_plan_service
from app.main import app
from app.models.enums import BillingPlan, DataTier
from app.models.subscriptions import SubscriptionPlan
from app.services.exceptions import PlanNotFoundError
from app.services.subscription_plans import SubscriptionPlanService


class FakePlanRepository:
    def __init__(self) -> None:
        self.plans: dict = {}

    def add(self, plan: SubscriptionPlan) -> None:
        self.plans[plan.id] = plan

    async def get_by_id(self, plan_id):
        return self.plans.get(plan_id)

    async def get_by_code(self, code):
        for plan in self.plans.values():
            if plan.code == code:
                return plan
        return None

    async def get_active_by_tier_and_billing(self, tier, billing_plan):
        for plan in self.plans.values():
            if (
                plan.tier == tier
                and plan.billing_plan == billing_plan
                and plan.is_active
            ):
                return plan
        return None

    async def list_plans(self, *, active_only=False, public_only=False):
        plans = list(self.plans.values())
        if active_only:
            plans = [plan for plan in plans if plan.is_active]
        if public_only:
            plans = [plan for plan in plans if plan.is_public]
        return sorted(plans, key=lambda plan: plan.sort_order)

    async def count_references(self, plan_id):
        _ = plan_id
        return 0


class FakeDatabaseSession:
    def __init__(self, repo: FakePlanRepository) -> None:
        self._repo = repo

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None

    async def delete(self, plan) -> None:
        self._repo.plans.pop(plan.id, None)


def _plan(**overrides) -> SubscriptionPlan:
    defaults = {
        "id": uuid4(),
        "code": "professional_monthly",
        "tier": DataTier.PROFESSIONAL,
        "billing_plan": BillingPlan.MONTHLY,
        "name_en": "Professional Monthly",
        "name_am": "Professional Monthly",
        "amount_etb": Decimal("1600"),
        "is_active": True,
        "is_public": True,
        "sort_order": 1,
        "created_at": datetime(2026, 7, 26, tzinfo=UTC),
        "updated_at": datetime(2026, 7, 26, tzinfo=UTC),
    }
    defaults.update(overrides)
    return SubscriptionPlan(**defaults)


def _service() -> tuple[SubscriptionPlanService, FakePlanRepository]:
    repo = FakePlanRepository()
    service = SubscriptionPlanService(FakeDatabaseSession(repo), repo)  # type: ignore[arg-type]
    return service, repo


async def test_create_and_get_plan() -> None:
    service, repo = _service()

    created = await service.create_plan(
        code="professional_monthly",
        tier=DataTier.PROFESSIONAL,
        billing_plan=BillingPlan.MONTHLY,
        name_en="Professional Monthly",
        name_am="Professional Monthly",
        amount_etb=Decimal("1600"),
    )

    assert created.code == "professional_monthly"
    fetched = await service.get_plan(created.id)
    assert fetched.name_en == "Professional Monthly"
    assert len(repo.plans) == 1


async def test_get_checkout_plan_by_billing_plan() -> None:
    service, repo = _service()
    plan = _plan()
    repo.add(plan)

    resolved = await service.get_checkout_plan(billing_plan=BillingPlan.MONTHLY)

    assert resolved.id == plan.id


async def test_get_checkout_plan_missing_raises() -> None:
    service, _ = _service()

    with pytest.raises(PlanNotFoundError):
        await service.get_checkout_plan(billing_plan=BillingPlan.MONTHLY)


async def test_delete_plan_not_found() -> None:
    service, _ = _service()

    with pytest.raises(PlanNotFoundError):
        await service.delete_plan(uuid4())


class FakePlanServiceForApi:
    def __init__(self) -> None:
        self.plan = _plan()

    async def list_plans(self, *, active_only=False, public_only=False):
        _ = (active_only, public_only)
        return [self.plan]

    async def create_plan(self, **kwargs):
        _ = kwargs
        return self.plan

    async def get_plan(self, plan_id):
        if plan_id != self.plan.id:
            raise PlanNotFoundError("missing")
        return self.plan

    async def update_plan(self, plan_id, **fields):
        if plan_id != self.plan.id:
            raise PlanNotFoundError("missing")
        for key, value in fields.items():
            setattr(self.plan, key, value)
        return self.plan

    async def delete_plan(self, plan_id):
        if plan_id != self.plan.id:
            raise PlanNotFoundError("missing")


async def test_public_plans_endpoint() -> None:
    fake = FakePlanServiceForApi()
    app.dependency_overrides[get_subscription_plan_service] = lambda: fake
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/plans")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["code"] == "professional_monthly"
