"""Add AI assist fields on pending submission verifications.

Revision ID: 20260725_0008
Revises: 20260725_0007
Create Date: 2026-07-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260725_0008"
down_revision: str | Sequence[str] | None = "20260725_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "submission_verifications",
        sa.Column("ai_verdict", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "submission_verifications",
        sa.Column("ai_confidence", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "submission_verifications",
        sa.Column("ai_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "submission_verifications",
        sa.Column("ai_model", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "submission_verifications",
        sa.Column("ai_checked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "submission_verifications_ai_verdict",
        "submission_verifications",
        "ai_verdict IS NULL OR ai_verdict IN ('accept', 'hold', 'flag')",
    )
    op.create_check_constraint(
        "submission_verifications_ai_confidence",
        "submission_verifications",
        "ai_confidence IS NULL OR ai_confidence IN ('high', 'medium', 'low')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "submission_verifications_ai_confidence",
        "submission_verifications",
        type_="check",
    )
    op.drop_constraint(
        "submission_verifications_ai_verdict",
        "submission_verifications",
        type_="check",
    )
    op.drop_column("submission_verifications", "ai_checked_at")
    op.drop_column("submission_verifications", "ai_model")
    op.drop_column("submission_verifications", "ai_reason")
    op.drop_column("submission_verifications", "ai_confidence")
    op.drop_column("submission_verifications", "ai_verdict")
