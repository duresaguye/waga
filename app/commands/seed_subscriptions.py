"""Seed demo subscriber accounts, usage, Chapa payments, and enterprise enquiries."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.config import get_settings
from app.database import session_factory
from app.models.auth import User
from app.models.enums import (
    BillingPlan,
    DataTier,
    EnterpriseEnquiryStatus,
    PaymentStatus,
    SubscriberLanguage,
    SubscriptionStatus,
    UpdateFrequency,
    UserRole,
    UserStatus,
)
from app.models.subscriptions import (
    EnterpriseEnquiry,
    PaymentTransaction,
    Subscription,
    SubscriptionUsage,
)
from app.repositories.users import UserRepository
from app.security import PasswordService

DEMO_PASSWORD = "DemoPassword12!"


async def seed() -> None:
    settings = get_settings()
    passwords = PasswordService()
    password_hash = await passwords.hash(DEMO_PASSWORD)
    today = datetime.now(UTC).date()

    async with session_factory() as session:
        users = UserRepository(session)
        trial_ends = today + timedelta(days=settings.trial_days)

        demo_accounts: list[dict[str, object]] = [
            {
                "email": "trial.one@ngo.example",
                "display_name": "Trial One",
                "organisation": "Hope NGO",
                "tier": DataTier.PROFESSIONAL,
                "status": SubscriptionStatus.TRIAL,
                "billing_plan": BillingPlan.MONTHLY,
                "trial_started_at": today,
                "trial_ends_at": trial_ends,
            },
            {
                "email": "trial.two@ngo.example",
                "display_name": "Trial Two",
                "organisation": "Relief Partners",
                "tier": DataTier.PROFESSIONAL,
                "status": SubscriptionStatus.TRIAL,
                "billing_plan": BillingPlan.ANNUAL,
                "trial_started_at": today,
                "trial_ends_at": trial_ends,
            },
            {
                "email": "active.monthly@ngo.example",
                "display_name": "Active Monthly",
                "organisation": "Food Security Lab",
                "tier": DataTier.PROFESSIONAL,
                "status": SubscriptionStatus.ACTIVE,
                "billing_plan": BillingPlan.MONTHLY,
                "trial_started_at": today - timedelta(days=20),
                "trial_ends_at": today - timedelta(days=6),
                "activated_at": datetime.now(UTC) - timedelta(days=5),
                "usage_exports": 1,
            },
            {
                "email": "active.annual@ngo.example",
                "display_name": "Active Annual",
                "organisation": "Policy Research Group",
                "tier": DataTier.PROFESSIONAL,
                "status": SubscriptionStatus.ACTIVE,
                "billing_plan": BillingPlan.ANNUAL,
                "trial_started_at": today - timedelta(days=30),
                "trial_ends_at": today - timedelta(days=16),
                "activated_at": datetime.now(UTC) - timedelta(days=15),
            },
            {
                "email": "enterprise@ngo.example",
                "display_name": "Enterprise Contact",
                "organisation": "Large Humanitarian Org",
                "tier": DataTier.ENTERPRISE,
                "status": SubscriptionStatus.ACTIVE,
                "billing_plan": BillingPlan.ANNUAL,
                "trial_started_at": today - timedelta(days=40),
                "trial_ends_at": today - timedelta(days=26),
                "activated_at": datetime.now(UTC) - timedelta(days=25),
            },
            {
                "email": "cancelled@ngo.example",
                "display_name": "Cancelled User",
                "organisation": "Former Client",
                "tier": DataTier.PROFESSIONAL,
                "status": SubscriptionStatus.CANCELLED,
                "billing_plan": BillingPlan.MONTHLY,
                "trial_started_at": today - timedelta(days=60),
                "trial_ends_at": today - timedelta(days=46),
                "activated_at": datetime.now(UTC) - timedelta(days=45),
                "cancelled_at": datetime.now(UTC) - timedelta(days=10),
            },
        ]

        seeded_user_ids: list[tuple[str, object]] = []
        for account in demo_accounts:
            email = str(account["email"])
            existing = await users.get_by_email(email)
            if existing is not None:
                print(f"subscriber = {email}")
                seeded_user_ids.append((email, existing.id))
                continue

            user_id = uuid4()
            user = User(
                id=user_id,
                email=email,
                password_hash=password_hash,
                display_name=str(account["display_name"]),
                role=UserRole.SUBSCRIBER,
                status=UserStatus.ACTIVE,
                auth_version=1,
                failed_login_attempts=0,
            )
            subscription = Subscription(
                id=uuid4(),
                user_id=user_id,
                organisation=str(account["organisation"]),
                tier=account["tier"],  # type: ignore[arg-type]
                status=account["status"],  # type: ignore[arg-type]
                billing_plan=account["billing_plan"],  # type: ignore[arg-type]
                trial_started_at=account.get("trial_started_at"),  # type: ignore[arg-type]
                trial_ends_at=account.get("trial_ends_at"),  # type: ignore[arg-type]
                activated_at=account.get("activated_at"),  # type: ignore[arg-type]
                cancelled_at=account.get("cancelled_at"),  # type: ignore[arg-type]
                language=SubscriberLanguage.EN,
            )
            users.add(user)
            session.add(subscription)
            await session.flush()

            usage_exports = account.get("usage_exports")
            if isinstance(usage_exports, int) and usage_exports > 0:
                session.add(
                    SubscriptionUsage(
                        id=uuid4(),
                        user_id=user_id,
                        usage_date=today,
                        exports_count=usage_exports,
                    )
                )

            seeded_user_ids.append((email, user_id))
            print(f"subscriber + {email}")

        if seeded_user_ids:
            active_user_id = seeded_user_ids[2][1]
            session.add_all(
                [
                    PaymentTransaction(
                        id=uuid4(),
                        user_id=active_user_id,
                        amount_etb=Decimal(settings.pro_monthly_etb),
                        billing_plan=BillingPlan.MONTHLY,
                        status=PaymentStatus.PENDING,
                        tx_ref="waga-demo-pending001",
                        checkout_url="https://checkout.chapa.co/pay/demo-pending",
                    ),
                    PaymentTransaction(
                        id=uuid4(),
                        user_id=active_user_id,
                        amount_etb=Decimal(settings.pro_monthly_etb),
                        billing_plan=BillingPlan.MONTHLY,
                        status=PaymentStatus.SUCCEEDED,
                        tx_ref="waga-demo-success001",
                        chapa_ref_id="CHAPA-DEMO-SUCCESS",
                        checkout_url="https://checkout.chapa.co/pay/demo-success",
                        confirmed_at=datetime.now(UTC),
                    ),
                    PaymentTransaction(
                        id=uuid4(),
                        user_id=active_user_id,
                        amount_etb=Decimal(settings.pro_annual_etb),
                        billing_plan=BillingPlan.ANNUAL,
                        status=PaymentStatus.FAILED,
                        tx_ref="waga-demo-failed001",
                        checkout_url="https://checkout.chapa.co/pay/demo-failed",
                        failure_reason="chapa_payment_failed",
                        confirmed_at=datetime.now(UTC),
                    ),
                ]
            )
            print("payments + demo Chapa transactions")

        session.add_all(
            [
                EnterpriseEnquiry(
                    id=uuid4(),
                    name="Sara Bekele",
                    organisation="Field Research Unit",
                    email="sara@research.example",
                    use_case="Monthly MEB reporting for five woredas.",
                    update_frequency=UpdateFrequency.MONTHLY,
                    status=EnterpriseEnquiryStatus.NEW,
                ),
                EnterpriseEnquiry(
                    id=uuid4(),
                    name="Daniel Haile",
                    organisation="AgriFin Co",
                    email="daniel@agrifin.example",
                    use_case="API access for inflation dashboards.",
                    update_frequency=UpdateFrequency.WEEKLY,
                    status=EnterpriseEnquiryStatus.CONTACTED,
                ),
            ]
        )
        await session.commit()
        print("enterprise enquiries + demo records")
        print(f"Demo subscriber password for all seeded accounts: {DEMO_PASSWORD}")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
