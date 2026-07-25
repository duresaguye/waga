from datetime import date
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User
from app.models.enums import PaymentStatus, UserRole
from app.models.subscriptions import (
    EnterpriseEnquiry,
    PaymentTransaction,
    Subscription,
    SubscriptionUsage,
)


class SubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add_subscription(self, subscription: Subscription) -> None:
        self._session.add(subscription)

    def add_usage(self, usage: SubscriptionUsage) -> None:
        self._session.add(usage)

    def add_payment(self, payment: PaymentTransaction) -> None:
        self._session.add(payment)

    def add_enquiry(self, enquiry: EnterpriseEnquiry) -> None:
        self._session.add(enquiry)

    async def get_subscription_by_user_id(
        self,
        user_id: UUID,
        *,
        for_update: bool = False,
    ) -> Subscription | None:
        statement = select(Subscription).where(Subscription.user_id == user_id)
        if for_update:
            statement = statement.with_for_update()
        return cast(Subscription | None, await self._session.scalar(statement))

    async def get_payment_by_id(
        self,
        payment_id: UUID,
        *,
        for_update: bool = False,
    ) -> PaymentTransaction | None:
        statement = select(PaymentTransaction).where(PaymentTransaction.id == payment_id)
        if for_update:
            statement = statement.with_for_update()
        return cast(PaymentTransaction | None, await self._session.scalar(statement))

    async def get_payment_by_tx_ref(
        self,
        tx_ref: str,
        *,
        for_update: bool = False,
    ) -> PaymentTransaction | None:
        statement = select(PaymentTransaction).where(PaymentTransaction.tx_ref == tx_ref)
        if for_update:
            statement = statement.with_for_update()
        return cast(PaymentTransaction | None, await self._session.scalar(statement))

    async def list_subscriptions(self) -> list[tuple[User, Subscription]]:
        statement = (
            select(User, Subscription)
            .join(Subscription, Subscription.user_id == User.id)
            .where(User.role == UserRole.SUBSCRIBER)
            .order_by(User.created_at.desc())
        )
        rows = await self._session.execute(statement)
        return list(rows.all())

    async def list_payments(
        self,
        *,
        status: PaymentStatus | None = None,
    ) -> list[PaymentTransaction]:
        statement = select(PaymentTransaction).order_by(PaymentTransaction.created_at.desc())
        if status is not None:
            statement = statement.where(PaymentTransaction.status == status)
        return list(await self._session.scalars(statement))

    async def list_enquiries(self) -> list[EnterpriseEnquiry]:
        statement = select(EnterpriseEnquiry).order_by(EnterpriseEnquiry.created_at.desc())
        return list(await self._session.scalars(statement))

    async def get_enquiry_by_id(
        self,
        enquiry_id: UUID,
        *,
        for_update: bool = False,
    ) -> EnterpriseEnquiry | None:
        statement = select(EnterpriseEnquiry).where(EnterpriseEnquiry.id == enquiry_id)
        if for_update:
            statement = statement.with_for_update()
        return cast(EnterpriseEnquiry | None, await self._session.scalar(statement))

    async def get_usage_for_date(
        self,
        user_id: UUID,
        usage_date: date,
        *,
        for_update: bool = False,
    ) -> SubscriptionUsage | None:
        statement = select(SubscriptionUsage).where(
            SubscriptionUsage.user_id == user_id,
            SubscriptionUsage.usage_date == usage_date,
        )
        if for_update:
            statement = statement.with_for_update()
        return cast(SubscriptionUsage | None, await self._session.scalar(statement))

    async def get_subscription_with_user(self, user_id: UUID) -> tuple[User, Subscription] | None:
        row = await self._session.execute(
            select(User, Subscription)
            .join(Subscription, Subscription.user_id == User.id)
            .where(User.id == user_id)
        )
        result = row.one_or_none()
        return None if result is None else (result[0], result[1])
