from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
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
from app.models.enums import (
    InputMode,
    LicenceClass,
    ParseMethod,
    ParseStatus,
    SubmissionSource,
    enum_values,
)


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint(
            "contributor_id",
            "client_submission_id",
            name="uq_submissions_contributor_client_id",
        ),
        CheckConstraint(
            "price_raw IS NULL OR price_raw > 0",
            name="price_raw_positive",
        ),
        CheckConstraint(
            "price_canonical IS NULL OR price_canonical > 0",
            name="price_canonical_positive",
        ),
        CheckConstraint(
            "parse_status <> 'parsed' OR "
            "(market_id IS NOT NULL AND commodity_id IS NOT NULL "
            "AND price_canonical IS NOT NULL AND unit_canonical IS NOT NULL)",
            name="parsed_fields_present",
        ),
        CheckConstraint(
            "contributor_id IS NOT NULL OR source IN ('scraped', 'seed')",
            name="contributor_required_for_direct_sources",
        ),
        Index(
            "ix_submissions_market_commodity_received_at",
            "market_id",
            "commodity_id",
            text("received_at DESC"),
        ),
        Index("ix_submissions_contributor_id", "contributor_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    client_submission_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    contributor_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("contributors.id", ondelete="RESTRICT"),
    )
    market_id: Mapped[int | None] = mapped_column(
        SmallInteger,
        ForeignKey("markets.id", ondelete="RESTRICT"),
    )
    commodity_id: Mapped[int | None] = mapped_column(
        SmallInteger,
        ForeignKey("commodities.id", ondelete="RESTRICT"),
    )
    price_raw: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    unit_raw: Mapped[str | None] = mapped_column(String(32))
    price_canonical: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    unit_canonical: Mapped[str | None] = mapped_column(String(32))
    raw_text: Mapped[str | None] = mapped_column(Text)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    source: Mapped[SubmissionSource] = mapped_column(
        SqlEnum(
            SubmissionSource,
            name="submission_source",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
    )
    licence_class: Mapped[LicenceClass] = mapped_column(
        SqlEnum(
            LicenceClass,
            name="licence_class",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=32,
        ),
        nullable=False,
        default=LicenceClass.INTERNAL_ONLY,
        server_default=LicenceClass.INTERNAL_ONLY.value,
    )
    parse_status: Mapped[ParseStatus] = mapped_column(
        SqlEnum(
            ParseStatus,
            name="submission_parse_status",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
    )
    parse_method: Mapped[ParseMethod] = mapped_column(
        SqlEnum(
            ParseMethod,
            name="submission_parse_method",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
    )
    input_mode: Mapped[InputMode] = mapped_column(
        SqlEnum(
            InputMode,
            name="submission_input_mode",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
        default=InputMode.REST,
        server_default=InputMode.REST.value,
    )
