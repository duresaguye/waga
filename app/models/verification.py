from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import ReviewOutcome, enum_values


class SubmissionVerification(Base):
    __tablename__ = "submission_verifications"
    __table_args__ = (
        CheckConstraint(
            "(outcome = 'pending' AND reviewer_label IS NULL) "
            "OR (outcome IN ('accepted', 'flagged') "
            "AND reviewer_label IS NOT NULL AND btrim(reviewer_label) <> '')",
            name="reviewer_required_for_final_outcome",
        ),
        CheckConstraint(
            "outcome <> 'flagged' OR (reason IS NOT NULL AND btrim(reason) <> '')",
            name="reason_required_when_flagged",
        ),
        UniqueConstraint(
            "submission_id",
            "outcome",
            name="uq_submission_verifications_submission_outcome",
        ),
        Index(
            "ix_submission_verifications_submission_created_at",
            "submission_id",
            text("created_at DESC"),
        ),
        Index(
            "uq_submission_verifications_one_final_outcome",
            "submission_id",
            unique=True,
            postgresql_where=text("outcome IN ('accepted', 'flagged')"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    submission_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("submissions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    outcome: Mapped[ReviewOutcome] = mapped_column(
        SqlEnum(
            ReviewOutcome,
            name="review_outcome",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
    )
    reviewer_label: Mapped[str | None] = mapped_column(String(120))
    reason_code: Mapped[str | None] = mapped_column(String(64))
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
