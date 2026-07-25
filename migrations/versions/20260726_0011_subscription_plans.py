"""Subscription plan catalog for admin CRUD and checkout pricing.

Revision ID: 20260726_0011
Revises: 20260726_0010
Create Date: 2026-07-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260726_0011"
down_revision: str | Sequence[str] | None = "20260726_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("tier", sa.String(length=16), nullable=False),
        sa.Column("billing_plan", sa.String(length=16), nullable=True),
        sa.Column("name_en", sa.String(length=160), nullable=False),
        sa.Column("name_am", sa.String(length=160), nullable=False),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("description_am", sa.Text(), nullable=True),
        sa.Column("amount_etb", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("trial_days", sa.Integer(), nullable=True),
        sa.Column("exports_per_day", sa.Integer(), nullable=True),
        sa.Column("history_days", sa.Integer(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "is_public",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            server_default=sa.text("0"),
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
        sa.CheckConstraint("btrim(code) <> ''", name="subscription_plan_code_not_blank"),
        sa.CheckConstraint("amount_etb > 0", name="subscription_plan_amount_positive"),
        sa.CheckConstraint(
            "tier IN ('public', 'professional', 'enterprise')",
            name="subscription_plan_tier",
        ),
        sa.CheckConstraint(
            "billing_plan IS NULL OR billing_plan IN ('monthly', 'annual')",
            name="subscription_plan_billing_plan",
        ),
        sa.CheckConstraint(
            "trial_days IS NULL OR trial_days >= 0",
            name="subscription_plan_trial_days_non_negative",
        ),
        sa.CheckConstraint(
            "exports_per_day IS NULL OR exports_per_day >= 0",
            name="subscription_plan_exports_non_negative",
        ),
        sa.CheckConstraint(
            "history_days IS NULL OR history_days >= 0",
            name="subscription_plan_history_non_negative",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_subscription_plans_code"),
    )
    op.create_index(
        "ix_subscription_plans_active_public",
        "subscription_plans",
        ["is_active", "is_public", "sort_order"],
    )

    op.add_column(
        "subscriptions",
        sa.Column("plan_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_subscriptions_plan_id",
        "subscriptions",
        "subscription_plans",
        ["plan_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "payment_transactions",
        sa.Column("plan_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_payment_transactions_plan_id",
        "payment_transactions",
        "subscription_plans",
        ["plan_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute(
        sa.text(
            """
            INSERT INTO subscription_plans (
                code, tier, billing_plan, name_en, name_am,
                description_en, description_am, amount_etb,
                trial_days, exports_per_day, history_days,
                is_active, is_public, sort_order
            ) VALUES
            (
                'professional_monthly', 'professional', 'monthly',
                'Professional Monthly', 'Professional Monthly',
                'Full market intelligence with monthly billing',
                'Full market intelligence with monthly billing',
                1600, 14, 1, 30, true, true, 1
            ),
            (
                'professional_annual', 'professional', 'annual',
                'Professional Annual', 'Professional Annual',
                'Full market intelligence with annual billing',
                'Full market intelligence with annual billing',
                16000, 14, 1, 90, true, true, 2
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_constraint("fk_payment_transactions_plan_id", "payment_transactions", type_="foreignkey")
    op.drop_column("payment_transactions", "plan_id")
    op.drop_constraint("fk_subscriptions_plan_id", "subscriptions", type_="foreignkey")
    op.drop_column("subscriptions", "plan_id")
    op.drop_index("ix_subscription_plans_active_public", table_name="subscription_plans")
    op.drop_table("subscription_plans")
