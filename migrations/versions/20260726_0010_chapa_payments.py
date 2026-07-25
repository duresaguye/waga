"""Migrate payment_transactions from demo Telebirr to Chapa.

Revision ID: 20260726_0010
Revises: 20260725_0009
Create Date: 2026-07-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260726_0010"
down_revision: str | Sequence[str] | None = "20260725_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "payment_transactions",
        "telebirr_reference",
        new_column_name="tx_ref",
    )
    op.drop_constraint(
        "uq_payment_transactions_telebirr_reference",
        "payment_transactions",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_payment_transactions_tx_ref",
        "payment_transactions",
        ["tx_ref"],
    )

    op.add_column(
        "payment_transactions",
        sa.Column("chapa_ref_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "payment_transactions",
        sa.Column("checkout_url", sa.Text(), nullable=True),
    )
    op.drop_column("payment_transactions", "demo_phone")

    op.execute("UPDATE payment_transactions SET provider = 'chapa' WHERE provider = 'telebirr'")

    op.drop_constraint("payment_provider", "payment_transactions", type_="check")
    op.create_check_constraint(
        "payment_provider",
        "payment_transactions",
        "provider IN ('chapa')",
    )
    op.execute(
        "ALTER TABLE payment_transactions "
        "ALTER COLUMN provider SET DEFAULT 'chapa'"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE payment_transactions "
        "ALTER COLUMN provider SET DEFAULT 'telebirr'"
    )
    op.drop_constraint("payment_provider", "payment_transactions", type_="check")
    op.create_check_constraint(
        "payment_provider",
        "payment_transactions",
        "provider IN ('telebirr')",
    )
    op.execute("UPDATE payment_transactions SET provider = 'telebirr' WHERE provider = 'chapa'")

    op.add_column(
        "payment_transactions",
        sa.Column("demo_phone", sa.String(length=32), nullable=True),
    )
    op.drop_column("payment_transactions", "checkout_url")
    op.drop_column("payment_transactions", "chapa_ref_id")

    op.drop_constraint("uq_payment_transactions_tx_ref", "payment_transactions", type_="unique")
    op.alter_column(
        "payment_transactions",
        "tx_ref",
        new_column_name="telebirr_reference",
    )
    op.create_unique_constraint(
        "uq_payment_transactions_telebirr_reference",
        "payment_transactions",
        ["telebirr_reference"],
    )
