"""Subscription tiers, usage tracking, demo Telebirr payments, enterprise enquiries.

Revision ID: 20260725_0009
Revises: 20260725_0008
Create Date: 2026-07-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260725_0009"
down_revision: str | Sequence[str] | None = "20260725_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("user_role", "users", type_="check")
    op.create_check_constraint(
        "user_role",
        "users",
        "role IN ('admin', 'operator', 'viewer', 'contributor', 'subscriber')",
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("organisation", sa.String(length=160), nullable=True),
        sa.Column(
            "tier",
            sa.String(length=16),
            server_default="professional",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default="trial",
            nullable=False,
        ),
        sa.Column("billing_plan", sa.String(length=16), nullable=True),
        sa.Column("trial_started_at", sa.Date(), nullable=True),
        sa.Column("trial_ends_at", sa.Date(), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "language",
            sa.String(length=8),
            server_default="en",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "tier IN ('public', 'professional', 'enterprise')",
            name="data_tier",
        ),
        sa.CheckConstraint(
            "status IN ('none', 'trial', 'active', 'cancelled', 'expired')",
            name="subscription_status",
        ),
        sa.CheckConstraint(
            "billing_plan IS NULL OR billing_plan IN ('monthly', 'annual')",
            name="billing_plan",
        ),
        sa.CheckConstraint(
            "language IN ('en', 'am')",
            name="subscriber_language",
        ),
        sa.CheckConstraint(
            "trial_ends_at IS NULL OR trial_started_at IS NULL OR trial_ends_at >= trial_started_at",
            name="subscription_trial_window_valid",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_subscriptions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_subscriptions"),
        sa.UniqueConstraint("user_id", name="uq_subscriptions_user_id"),
    )

    op.create_table(
        "subscription_usage",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("exports_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_subscription_usage_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_subscription_usage"),
        sa.UniqueConstraint("user_id", "usage_date", name="uq_subscription_usage_user_date"),
    )

    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "provider",
            sa.String(length=16),
            server_default="telebirr",
            nullable=False,
        ),
        sa.Column("amount_etb", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("billing_plan", sa.String(length=16), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("telebirr_reference", sa.String(length=64), nullable=False),
        sa.Column("demo_phone", sa.String(length=32), nullable=True),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount_etb > 0", name="payment_amount_positive"),
        sa.CheckConstraint(
            "provider IN ('telebirr')",
            name="payment_provider",
        ),
        sa.CheckConstraint(
            "billing_plan IN ('monthly', 'annual')",
            name="payment_transactions_billing_plan",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed')",
            name="payment_status",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_payment_transactions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_payment_transactions"),
        sa.UniqueConstraint("telebirr_reference", name="uq_payment_transactions_telebirr_reference"),
    )
    op.create_index(
        "ix_payment_transactions_user_id",
        "payment_transactions",
        ["user_id"],
    )
    op.create_index(
        "ix_payment_transactions_status",
        "payment_transactions",
        ["status"],
    )

    op.create_table(
        "enterprise_enquiries",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("organisation", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("use_case", sa.Text(), nullable=False),
        sa.Column("update_frequency", sa.String(length=16), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default="new",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("btrim(name) <> ''", name="enterprise_enquiry_name_not_blank"),
        sa.CheckConstraint("btrim(organisation) <> ''", name="enterprise_enquiry_org_not_blank"),
        sa.CheckConstraint("btrim(email) <> ''", name="enterprise_enquiry_email_not_blank"),
        sa.CheckConstraint(
            "update_frequency IN ('daily', 'weekly', 'monthly')",
            name="update_frequency",
        ),
        sa.CheckConstraint(
            "status IN ('new', 'contacted', 'qualified', 'contracted', 'closed')",
            name="enterprise_enquiry_status",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_enterprise_enquiries"),
    )


def downgrade() -> None:
    op.drop_table("enterprise_enquiries")
    op.drop_index("ix_payment_transactions_status", table_name="payment_transactions")
    op.drop_index("ix_payment_transactions_user_id", table_name="payment_transactions")
    op.drop_table("payment_transactions")
    op.drop_table("subscription_usage")
    op.drop_table("subscriptions")

    op.drop_constraint("user_role", "users", type_="check")
    op.create_check_constraint(
        "user_role",
        "users",
        "role IN ('admin', 'operator', 'viewer', 'contributor')",
    )
