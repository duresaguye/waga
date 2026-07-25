from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import BillingPlan, DataTier
from app.models.subscriptions import SubscriptionPlan
from app.repositories.subscription_plans import SubscriptionPlanRepository
from app.services.exceptions import PlanConflictError, PlanInUseError, PlanNotFoundError


class SubscriptionPlanService:
    def __init__(
        self,
        session: AsyncSession,
        plans: SubscriptionPlanRepository,
    ) -> None:
        self._session = session
        self._plans = plans

    async def list_plans(
        self,
        *,
        active_only: bool = False,
        public_only: bool = False,
    ) -> list[SubscriptionPlan]:
        return await self._plans.list_plans(
            active_only=active_only,
            public_only=public_only,
        )

    async def get_plan(self, plan_id: UUID) -> SubscriptionPlan:
        plan = await self._plans.get_by_id(plan_id)
        if plan is None:
            raise PlanNotFoundError(f"Plan {plan_id} not found")
        return plan

    async def get_checkout_plan(
        self,
        *,
        plan_id: UUID | None = None,
        billing_plan: BillingPlan | None = None,
    ) -> SubscriptionPlan:
        if plan_id is not None:
            plan = await self.get_plan(plan_id)
            if not plan.is_active:
                raise PlanNotFoundError(f"Plan {plan_id} is not active")
            return plan

        if billing_plan is None:
            raise PlanNotFoundError("Either plan_id or billing_plan is required")

        plan = await self._plans.get_active_by_tier_and_billing(
            DataTier.PROFESSIONAL,
            billing_plan,
        )
        if plan is None:
            raise PlanNotFoundError(
                f"No active plan found for professional {billing_plan.value} billing",
            )
        return plan

    async def create_plan(
        self,
        *,
        code: str,
        tier: DataTier,
        billing_plan: BillingPlan | None,
        name_en: str,
        name_am: str,
        amount_etb: Decimal,
        description_en: str | None = None,
        description_am: str | None = None,
        trial_days: int | None = None,
        exports_per_day: int | None = None,
        history_days: int | None = None,
        is_active: bool = True,
        is_public: bool = True,
        sort_order: int = 0,
    ) -> SubscriptionPlan:
        plan = SubscriptionPlan(
            id=uuid4(),
            code=code.strip().lower(),
            tier=tier,
            billing_plan=billing_plan,
            name_en=name_en.strip(),
            name_am=name_am.strip(),
            description_en=description_en.strip() if description_en else None,
            description_am=description_am.strip() if description_am else None,
            amount_etb=amount_etb,
            trial_days=trial_days,
            exports_per_day=exports_per_day,
            history_days=history_days,
            is_active=is_active,
            is_public=is_public,
            sort_order=sort_order,
        )
        self._plans.add(plan)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise PlanConflictError("Plan code already exists") from error
        return plan

    async def update_plan(self, plan_id: UUID, **fields) -> SubscriptionPlan:
        plan = await self.get_plan(plan_id)
        if "code" in fields and fields["code"] is not None:
            fields["code"] = fields["code"].strip().lower()
        for key, value in fields.items():
            if value is not None or key in {"billing_plan", "description_en", "description_am"}:
                setattr(plan, key, value)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise PlanConflictError("Plan code already exists") from error
        return plan

    async def delete_plan(self, plan_id: UUID) -> None:
        plan = await self.get_plan(plan_id)
        references = await self._plans.count_references(plan_id)
        if references:
            raise PlanInUseError("Plan is referenced by subscriptions or payments")
        await self._session.delete(plan)
        await self._session.commit()
