"""Add custom JWT authentication tables.

Revision ID: 20260725_0002
Revises: 20260725_0001
Create Date: 2026-07-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260725_0002"
down_revision: str | Sequence[str] | None = "20260725_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=True),
        sa.Column(
            "role",
            sa.String(length=16),
            server_default=sa.text("'contributor'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "auth_version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "failed_login_attempts",
            sa.SmallInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "password_changed_at",
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("auth_version > 0", name="auth_version_positive"),
        sa.CheckConstraint("btrim(email) <> ''", name="email_not_blank"),
        sa.CheckConstraint("email = lower(email)", name="email_normalized"),
        sa.CheckConstraint(
            "failed_login_attempts >= 0",
            name="failed_attempts_nonnegative",
        ),
        sa.CheckConstraint(
            "role IN ('admin', 'operator', 'viewer', 'contributor')",
            name="user_role",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'disabled')",
            name="user_status",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.add_column("contributors", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_contributors_user_id_users",
        "contributors",
        "users",
        ["user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_contributors_user_id",
        "contributors",
        ["user_id"],
    )

    op.create_table(
        "auth_sessions",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "session_family_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_session_id", sa.Uuid(), nullable=True),
        sa.CheckConstraint(
            "char_length(refresh_token_hash) = 64",
            name="refresh_hash_length",
        ),
        sa.CheckConstraint("expires_at > created_at", name="valid_expiry"),
        sa.ForeignKeyConstraint(
            ["replaced_by_session_id"],
            ["auth_sessions.id"],
            name="fk_auth_sessions_replaced_by_session_id_auth_sessions",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_auth_sessions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_auth_sessions"),
        sa.UniqueConstraint(
            "refresh_token_hash",
            name="uq_auth_sessions_refresh_token_hash",
        ),
    )
    op.create_index(
        "ix_auth_sessions_session_family_id",
        "auth_sessions",
        ["session_family_id"],
        unique=False,
    )
    op.create_index(
        "ix_auth_sessions_user_id_revoked_at",
        "auth_sessions",
        ["user_id", "revoked_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_auth_sessions_user_id_revoked_at",
        table_name="auth_sessions",
    )
    op.drop_index(
        "ix_auth_sessions_session_family_id",
        table_name="auth_sessions",
    )
    op.drop_table("auth_sessions")

    op.drop_constraint(
        "uq_contributors_user_id",
        "contributors",
        type_="unique",
    )
    op.drop_constraint(
        "fk_contributors_user_id_users",
        "contributors",
        type_="foreignkey",
    )
    op.drop_column("contributors", "user_id")
    op.drop_table("users")
