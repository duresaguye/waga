from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import BillingPlan, DataTier
from app.models.subscriptions import SubscriptionPlan


class SubscriptionPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, plan: SubscriptionPlan) -> None:
        self._session.add(plan)

    async def get_by_id(self, plan_id: UUID) -> SubscriptionPlan | None:
        return await self._session.get(SubscriptionPlan, plan_id)

    async def get_by_code(self, code: str) -> SubscriptionPlan | None:
        normalized = code.strip().lower()
        result = await self._session.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.code == normalized),
        )
        return result.scalar_one_or_none()

    async def get_active_by_tier_and_billing(
        self,
        tier: DataTier,
        billing_plan: BillingPlan,
    ) -> SubscriptionPlan | None:
        result = await self._session.execute(
            select(SubscriptionPlan)
            .where(
                SubscriptionPlan.tier == tier,
                SubscriptionPlan.billing_plan == billing_plan,
                SubscriptionPlan.is_active.is_(True),
            )
            .order_by(SubscriptionPlan.sort_order)
            .limit(1),
        )
        return result.scalar_one_or_none()

    async def list_plans(
        self,
        *,
        active_only: bool = False,
        public_only: bool = False,
    ) -> list[SubscriptionPlan]:
        query = select(SubscriptionPlan).order_by(
            SubscriptionPlan.sort_order,
            SubscriptionPlan.created_at,
        )
        if active_only:
            query = query.where(SubscriptionPlan.is_active.is_(True))
        if public_only:
            query = query.where(SubscriptionPlan.is_public.is_(True))
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_references(self, plan_id: UUID) -> int:
        from app.models.subscriptions import PaymentTransaction, Subscription

        subscription_count = await self._session.scalar(
            select(Subscription.id).where(Subscription.plan_id == plan_id).limit(1),
        )
        payment_count = await self._session.scalar(
            select(PaymentTransaction.id).where(PaymentTransaction.plan_id == plan_id).limit(1),
        )
        return int(subscription_count is not None) + int(payment_count is not None)
