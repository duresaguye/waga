"""Allow telegram input_mode on submissions.

Revision ID: 20260725_0007
Revises: 20260725_0006
Create Date: 2026-07-25

"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260725_0007"
down_revision: str | Sequence[str] | None = "20260725_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("submission_input_mode", "submissions", type_="check")
    op.create_check_constraint(
        "submission_input_mode",
        "submissions",
        "input_mode IN ('rest', 'telegram')",
    )


def downgrade() -> None:
    op.drop_constraint("submission_input_mode", "submissions", type_="check")
    op.create_check_constraint(
        "submission_input_mode",
        "submissions",
        "input_mode IN ('rest')",
    )
