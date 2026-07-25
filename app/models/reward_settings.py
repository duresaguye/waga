"""Admin-configured agent reward conversion (score → ETB)."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgentRewardSettings(Base):
    """Singleton-style row: active conversion from reputation points to birr."""

    __tablename__ = "agent_reward_settings"
    __table_args__ = (
        CheckConstraint("birr_per_point > 0", name="birr_per_point_positive"),
        CheckConstraint("redeem_min_points > 0", name="redeem_min_points_positive"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    birr_per_point: Mapped[float] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=1,
        server_default="1",
    )
    redeem_min_points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=50,
        server_default="50",
    )
    currency_code: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default="ETB",
        server_default="ETB",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class AgentRedeemRequest(Base):
    """Payout queue created when an agent redeems score."""

    __tablename__ = "agent_redeem_requests"
    __table_args__ = (
        CheckConstraint("points_redeemed > 0", name="points_redeemed_positive"),
        CheckConstraint("birr_amount > 0", name="birr_amount_positive"),
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
    telegram_id: Mapped[str | None] = mapped_column(String(64))
    points_redeemed: Mapped[int] = mapped_column(Integer, nullable=False)
    birr_per_point: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    birr_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(8), nullable=False, default="ETB")
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        server_default="pending",
    )  # pending | paid | rejected
    admin_note: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
