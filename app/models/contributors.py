from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
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
from app.models.enums import AgentScoreEventType, ContributorKind, enum_values


class Contributor(Base):
    __tablename__ = "contributors"
    __table_args__ = (
        CheckConstraint("reputation_score >= -10000", name="reputation_score_bounds"),
        CheckConstraint("pending_count >= 0", name="pending_count_nonnegative"),
        CheckConstraint("accepted_count >= 0", name="accepted_count_nonnegative"),
        CheckConstraint("flagged_count >= 0", name="flagged_count_nonnegative"),
        CheckConstraint("redeemed_total >= 0", name="redeemed_total_nonnegative"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True,
    )
    external_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        unique=True,
    )
    kind: Mapped[ContributorKind] = mapped_column(
        SqlEnum(
            ContributorKind,
            name="contributor_kind",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
        default=ContributorKind.USER,
        server_default=ContributorKind.USER.value,
    )
    telegram_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    full_name: Mapped[str | None] = mapped_column(String(120))
    phone_number: Mapped[str | None] = mapped_column(String(32))
    city: Mapped[str | None] = mapped_column(String(80))
    market_id: Mapped[int | None] = mapped_column(
        SmallInteger,
        ForeignKey("markets.id", ondelete="SET NULL"),
    )
    is_agent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    reputation_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    pending_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    accepted_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    flagged_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    redeemed_total: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    banned: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    ban_reason: Mapped[str | None] = mapped_column(String(255))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class ContributorConsent(Base):
    __tablename__ = "contributor_consents"
    __table_args__ = (
        UniqueConstraint(
            "contributor_id",
            "consent_version",
            name="uq_contributor_consents_contributor_version",
        ),
        CheckConstraint("btrim(consent_version) <> ''", name="version_not_blank"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    contributor_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("contributors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    consent_version: Mapped[str] = mapped_column(String(64), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class AgentInviteCode(Base):
    __tablename__ = "agent_invite_codes"
    __table_args__ = (
        CheckConstraint("btrim(code) <> ''", name="agent_invite_code_not_blank"),
        CheckConstraint("max_uses >= 0", name="agent_invite_max_uses_nonnegative"),
        CheckConstraint("uses_count >= 0", name="agent_invite_uses_nonnegative"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    max_uses: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )  # 0 = unlimited
    uses_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class AgentScoreEvent(Base):
    __tablename__ = "agent_score_events"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    contributor_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("contributors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[AgentScoreEventType] = mapped_column(
        SqlEnum(
            AgentScoreEventType,
            name="agent_score_event_type",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=32,
        ),
        nullable=False,
    )
    points_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    score_after: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
