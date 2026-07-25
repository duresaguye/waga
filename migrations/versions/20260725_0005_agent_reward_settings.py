"""Admin reward settings (score → birr) and redeem payout queue.

Revision ID: 20260725_0005
Revises: 20260725_0004
Create Date: 2026-07-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260725_0005"
down_revision: str | Sequence[str] | None = "20260725_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_reward_settings",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("birr_per_point", sa.Numeric(12, 4), server_default="1", nullable=False),
        sa.Column("redeem_min_points", sa.Integer(), server_default="50", nullable=False),
        sa.Column("currency_code", sa.String(length=8), server_default="ETB", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("birr_per_point > 0", name="birr_per_point_positive"),
        sa.CheckConstraint("redeem_min_points > 0", name="redeem_min_points_positive"),
        sa.PrimaryKeyConstraint("id", name="pk_agent_reward_settings"),
    )

    op.create_table(
        "agent_redeem_requests",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("contributor_id", sa.Uuid(), nullable=False),
        sa.Column("telegram_id", sa.String(length=64), nullable=True),
        sa.Column("points_redeemed", sa.Integer(), nullable=False),
        sa.Column("birr_per_point", sa.Numeric(12, 4), nullable=False),
        sa.Column("birr_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency_code", sa.String(length=8), server_default="ETB", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("admin_note", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("points_redeemed > 0", name="points_redeemed_positive"),
        sa.CheckConstraint("birr_amount > 0", name="birr_amount_positive"),
        sa.ForeignKeyConstraint(
            ["contributor_id"],
            ["contributors.id"],
            name="fk_agent_redeem_requests_contributor_id_contributors",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_agent_redeem_requests"),
    )
    op.create_index(
        "ix_agent_redeem_requests_contributor_id",
        "agent_redeem_requests",
        ["contributor_id"],
    )

    # Default: 1 point = 2 birr, redeem from 50 points → 100 ETB
    op.execute(
        sa.text(
            "INSERT INTO agent_reward_settings "
            "(birr_per_point, redeem_min_points, currency_code, is_active) "
            "VALUES (2, 50, 'ETB', true)"
        )
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_redeem_requests_contributor_id",
        table_name="agent_redeem_requests",
    )
    op.drop_table("agent_redeem_requests")
    op.drop_table("agent_reward_settings")
