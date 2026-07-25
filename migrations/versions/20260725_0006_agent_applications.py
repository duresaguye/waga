"""Agent applications (apply → admin approve) + contributor contact fields.

Revision ID: 20260725_0006
Revises: 20260725_0005
Create Date: 2026-07-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260725_0006"
down_revision: str | Sequence[str] | None = "20260725_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("contributors", sa.Column("full_name", sa.String(length=120), nullable=True))
    op.add_column("contributors", sa.Column("phone_number", sa.String(length=32), nullable=True))
    op.add_column("contributors", sa.Column("city", sa.String(length=80), nullable=True))

    op.create_table(
        "agent_applications",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("telegram_id", sa.String(length=64), nullable=False),
        sa.Column("telegram_username", sa.String(length=64), nullable=True),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("city", sa.String(length=80), nullable=False),
        sa.Column("subcity", sa.String(length=80), nullable=True),
        sa.Column("preferred_market_code", sa.String(length=64), nullable=False),
        sa.Column("visit_frequency", sa.String(length=64), nullable=False),
        sa.Column("languages", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "consent_honest_reporting",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("review_note", sa.String(length=255), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("contributor_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("btrim(full_name) <> ''", name="agent_app_full_name_not_blank"),
        sa.CheckConstraint("btrim(phone_number) <> ''", name="agent_app_phone_not_blank"),
        sa.CheckConstraint("btrim(city) <> ''", name="agent_app_city_not_blank"),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="agent_application_status",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
            name="fk_agent_applications_reviewed_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["contributor_id"],
            ["contributors.id"],
            name="fk_agent_applications_contributor_id_contributors",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_agent_applications"),
    )
    op.create_index(
        "ix_agent_applications_telegram_id",
        "agent_applications",
        ["telegram_id"],
    )
    op.create_index(
        "ix_agent_applications_status",
        "agent_applications",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_applications_status", table_name="agent_applications")
    op.drop_index("ix_agent_applications_telegram_id", table_name="agent_applications")
    op.drop_table("agent_applications")
    op.drop_column("contributors", "city")
    op.drop_column("contributors", "phone_number")
    op.drop_column("contributors", "full_name")
