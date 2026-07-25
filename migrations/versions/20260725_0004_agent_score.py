"""Add agent score fields, invite codes, and score event ledger.

Revision ID: 20260725_0004
Revises: 20260725_0003
Create Date: 2026-07-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260725_0004"
down_revision: str | Sequence[str] | None = "20260725_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "contributors",
        sa.Column("is_agent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "contributors",
        sa.Column("reputation_score", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "contributors",
        sa.Column("pending_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "contributors",
        sa.Column("accepted_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "contributors",
        sa.Column("flagged_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "contributors",
        sa.Column("redeemed_total", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "contributors",
        sa.Column("banned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "contributors",
        sa.Column("ban_reason", sa.String(length=255), nullable=True),
    )
    op.create_check_constraint(
        "reputation_score_bounds",
        "contributors",
        "reputation_score >= -10000",
    )
    op.create_check_constraint(
        "pending_count_nonnegative",
        "contributors",
        "pending_count >= 0",
    )
    op.create_check_constraint(
        "accepted_count_nonnegative",
        "contributors",
        "accepted_count >= 0",
    )
    op.create_check_constraint(
        "flagged_count_nonnegative",
        "contributors",
        "flagged_count >= 0",
    )
    op.create_check_constraint(
        "redeemed_total_nonnegative",
        "contributors",
        "redeemed_total >= 0",
    )

    op.create_table(
        "agent_invite_codes",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("max_uses", sa.Integer(), server_default="0", nullable=False),
        sa.Column("uses_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("btrim(code) <> ''", name="agent_invite_code_not_blank"),
        sa.CheckConstraint("max_uses >= 0", name="agent_invite_max_uses_nonnegative"),
        sa.CheckConstraint("uses_count >= 0", name="agent_invite_uses_nonnegative"),
        sa.PrimaryKeyConstraint("id", name="pk_agent_invite_codes"),
        sa.UniqueConstraint("code", name="uq_agent_invite_codes_code"),
    )

    op.create_table(
        "agent_score_events",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("contributor_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("points_delta", sa.Integer(), nullable=False),
        sa.Column("score_after", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "event_type IN ("
            "'pending_submit', 'accepted', 'flagged', 'redeem', 'activate', 'ban')",
            name="agent_score_event_type",
        ),
        sa.ForeignKeyConstraint(
            ["contributor_id"],
            ["contributors.id"],
            name="fk_agent_score_events_contributor_id_contributors",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_agent_score_events"),
    )
    op.create_index(
        "ix_agent_score_events_contributor_id",
        "agent_score_events",
        ["contributor_id"],
    )

    # Seed default invite code for Addis pilot.
    op.execute(
        sa.text(
            "INSERT INTO agent_invite_codes (code, is_active, max_uses, uses_count) "
            "VALUES ('waga-addis-01', true, 0, 0) "
            "ON CONFLICT (code) DO NOTHING"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_agent_score_events_contributor_id", table_name="agent_score_events")
    op.drop_table("agent_score_events")
    op.drop_table("agent_invite_codes")
    op.drop_constraint("redeemed_total_nonnegative", "contributors", type_="check")
    op.drop_constraint("flagged_count_nonnegative", "contributors", type_="check")
    op.drop_constraint("accepted_count_nonnegative", "contributors", type_="check")
    op.drop_constraint("pending_count_nonnegative", "contributors", type_="check")
    op.drop_constraint("reputation_score_bounds", "contributors", type_="check")
    op.drop_column("contributors", "ban_reason")
    op.drop_column("contributors", "banned")
    op.drop_column("contributors", "redeemed_total")
    op.drop_column("contributors", "flagged_count")
    op.drop_column("contributors", "accepted_count")
    op.drop_column("contributors", "pending_count")
    op.drop_column("contributors", "reputation_score")
    op.drop_column("contributors", "is_agent")
