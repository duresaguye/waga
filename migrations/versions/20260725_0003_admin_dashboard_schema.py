"""Add admin dashboard schema.

 commodity hints, contributor fields, audit log, rate limits, invite tokens.

Revision ID: 20260725_0003
Revises: 20260725_0002
Create Date: 2026-07-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260725_0003"
down_revision: str | Sequence[str] | None = "20260725_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -- commodity_synonyms: add is_active ----------------------------------------
    op.add_column(
        "commodity_synonyms",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    # -- commodities: add allow_conversion, price hints ---------------------------
    op.add_column(
        "commodities",
        sa.Column(
            "allow_conversion",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "commodities",
        sa.Column("price_hint_low", sa.Numeric(18, 4), nullable=True),
    )
    op.add_column(
        "commodities",
        sa.Column("price_hint_high", sa.Numeric(18, 4), nullable=True),
    )

    # -- contributors: add telegram_id, market_id ---------------------------------
    op.add_column(
        "contributors",
        sa.Column("telegram_id", sa.String(64), nullable=True),
    )
    op.create_unique_constraint(
        "uq_contributors_telegram_id",
        "contributors",
        ["telegram_id"],
    )
    op.add_column(
        "contributors",
        sa.Column("market_id", sa.SmallInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_contributors_market_id_markets",
        "contributors",
        "markets",
        ["market_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # -- audit_log ----------------------------------------------------------------
    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("actor_user_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_audit_log_actor_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_log"),
    )
    op.create_index(
        "ix_audit_log_actor_user_id",
        "audit_log",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_log_created_at",
        "audit_log",
        [sa.text("created_at DESC")],
        unique=False,
    )

    # -- rate_limit_events --------------------------------------------------------
    op.create_table(
        "rate_limit_events",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("contributor_id", sa.Uuid(), nullable=False),
        sa.Column("rule", sa.String(64), nullable=False),
        sa.Column("market_id", sa.SmallInteger(), nullable=True),
        sa.Column("commodity_id", sa.SmallInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["contributor_id"],
            ["contributors.id"],
            name="fk_rate_limit_events_contributor_id_contributors",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["market_id"],
            ["markets.id"],
            name="fk_rate_limit_events_market_id_markets",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["commodity_id"],
            ["commodities.id"],
            name="fk_rate_limit_events_commodity_id_commodities",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_rate_limit_events"),
    )
    op.create_index(
        "ix_rate_limit_events_contributor_id",
        "rate_limit_events",
        ["contributor_id"],
        unique=False,
    )
    op.create_index(
        "ix_rate_limit_events_created_at",
        "rate_limit_events",
        [sa.text("created_at DESC")],
        unique=False,
    )

    # -- invite_tokens ------------------------------------------------------------
    op.create_table(
        "invite_tokens",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(token_hash) = 64",
            name="invite_token_hash_length",
        ),
        sa.CheckConstraint("expires_at > created_at", name="invite_valid_expiry"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_invite_tokens_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_invite_tokens"),
        sa.UniqueConstraint("token_hash", name="uq_invite_tokens_token_hash"),
    )
    op.create_index(
        "ix_invite_tokens_user_id",
        "invite_tokens",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_invite_tokens_user_id", table_name="invite_tokens")
    op.drop_table("invite_tokens")

    op.drop_index("ix_rate_limit_events_created_at", table_name="rate_limit_events")
    op.drop_index("ix_rate_limit_events_contributor_id", table_name="rate_limit_events")
    op.drop_table("rate_limit_events")

    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_actor_user_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_constraint(
        "fk_contributors_market_id_markets",
        "contributors",
        type_="foreignkey",
    )
    op.drop_column("contributors", "market_id")
    op.drop_constraint(
        "uq_contributors_telegram_id",
        "contributors",
        type_="unique",
    )
    op.drop_column("contributors", "telegram_id")

    op.drop_column("commodities", "price_hint_high")
    op.drop_column("commodities", "price_hint_low")
    op.drop_column("commodities", "allow_conversion")

    op.drop_column("commodity_synonyms", "is_active")
