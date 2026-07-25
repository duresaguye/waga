from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import (
    BillingPlan,
    DataTier,
    EnterpriseEnquiryStatus,
    PaymentProvider,
    PaymentStatus,
    SubscriberLanguage,
    SubscriptionStatus,
    UpdateFrequency,
    enum_values,
)


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint(
            (
                "trial_ends_at IS NULL OR trial_started_at IS NULL "
                "OR trial_ends_at >= trial_started_at"
            ),
            name="subscription_trial_window_valid",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    organisation: Mapped[str | None] = mapped_column(String(160))
    tier: Mapped[DataTier] = mapped_column(
        SqlEnum(
            DataTier,
            name="data_tier",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
        default=DataTier.PROFESSIONAL,
        server_default=DataTier.PROFESSIONAL.value,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        SqlEnum(
            SubscriptionStatus,
            name="subscription_status",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
        default=SubscriptionStatus.TRIAL,
        server_default=SubscriptionStatus.TRIAL.value,
    )
    billing_plan: Mapped[BillingPlan | None] = mapped_column(
        SqlEnum(
            BillingPlan,
            name="billing_plan",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
    )
    trial_started_at: Mapped[date | None] = mapped_column(Date())
    trial_ends_at: Mapped[date | None] = mapped_column(Date())
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    language: Mapped[SubscriberLanguage] = mapped_column(
        SqlEnum(
            SubscriberLanguage,
            name="subscriber_language",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=8,
        ),
        nullable=False,
        default=SubscriberLanguage.EN,
        server_default=SubscriberLanguage.EN.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    plan_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="SET NULL"),
    )


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    __table_args__ = (
        CheckConstraint("btrim(code) <> ''", name="subscription_plan_code_not_blank"),
        CheckConstraint("amount_etb > 0", name="subscription_plan_amount_positive"),
        CheckConstraint(
            "trial_days IS NULL OR trial_days >= 0",
            name="subscription_plan_trial_days_non_negative",
        ),
        CheckConstraint(
            "exports_per_day IS NULL OR exports_per_day >= 0",
            name="subscription_plan_exports_non_negative",
        ),
        CheckConstraint(
            "history_days IS NULL OR history_days >= 0",
            name="subscription_plan_history_non_negative",
        ),
        Index("ix_subscription_plans_active_public", "is_active", "is_public", "sort_order"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    tier: Mapped[DataTier] = mapped_column(
        SqlEnum(
            DataTier,
            name="data_tier",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
    )
    billing_plan: Mapped[BillingPlan | None] = mapped_column(
        SqlEnum(
            BillingPlan,
            name="billing_plan",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
    )
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    name_am: Mapped[str] = mapped_column(String(160), nullable=False)
    description_en: Mapped[str | None] = mapped_column(Text())
    description_am: Mapped[str | None] = mapped_column(Text())
    amount_etb: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    trial_days: Mapped[int | None] = mapped_column()
    exports_per_day: Mapped[int | None] = mapped_column()
    history_days: Mapped[int | None] = mapped_column()
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    is_public: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SubscriptionUsage(Base):
    __tablename__ = "subscription_usage"
    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uq_subscription_usage_user_date"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    usage_date: Mapped[date] = mapped_column(Date(), nullable=False)
    exports_count: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    __table_args__ = (
        CheckConstraint("amount_etb > 0", name="payment_amount_positive"),
        Index("ix_payment_transactions_user_id", "user_id"),
        Index("ix_payment_transactions_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[PaymentProvider] = mapped_column(
        SqlEnum(
            PaymentProvider,
            name="payment_provider",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
        default=PaymentProvider.CHAPA,
        server_default=PaymentProvider.CHAPA.value,
    )
    amount_etb: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    billing_plan: Mapped[BillingPlan] = mapped_column(
        SqlEnum(
            BillingPlan,
            name="billing_plan",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
    )
    plan_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="SET NULL"),
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SqlEnum(
            PaymentStatus,
            name="payment_status",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
    )
    tx_ref: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    chapa_ref_id: Mapped[str | None] = mapped_column(String(64))
    checkout_url: Mapped[str | None] = mapped_column(Text())
    failure_reason: Mapped[str | None] = mapped_column(String(255))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class EnterpriseEnquiry(Base):
    __tablename__ = "enterprise_enquiries"
    __table_args__ = (
        CheckConstraint("btrim(name) <> ''", name="enterprise_enquiry_name_not_blank"),
        CheckConstraint("btrim(organisation) <> ''", name="enterprise_enquiry_org_not_blank"),
        CheckConstraint("btrim(email) <> ''", name="enterprise_enquiry_email_not_blank"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    organisation: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    use_case: Mapped[str] = mapped_column(Text(), nullable=False)
    update_frequency: Mapped[UpdateFrequency] = mapped_column(
        SqlEnum(
            UpdateFrequency,
            name="update_frequency",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
    )
    status: Mapped[EnterpriseEnquiryStatus] = mapped_column(
        SqlEnum(
            EnterpriseEnquiryStatus,
            name="enterprise_enquiry_status",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
        default=EnterpriseEnquiryStatus.NEW,
        server_default=EnterpriseEnquiryStatus.NEW.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
