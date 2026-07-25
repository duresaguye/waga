from datetime import datetime
from uuid import UUID, uuid4

from enum import StrEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import enum_values


class AgentApplicationStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AgentApplication(Base):
    __tablename__ = "agent_applications"
    __table_args__ = (
        CheckConstraint("btrim(full_name) <> ''", name="agent_app_full_name_not_blank"),
        CheckConstraint("btrim(phone_number) <> ''", name="agent_app_phone_not_blank"),
        CheckConstraint("btrim(city) <> ''", name="agent_app_city_not_blank"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    telegram_id: Mapped[str] = mapped_column(String(64), nullable=False)
    telegram_username: Mapped[str | None] = mapped_column(String(64))
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False, default="Addis Ababa")
    subcity: Mapped[str | None] = mapped_column(String(80))
    preferred_market_code: Mapped[str] = mapped_column(String(64), nullable=False)
    visit_frequency: Mapped[str] = mapped_column(String(64), nullable=False)
    languages: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)
    consent_honest_reporting: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    status: Mapped[AgentApplicationStatus] = mapped_column(
        SqlEnum(
            AgentApplicationStatus,
            name="agent_application_status",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
        default=AgentApplicationStatus.PENDING,
        server_default=AgentApplicationStatus.PENDING.value,
    )
    review_note: Mapped[str | None] = mapped_column(String(255))
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    contributor_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("contributors.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
