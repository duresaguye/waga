from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import IndexStatus, enum_values


class IndexValue(Base):
    __tablename__ = "index_values"
    __table_args__ = (
        UniqueConstraint(
            "trigger_verification_id",
            "method_version",
            name="uq_index_values_trigger_method",
        ),
        CheckConstraint("window_start < window_end", name="valid_window"),
        CheckConstraint("n_submissions >= 0", name="submission_count_nonnegative"),
        CheckConstraint("n_contributors >= 0", name="contributor_count_nonnegative"),
        CheckConstraint(
            "(status = 'published' AND value IS NOT NULL) "
            "OR (status = 'insufficient_data' AND value IS NULL)",
            name="status_matches_value",
        ),
        CheckConstraint("btrim(unit) <> ''", name="unit_not_blank"),
        CheckConstraint("btrim(method_version) <> ''", name="method_version_not_blank"),
        Index(
            "ix_index_values_market_commodity_computed_at",
            "market_id",
            "commodity_id",
            text("computed_at DESC"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    market_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("markets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    commodity_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("commodities.id", ondelete="RESTRICT"),
        nullable=False,
    )
    trigger_verification_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "submission_verifications.id",
            name="fk_index_values_trigger_verification",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    method_version: Mapped[str] = mapped_column(String(32), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    n_submissions: Mapped[int] = mapped_column(Integer, nullable=False)
    n_contributors: Mapped[int] = mapped_column(Integer, nullable=False)
    source_mix: Mapped[dict[str, int]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    status: Mapped[IndexStatus] = mapped_column(
        SqlEnum(
            IndexStatus,
            name="index_status",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=24,
        ),
        nullable=False,
    )
